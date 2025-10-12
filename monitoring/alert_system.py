"""
Real-time Monitoring and Alerting System for Spam Detection
"""

import os
import json
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import schedule

import numpy as np
from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Alert data structure."""
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class MetricsCollector:
    """
    Collects and analyzes system metrics.
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics = {
            'response_times': deque(maxlen=window_size),
            'error_rates': deque(maxlen=window_size),
            'prediction_counts': defaultdict(int),
            'cache_hit_rate': deque(maxlen=window_size),
            'model_accuracy': deque(maxlen=window_size),
            'system_health': deque(maxlen=window_size)
        }
        self.thresholds = {
            'response_time_ms': 500,
            'error_rate': 0.05,
            'cache_hit_rate': 0.3,
            'model_accuracy': 0.85,
            'cpu_usage': 80,
            'memory_usage': 85
        }
        
    def add_metric(self, metric_type: str, value: float):
        """Add a metric value."""
        if metric_type in self.metrics:
            if isinstance(self.metrics[metric_type], deque):
                self.metrics[metric_type].append(value)
            elif isinstance(self.metrics[metric_type], defaultdict):
                self.metrics[metric_type][value] += 1
    
    def get_statistics(self, metric_type: str) -> Dict[str, float]:
        """Calculate statistics for a metric."""
        if metric_type not in self.metrics:
            return {}
        
        values = self.metrics[metric_type]
        if isinstance(values, deque) and len(values) > 0:
            return {
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99)
            }
        return {}
    
    def check_thresholds(self) -> List[Alert]:
        """Check if any metrics exceed thresholds."""
        alerts = []
        
        # Check response time
        if len(self.metrics['response_times']) > 0:
            avg_response_time = np.mean(self.metrics['response_times'])
            if avg_response_time > self.thresholds['response_time_ms']:
                alerts.append(Alert(
                    alert_type='performance',
                    severity='high' if avg_response_time > 1000 else 'medium',
                    message=f'High response time: {avg_response_time:.2f}ms',
                    metadata={'avg_response_time': avg_response_time}
                ))
        
        # Check error rate
        if len(self.metrics['error_rates']) > 0:
            error_rate = np.mean(self.metrics['error_rates'])
            if error_rate > self.thresholds['error_rate']:
                alerts.append(Alert(
                    alert_type='error',
                    severity='critical' if error_rate > 0.1 else 'high',
                    message=f'High error rate: {error_rate:.2%}',
                    metadata={'error_rate': error_rate}
                ))
        
        # Check cache hit rate
        if len(self.metrics['cache_hit_rate']) > 0:
            cache_hit_rate = np.mean(self.metrics['cache_hit_rate'])
            if cache_hit_rate < self.thresholds['cache_hit_rate']:
                alerts.append(Alert(
                    alert_type='performance',
                    severity='low',
                    message=f'Low cache hit rate: {cache_hit_rate:.2%}',
                    metadata={'cache_hit_rate': cache_hit_rate}
                ))
        
        # Check model accuracy
        if len(self.metrics['model_accuracy']) > 0:
            accuracy = np.mean(self.metrics['model_accuracy'])
            if accuracy < self.thresholds['model_accuracy']:
                alerts.append(Alert(
                    alert_type='model',
                    severity='high',
                    message=f'Model accuracy below threshold: {accuracy:.2%}',
                    metadata={'accuracy': accuracy}
                ))
        
        return alerts


