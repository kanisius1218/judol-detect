"""
Celery application configuration for async task processing.
Handles auto-deletion queue, scheduling, and background jobs.
"""
from celery import Celery, Task
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from kombu import Exchange, Queue
from typing import Any, Optional
import logging
from datetime import datetime, timedelta
from ..core import settings, logger, audit_logger


class CeleryConfig:
    """Celery configuration."""
    
    # Broker settings
    broker_url = settings.CELERY_BROKER_URL
    result_backend = settings.CELERY_RESULT_BACKEND
    
    # Task settings
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    
    # Task execution settings
    task_always_eager = settings.CELERY_TASK_ALWAYS_EAGER  # For testing
    task_eager_propagates = True
    task_track_started = True
    task_time_limit = 300  # 5 minutes hard limit
    task_soft_time_limit = 240  # 4 minutes soft limit
    task_acks_late = True
    worker_prefetch_multiplier = 1
    
    # Result backend settings
    result_expires = 3600  # Results expire after 1 hour
    result_persistent = True
    
    # Queue configuration
    task_default_queue = 'default'
    task_default_exchange = 'default'
    task_default_exchange_type = 'direct'
    task_default_routing_key = 'default'
    
    task_queues = (
        # Default queue for general tasks
        Queue('default', Exchange('default'), routing_key='default'),
        
        # High priority queue for urgent spam detection
        Queue('high_priority', Exchange('high_priority'), routing_key='high_priority',
              priority=10, max_priority=10),
        
        # Auto-deletion queue with delay and retry
        Queue('auto_deletion', Exchange('auto_deletion'), routing_key='auto_deletion',
              priority=5, max_priority=10),
        
        # Rollback queue for undoing deletions
        Queue('rollback', Exchange('rollback'), routing_key='rollback',
              priority=8, max_priority=10),
        
        # Analytics and reporting
        Queue('analytics', Exchange('analytics'), routing_key='analytics',
              priority=2, max_priority=10),
        
        # Platform-specific queues
        Queue('youtube', Exchange('platform'), routing_key='youtube'),
        Queue('instagram', Exchange('platform'), routing_key='instagram'),
        Queue('tiktok', Exchange('platform'), routing_key='tiktok'),
    )
    
    # Task routing
    task_routes = {
        'workers.tasks.detect_spam': {'queue': 'high_priority'},
        'workers.tasks.auto_delete_spam': {'queue': 'auto_deletion'},
        'workers.tasks.rollback_deletion': {'queue': 'rollback'},
        'workers.tasks.process_analytics': {'queue': 'analytics'},
        'workers.tasks.delete_youtube_comment': {'queue': 'youtube'},
        'workers.tasks.delete_instagram_comment': {'queue': 'instagram'},
        'workers.tasks.delete_tiktok_comment': {'queue': 'tiktok'},
    }
    
    # Retry settings
    task_default_retry_delay = 60  # 60 seconds
    task_max_retries = 3
    
    # Beat schedule (periodic tasks)
    beat_schedule = {
        'cleanup-expired-rollback-tokens': {
            'task': 'workers.tasks.cleanup_expired_rollback_tokens',
            'schedule': timedelta(hours=1),
            'options': {'queue': 'default'}
        },
        'process-deletion-queue': {
            'task': 'workers.tasks.process_deletion_queue',
            'schedule': timedelta(seconds=30),
            'options': {'queue': 'auto_deletion'}
        },
        'generate-analytics-report': {
            'task': 'workers.tasks.generate_analytics_report',
            'schedule': timedelta(hours=6),
            'options': {'queue': 'analytics'}
        },
        'health-check': {
            'task': 'workers.tasks.health_check',
            'schedule': timedelta(minutes=5),
            'options': {'queue': 'default'}
        },
        'model-performance-check': {
            'task': 'workers.tasks.check_model_performance',
            'schedule': timedelta(hours=12),
            'options': {'queue': 'analytics'}
        }
    }
    
    # Worker settings
    worker_pool = 'prefork'  # Use 'solo' for Windows
    worker_concurrency = 4
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    worker_send_task_events = True
    
    # Monitoring
    worker_send_task_events = True
    task_send_sent_event = True


# Create Celery app
app = Celery('spam_detection_system')
app.config_from_object(CeleryConfig)


class LoggingTask(Task):
    """Base task with logging and monitoring."""
    
    def __call__(self, *args, **kwargs):
        """Execute task with logging."""
        task_id = self.request.id
        logger.info(f"Task {self.name} [{task_id}] started")
        
        try:
            result = super().__call__(*args, **kwargs)
            logger.info(f"Task {self.name} [{task_id}] completed successfully")
            return result
        except Exception as exc:
            logger.error(f"Task {self.name} [{task_id}] failed: {str(exc)}")
            raise
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {self.name} [{task_id}] failed with exception: {exc}")
        
        # Log to audit trail for critical tasks
        if 'delete' in self.name.lower():
            audit_logger.log_action(
                action="TASK_FAILURE",
                user_id="system",
                resource_type="celery_task",
                resource_id=task_id,
                details={
                    "task_name": self.name,
                    "exception": str(exc),
                    "args": str(args)[:500],  # Truncate for safety
                },
                status="failure"
            )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Task {self.name} [{task_id}] retrying due to: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        if 'delete' in self.name.lower():
            audit_logger.log_action(
                action="TASK_SUCCESS",
                user_id="system",
                resource_type="celery_task",
                resource_id=task_id,
                details={
                    "task_name": self.name,
                    "result": str(retval)[:500],  # Truncate for safety
                },
                status="success"
            )


# Set base task
app.Task = LoggingTask


# Signal handlers for monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log task start."""
    logger.debug(f"Task {task.name} [{task_id}] starting execution")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw):
    """Log task completion."""
    logger.debug(f"Task {task.name} [{task_id}] completed with state: {state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Handle task failure for monitoring."""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")
    
    # Send alert for critical failures
    if 'critical' in kwargs.get('tags', []):
        # In production, send to monitoring service
        pass


@task_success.connect
def task_success_handler(sender=None, result=None, **kw):
    """Handle task success for monitoring."""
    pass  # Metrics collection can be added here


# Auto-discover tasks
app.autodiscover_tasks(['src.workers'])
