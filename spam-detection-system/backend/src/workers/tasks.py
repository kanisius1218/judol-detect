"""
Celery tasks for spam detection, auto-deletion, and rollback operations.
Implements safe deletion with grace period and rollback mechanism.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from celery import group, chain, chord
from celery.exceptions import SoftTimeLimitExceeded
import json
import uuid
from dataclasses import asdict
from .celery_app import app
from ..core import logger, audit_logger, settings
from ..models.ml.spam_detector import SpamDetector, PredictionResult
from ..adapters import youtube, instagram, tiktok
from ..services.notification_service import NotificationService
from ..repository.spam_repository import SpamRepository
from ..core.exceptions import (
    DeletionNotAllowedError,
    RollbackWindowExpiredError,
    PlatformAPIError
)


# Initialize services
spam_detector = SpamDetector()
notification_service = NotificationService()
spam_repository = SpamRepository()


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def detect_spam(self, text: str, platform: str, content_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Detect spam in text content.
    
    Args:
        text: Content to analyze
        platform: Platform name (youtube, instagram, tiktok)
        content_id: Unique content identifier on the platform
        metadata: Additional context (author, timestamp, etc.)
    
    Returns:
        Detection result with spam score and decision
    """
    try:
        # Run spam detection
        result = spam_detector.predict(text)
        
        # Store detection result
        detection_record = spam_repository.create_detection(
            platform=platform,
            content_id=content_id,
            content=text,
            is_spam=result.is_spam,
            confidence=result.confidence,
            spam_score=result.spam_score,
            features=result.features,
            metadata=metadata
        )
        
        # If spam with high confidence, schedule for deletion
        if result.is_spam and result.confidence >= settings.AUTO_DELETE_CONFIDENCE_THRESHOLD:
            if settings.AUTO_DELETE_ENABLED:
                # Schedule auto-deletion with delay
                auto_delete_spam.apply_async(
                    args=[platform, content_id, detection_record.id, result.spam_score],
                    countdown=settings.AUTO_DELETE_DELAY_SECONDS,
                    queue='auto_deletion'
                )
                
                logger.info(f"Scheduled auto-deletion for {platform}:{content_id} in {settings.AUTO_DELETE_DELAY_SECONDS}s")
            
            # Send notification for manual review if confidence is borderline
            if result.confidence < 0.99:
                notification_service.send_review_alert(
                    platform=platform,
                    content_id=content_id,
                    spam_score=result.spam_score,
                    content_preview=text[:200]
                )
        
        return {
            'task_id': self.request.id,
            'is_spam': result.is_spam,
            'confidence': result.confidence,
            'spam_score': result.spam_score,
            'risk_level': result.risk_level,
            'explanation': result.explanation,
            'detection_id': detection_record.id,
            'auto_delete_scheduled': result.is_spam and result.confidence >= settings.AUTO_DELETE_CONFIDENCE_THRESHOLD
        }
        
    except Exception as exc:
        logger.error(f"Spam detection failed for {platform}:{content_id}: {str(exc)}")
        self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=120)