class AlertManager:
    """
    Manages alerts and notifications.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_alerts = []
        self.alert_history = deque(maxlen=1000)
        self.notification_channels = []
        
        # Initialize notification channels
        if config.get('email_enabled'):
            self.notification_channels.append(EmailNotifier(config['email']))
        if config.get('slack_enabled'):
            self.notification_channels.append(SlackNotifier(config['slack']))
        if config.get('webhook_enabled'):
            self.notification_channels.append(WebhookNotifier(config['webhook']))
    
    def process_alert(self, alert: Alert):
        """Process a new alert."""
        # Check if similar alert already exists
        for active_alert in self.active_alerts:
            if (active_alert.alert_type == alert.alert_type and 
                active_alert.severity == alert.severity and
                not active_alert.resolved):
                # Update existing alert
                active_alert.timestamp = alert.timestamp
                return
        
        # Add new alert
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Send notifications based on severity
        if alert.severity in ['high', 'critical']:
            self._send_notifications(alert)
    
    def _send_notifications(self, alert: Alert):
        """Send notifications through configured channels."""
        for channel in self.notification_channels:
            try:
                channel.send(alert)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.__class__.__name__}: {e}")
    
    def resolve_alerts(self, alert_type: Optional[str] = None):
        """Resolve alerts of a specific type or all alerts."""
        for alert in self.active_alerts:
            if not alert.resolved and (alert_type is None or alert.alert_type == alert_type):
                alert.resolved = True
                alert.resolution_time = datetime.now()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        return [a for a in self.active_alerts if not a.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts."""
        active = self.get_active_alerts()
        return {
            'active_count': len(active),
            'critical': sum(1 for a in active if a.severity == 'critical'),
            'high': sum(1 for a in active if a.severity == 'high'),
            'medium': sum(1 for a in active if a.severity == 'medium'),
            'low': sum(1 for a in active if a.severity == 'low'),
            'recent_alerts': [
                {
                    'type': a.alert_type,
                    'severity': a.severity,
                    'message': a.message,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in list(self.alert_history)[-10:]
            ]
        }


class EmailNotifier:
    """Email notification channel."""
    
    def __init__(self, config: Dict[str, str]):
        self.smtp_server = config['smtp_server']
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config['username']
        self.password = config['password']
        self.from_email = config['from_email']
        self.to_emails = config['to_emails']
    
    def send(self, alert: Alert):
        """Send email notification."""
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        msg['Subject'] = f"[{alert.severity.upper()}] Spam Detection Alert: {alert.alert_type}"
        
        body = f"""
        Alert Type: {alert.alert_type}
        Severity: {alert.severity}
        Time: {alert.timestamp}
        
        Message: {alert.message}
        
        Metadata:
        {json.dumps(alert.metadata, indent=2)}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)


class SlackNotifier:
    """Slack notification channel."""
    
    def __init__(self, config: Dict[str, str]):
        self.webhook_url = config['webhook_url']
        self.channel = config.get('channel', '#alerts')
    
    def send(self, alert: Alert):
        """Send Slack notification."""
        emoji = {
            'critical': ':rotating_light:',
            'high': ':warning:',
            'medium': ':information_source:',
            'low': ':speech_balloon:'
        }.get(alert.severity, ':bell:')
        
        payload = {
            'channel': self.channel,
            'username': 'Spam Detection Monitor',
            'icon_emoji': emoji,
            'attachments': [{
                'color': {
                    'critical': 'danger',
                    'high': 'warning',
                    'medium': 'warning',
                    'low': 'good'
                }.get(alert.severity, 'good'),
                'title': f"{alert.alert_type.upper()} Alert",
                'text': alert.message,
                'fields': [
                    {'title': 'Severity', 'value': alert.severity, 'short': True},
                    {'title': 'Time', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
                ],
                'footer': 'Spam Detection System'
            }]
        }
        
        requests.post(self.webhook_url, json=payload)


class WebhookNotifier:
    """Generic webhook notification channel."""
    
    def __init__(self, config: Dict[str, str]):
        self.url = config['url']
        self.headers = config.get('headers', {})
    
    def send(self, alert: Alert):
        """Send webhook notification."""
        payload = {
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'metadata': alert.metadata
        }
        
        requests.post(self.url, json=payload, headers=self.headers)


class MonitoringService:
    """
    Main monitoring service that orchestrates metrics collection and alerting.
    """
    
    def __init__(self, config_file: str = 'monitoring_config.json'):
        self.config = self._load_config(config_file)
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.config.get('notifications', {}))
        self.running = False
        self.monitor_thread = None
        
        # Prometheus registry
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load monitoring configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                'api_endpoint': 'http://localhost:5000',
                'check_interval': 60,
                'notifications': {
                    'email_enabled': False,
                    'slack_enabled': False,
                    'webhook_enabled': False
                }
            }
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics."""
        self.prom_metrics = {
            'response_time': Gauge('spam_detector_response_time_ms', 'Response time in milliseconds', registry=self.registry),
            'error_rate': Gauge('spam_detector_error_rate', 'Error rate', registry=self.registry),
            'cache_hit_rate': Gauge('spam_detector_cache_hit_rate', 'Cache hit rate', registry=self.registry),
            'active_alerts': Gauge('spam_detector_active_alerts', 'Number of active alerts', registry=self.registry)
        }
    
    def collect_api_metrics(self):
        """Collect metrics from the API."""
        try:
            # Get health status
            health_response = requests.get(f"{self.config['api_endpoint']}/api/health")
            if health_response.status_code == 200:
                self.metrics_collector.add_metric('system_health', 1)
            else:
                self.metrics_collector.add_metric('system_health', 0)
            
            # Get analytics
            analytics_response = requests.get(f"{self.config['api_endpoint']}/api/analytics")
            if analytics_response.status_code == 200:
                data = analytics_response.json()
                
                # Extract metrics
                if 'request_analytics' in data:
                    analytics = data['request_analytics']
                    self.metrics_collector.add_metric('response_times', analytics.get('avg_latency_ms', 0))
                    
                    # Calculate error rate (simplified)
                    total_requests = analytics.get('total_requests', 1)
                    # This would need actual error count from API
                    error_rate = 0.01  # Placeholder
                    self.metrics_collector.add_metric('error_rates', error_rate)
            
        except Exception as e:
            logger.error(f"Failed to collect API metrics: {e}")
            self.metrics_collector.add_metric('system_health', 0)
    
    def run_checks(self):
        """Run monitoring checks."""
        # Collect metrics
        self.collect_api_metrics()
        
        # Check thresholds
        alerts = self.metrics_collector.check_thresholds()
        
        # Process alerts
        for alert in alerts:
            self.alert_manager.process_alert(alert)
        
        # Update Prometheus metrics
        self._update_prometheus_metrics()
        
        # Push to Prometheus gateway if configured
        if self.config.get('prometheus_gateway'):
            try:
                push_to_gateway(
                    self.config['prometheus_gateway'],
                    job='spam_detector_monitor',
                    registry=self.registry
                )
            except Exception as e:
                logger.error(f"Failed to push to Prometheus: {e}")
    
    def _update_prometheus_metrics(self):
        """Update Prometheus metrics."""
        stats = self.metrics_collector.get_statistics('response_times')
        if stats:
            self.prom_metrics['response_time'].set(stats['mean'])
        
        error_stats = self.metrics_collector.get_statistics('error_rates')
        if error_stats:
            self.prom_metrics['error_rate'].set(error_stats['mean'])
        
        cache_stats = self.metrics_collector.get_statistics('cache_hit_rate')
        if cache_stats:
            self.prom_metrics['cache_hit_rate'].set(cache_stats['mean'])
        
        active_alerts = len(self.alert_manager.get_active_alerts())
        self.prom_metrics['active_alerts'].set(active_alerts)
    
    def start(self):
        """Start monitoring service."""
        self.running = True
        
        # Schedule periodic checks
        schedule.every(self.config.get('check_interval', 60)).seconds.do(self.run_checks)
        
        def monitor_loop():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor_loop)
        self.monitor_thread.start()
        
        logger.info("Monitoring service started")
    
    def stop(self):
        """Stop monitoring service."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Monitoring service stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring status."""
        return {
            'running': self.running,
            'alerts': self.alert_manager.get_alert_summary(),
            'metrics': {
                'response_time': self.metrics_collector.get_statistics('response_times'),
                'error_rate': self.metrics_collector.get_statistics('error_rates'),
                'cache_hit_rate': self.metrics_collector.get_statistics('cache_hit_rate')
            }
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create monitoring service
    monitor = MonitoringService()
    
    # Start monitoring
    monitor.start()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            status = monitor.get_status()
            print(f"Monitoring Status: {json.dumps(status, indent=2)}")
    except KeyboardInterrupt:
        monitor.stop()
        print("Monitoring stopped")