def auto_delete_spam(
    self,
    platform: str,
    content_id: str,
    detection_id: str,
    spam_score: float,
    force: bool = False
) -> Dict[str, Any]:
    """
    Auto-delete spam content with safety checks.
    
    Args:
        platform: Platform name
        content_id: Content identifier
        detection_id: Detection record ID
        spam_score: Spam confidence score
        force: Skip safety checks (admin only)
    
    Returns:
        Deletion result with rollback token
    """
    try:
        # Verify deletion is still valid
        detection = spam_repository.get_detection(detection_id)
        
        if not detection:
            logger.error(f"Detection record {detection_id} not found")
            return {'error': 'Detection record not found'}
        
        # Check if already deleted
        if detection.deleted_at:
            logger.info(f"Content {platform}:{content_id} already deleted")
            return {'status': 'already_deleted', 'deleted_at': detection.deleted_at.isoformat()}
        
        # Safety checks (unless forced)
        if not force:
            # Re-check spam score if confidence dropped
            if spam_score < settings.AUTO_DELETE_CONFIDENCE_THRESHOLD:
                logger.warning(f"Spam score too low for auto-deletion: {spam_score}")
                return {'status': 'cancelled', 'reason': 'confidence_too_low'}
            
            # Check for manual override
            if detection.manual_override == 'keep':
                logger.info(f"Manual override prevents deletion of {platform}:{content_id}")
                return {'status': 'cancelled', 'reason': 'manual_override'}
        
        # Generate rollback token
        rollback_token = str(uuid.uuid4())
        
        # Store original content for rollback
        backup_data = {
            'platform': platform,
            'content_id': content_id,
            'content': detection.content,
            'metadata': detection.metadata,
            'deleted_at': datetime.utcnow().isoformat(),
            'rollback_token': rollback_token
        }
        
        spam_repository.create_deletion_backup(
            rollback_token=rollback_token,
            data=backup_data,
            expires_at=datetime.utcnow() + timedelta(hours=settings.ROLLBACK_WINDOW_HOURS)
        )
        
        # Perform platform-specific deletion
        deletion_result = delete_from_platform(platform, content_id)
        
        if deletion_result['success']:
            # Update detection record
            spam_repository.mark_as_deleted(
                detection_id=detection_id,
                deleted_at=datetime.utcnow(),
                deletion_method='auto',
                rollback_token=rollback_token
            )
            
            # Log deletion
            audit_logger.log_deletion(
                platform=platform,
                content_id=content_id,
                user_id='system',
                reason='auto_deletion',
                confidence_score=spam_score,
                rollback_token=rollback_token
            )
            
            # Send notification
            notification_service.send_deletion_notification(
                platform=platform,
                content_id=content_id,
                rollback_token=rollback_token,
                rollback_window_hours=settings.ROLLBACK_WINDOW_HOURS
            )
            
            logger.info(f"Successfully deleted spam from {platform}:{content_id}")
            
            return {
                'status': 'deleted',
                'platform': platform,
                'content_id': content_id,
                'rollback_token': rollback_token,
                'rollback_expires_at': (datetime.utcnow() + timedelta(hours=settings.ROLLBACK_WINDOW_HOURS)).isoformat()
            }
        else:
            # Deletion failed
            logger.error(f"Failed to delete from {platform}: {deletion_result.get('error')}")
            
            # Clean up backup
            spam_repository.delete_backup(rollback_token)
            
            # Retry or fail
            if self.request.retries < self.max_retries:
                self.retry(exc=Exception(deletion_result.get('error')))
            
            return {
                'status': 'failed',
                'error': deletion_result.get('error', 'Platform deletion failed')
            }
            
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for deletion of {platform}:{content_id}")
        return {'status': 'timeout', 'error': 'Task execution timeout'}
    
    except Exception as exc:
        logger.error(f"Auto-deletion failed for {platform}:{content_id}: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            self.retry(exc=exc)
        
        return {'status': 'error', 'error': str(exc)}


def delete_from_platform(platform: str, content_id: str) -> Dict[str, Any]:
    """
    Execute platform-specific deletion.
    
    Args:
        platform: Platform name
        content_id: Content identifier
    
    Returns:
        Deletion result
    """
    try:
        if platform.lower() == 'youtube':
            return youtube.delete_comment(content_id)
        elif platform.lower() == 'instagram':
            return instagram.delete_comment(content_id)
        elif platform.lower() == 'tiktok':
            return tiktok.delete_comment(content_id)
        else:
            return {'success': False, 'error': f'Unsupported platform: {platform}'}
    
    except Exception as e:
        logger.error(f"Platform deletion error: {str(e)}")
        return {'success': False, 'error': str(e)}


@app.task(bind=True, max_retries=2)
def rollback_deletion(self, rollback_token: str, reason: str = "manual_rollback") -> Dict[str, Any]:
    """
    Rollback a deletion using the rollback token.
    
    Args:
        rollback_token: Unique token for rollback
        reason: Reason for rollback
    
    Returns:
        Rollback result
    """
    try:
        # Get backup data
        backup = spam_repository.get_deletion_backup(rollback_token)
        
        if not backup:
            raise RollbackWindowExpiredError(
                message="Rollback token not found or expired",
                expired_hours=settings.ROLLBACK_WINDOW_HOURS
            )
        
        # Check if not expired
        if backup.expires_at < datetime.utcnow():
            raise RollbackWindowExpiredError(
                message="Rollback window has expired",
                expired_hours=settings.ROLLBACK_WINDOW_HOURS
            )
        
        # Restore content on platform
        platform = backup.data['platform']
        content_id = backup.data['content_id']
        content = backup.data['content']
        metadata = backup.data.get('metadata', {})
        
        restore_result = restore_on_platform(platform, content_id, content, metadata)
        
        if restore_result['success']:
            # Update records
            detection = spam_repository.find_by_content_id(platform, content_id)
            if detection:
                spam_repository.mark_as_restored(
                    detection_id=detection.id,
                    restored_at=datetime.utcnow(),
                    reason=reason
                )
            
            # Log rollback
            audit_logger.log_rollback(
                platform=platform,
                content_id=content_id,
                user_id='system',
                rollback_token=rollback_token
            )
            
            # Clean up backup
            spam_repository.delete_backup(rollback_token)
            
            # Send notification
            notification_service.send_rollback_notification(
                platform=platform,
                content_id=content_id,
                reason=reason
            )
            
            logger.info(f"Successfully rolled back deletion for {platform}:{content_id}")
            
            return {
                'status': 'restored',
                'platform': platform,
                'content_id': content_id,
                'reason': reason
            }
        else:
            logger.error(f"Failed to restore on {platform}: {restore_result.get('error')}")
            
            return {
                'status': 'failed',
                'error': restore_result.get('error', 'Platform restoration failed')
            }
            
    except Exception as exc:
        logger.error(f"Rollback failed for token {rollback_token}: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            self.retry(exc=exc)
        
        return {'status': 'error', 'error': str(exc)}


def restore_on_platform(platform: str, content_id: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restore content on platform.
    
    Args:
        platform: Platform name
        content_id: Content identifier
        content: Original content
        metadata: Content metadata
    
    Returns:
        Restoration result
    """
    try:
        if platform.lower() == 'youtube':
            return youtube.restore_comment(content_id, content, metadata)
        elif platform.lower() == 'instagram':
            return instagram.restore_comment(content_id, content, metadata)
        elif platform.lower() == 'tiktok':
            return tiktok.restore_comment(content_id, content, metadata)
        else:
            return {'success': False, 'error': f'Unsupported platform: {platform}'}
    
    except Exception as e:
        logger.error(f"Platform restoration error: {str(e)}")
        return {'success': False, 'error': str(e)}


@app.task
def process_deletion_queue() -> Dict[str, Any]:
    """
    Process pending deletions in queue.
    Runs periodically to handle queued spam deletions.
    """
    try:
        # Get pending deletions
        pending = spam_repository.get_pending_deletions(
            limit=settings.AUTO_DELETE_BATCH_SIZE
        )
        
        if not pending:
            logger.debug("No pending deletions in queue")
            return {'processed': 0, 'status': 'no_pending'}
        
        # Process in parallel
        deletion_tasks = []
        for item in pending:
            task = auto_delete_spam.s(
                platform=item.platform,
                content_id=item.content_id,
                detection_id=item.id,
                spam_score=item.spam_score
            )
            deletion_tasks.append(task)
        
        # Execute as group
        job = group(deletion_tasks)
        result = job.apply_async(queue='auto_deletion')
        
        logger.info(f"Processing {len(pending)} pending deletions")
        
        return {
            'processed': len(pending),
            'status': 'processing',
            'job_id': result.id
        }
        
    except Exception as exc:
        logger.error(f"Error processing deletion queue: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}


@app.task
def cleanup_expired_rollback_tokens() -> Dict[str, Any]:
    """
    Clean up expired rollback tokens and backups.
    Runs periodically to maintain database hygiene.
    """
    try:
        expired_count = spam_repository.cleanup_expired_backups()
        
        logger.info(f"Cleaned up {expired_count} expired rollback tokens")
        
        return {
            'cleaned': expired_count,
            'status': 'success'
        }
        
    except Exception as exc:
        logger.error(f"Error cleaning up rollback tokens: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}


@app.task
def batch_detect_spam(texts: List[str], platform: str, metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Detect spam in batch for multiple texts.
    
    Args:
        texts: List of texts to analyze
        platform: Platform name
        metadata: List of metadata for each text
    
    Returns:
        Batch detection results
    """
    try:
        # Ensure metadata list matches texts
        if metadata and len(metadata) != len(texts):
            metadata = None
        
        # Process in parallel
        detection_tasks = []
        for i, text in enumerate(texts):
            meta = metadata[i] if metadata else {}
            content_id = meta.get('content_id', f'batch_{uuid.uuid4().hex[:8]}')
            
            task = detect_spam.s(
                text=text,
                platform=platform,
                content_id=content_id,
                metadata=meta
            )
            detection_tasks.append(task)
        
        # Execute as group
        job = group(detection_tasks)
        results = job.apply_async(queue='high_priority').get(timeout=300)
        
        # Aggregate results
        spam_count = sum(1 for r in results if r['is_spam'])
        ham_count = len(results) - spam_count
        avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
        
        return {
            'total_processed': len(texts),
            'spam_count': spam_count,
            'ham_count': ham_count,
            'average_confidence': avg_confidence,
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Batch spam detection failed: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}


@app.task
def generate_analytics_report() -> Dict[str, Any]:
    """
    Generate analytics report for spam detection performance.
    """
    try:
        # Get statistics from repository
        stats = spam_repository.get_statistics(
            start_date=datetime.utcnow() - timedelta(hours=24),
            end_date=datetime.utcnow()
        )
        
        report = {
            'period': '24_hours',
            'total_detections': stats['total_detections'],
            'spam_detected': stats['spam_count'],
            'ham_detected': stats['ham_count'],
            'auto_deletions': stats['auto_deletions'],
            'manual_deletions': stats['manual_deletions'],
            'rollbacks': stats['rollbacks'],
            'average_confidence': stats['avg_confidence'],
            'platforms': stats['by_platform'],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Send report
        notification_service.send_analytics_report(report)
        
        logger.info("Analytics report generated successfully")
        
        return report
        
    except Exception as exc:
        logger.error(f"Error generating analytics report: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}


@app.task
def check_model_performance() -> Dict[str, Any]:
    """
    Check ML model performance and alert if degraded.
    """
    try:
        # Get recent predictions
        recent = spam_repository.get_recent_predictions(hours=12)
        
        if len(recent) < 100:
            logger.info("Insufficient data for performance check")
            return {'status': 'insufficient_data'}
        
        # Calculate metrics
        false_positives = sum(1 for p in recent if p.manual_override == 'not_spam' and p.is_spam)
        false_negatives = sum(1 for p in recent if p.manual_override == 'spam' and not p.is_spam)
        total_overrides = false_positives + false_negatives
        
        error_rate = total_overrides / len(recent) if recent else 0
        
        # Alert if error rate is high
        if error_rate > 0.1:  # 10% error rate threshold
            notification_service.send_model_alert(
                error_rate=error_rate,
                false_positives=false_positives,
                false_negatives=false_negatives,
                sample_size=len(recent)
            )
            
            logger.warning(f"Model performance degraded: {error_rate:.2%} error rate")
        
        return {
            'status': 'checked',
            'error_rate': error_rate,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'sample_size': len(recent)
        }
        
    except Exception as exc:
        logger.error(f"Error checking model performance: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}


@app.task
def health_check() -> Dict[str, Any]:
    """
    Perform system health check.
    """
    try:
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check database
        try:
            spam_repository.ping()
            health['components']['database'] = 'healthy'
        except:
            health['components']['database'] = 'unhealthy'
            health['status'] = 'degraded'
        
        # Check model
        try:
            test_result = spam_detector.predict("Test message")
            health['components']['ml_model'] = 'healthy'
        except:
            health['components']['ml_model'] = 'unhealthy'
            health['status'] = 'degraded'
        
        # Check queue size
        queue_size = spam_repository.get_queue_size()
        health['components']['queue'] = {
            'status': 'healthy' if queue_size < 1000 else 'warning',
            'size': queue_size
        }
        
        if health['status'] == 'degraded':
            notification_service.send_health_alert(health)
        
        return health
        
    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}
