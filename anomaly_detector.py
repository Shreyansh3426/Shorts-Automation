"""
Anomaly Detection & Alerting Module
Analyzes pipeline performance patterns to detect degradation and issues.
Automatically flags unusual behavior for investigation.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import dict, list

class AnomalyDetector:
    """Detects performance anomalies and unusual patterns."""
    
    def __init__(self, job_folder: str):
        self.job_folder = job_folder
        self.history_file = os.path.join(job_folder, 'run_history.json')
        self.history = self._load_history()
    
    def _load_history(self) -> list:
        """Load previous run history."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """Save run history."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-100:], f)  # Keep last 100 runs
    
    def add_run(self, run_data: dict):
        """Add a new run to history."""
        self.history.append(run_data)
        self._save_history()
    
    def detect_anomalies(self, current_run: dict) -> list:
        """Detect anomalies in current run compared to history."""
        if len(self.history) < 3:
            return []  # Need baseline data
        
        anomalies = []
        
        # 1. Check for performance degradation
        recent_duration = [r.get('total_duration_sec', 0) for r in self.history[-10:]]
        if recent_duration:
            avg_duration = sum(recent_duration) / len(recent_duration)
            current_duration = current_run.get('total_duration_sec', 0)
            
            if current_duration > avg_duration * 1.5:
                anomalies.append({
                    "type": "performance_degradation",
                    "severity": "warning",
                    "message": f"Pipeline took {current_duration:.0f}s (avg {avg_duration:.0f}s) - 50% slower than normal",
                    "expected": avg_duration,
                    "actual": current_duration
                })
        
        # 2. Check error rate trend
        recent_errors = [len(r.get('errors', [])) for r in self.history[-10:]]
        if recent_errors and sum(recent_errors) > 0:
            error_rate = sum(recent_errors) / len(recent_errors)
            current_errors = len(current_run.get('errors', []))
            
            if current_errors > error_rate * 2:
                anomalies.append({
                    "type": "elevated_error_rate",
                    "severity": "critical",
                    "message": f"Current errors ({current_errors}) exceed baseline ({error_rate:.1f})",
                    "expected": error_rate,
                    "actual": current_errors
                })
        
        # 3. Check for stage timeout patterns
        for stage_name, stage_data in current_run.get('stages', {}).items():
            stage_duration = stage_data.get('duration_sec', 0)
            
            # Compare against historical stage performance
            historical_durations = []
            for run in self.history[-10:]:
                if stage_name in run.get('stages', {}):
                    historical_durations.append(run['stages'][stage_name].get('duration_sec', 0))
            
            if historical_durations:
                avg_stage_time = sum(historical_durations) / len(historical_durations)
                if stage_duration > avg_stage_time * 2.5:
                    anomalies.append({
                        "type": "stage_timeout",
                        "severity": "warning",
                        "stage": stage_name,
                        "message": f"Stage '{stage_name}' took {stage_duration:.0f}s (historical avg {avg_stage_time:.0f}s)",
                        "expected": avg_stage_time,
                        "actual": stage_duration
                    })
        
        # 4. Check for resource constraint patterns
        sys_data = current_run.get('system', {})
        if sys_data.get('disk_usage_percent', 0) > 85:
            anomalies.append({
                "type": "low_disk_space",
                "severity": "critical",
                "message": f"Disk usage critically high: {sys_data['disk_usage_percent']}%",
                "threshold": 85,
                "actual": sys_data['disk_usage_percent']
            })
        
        if sys_data.get('memory_percent', 0) > 80:
            anomalies.append({
                "type": "high_memory_usage",
                "severity": "warning",
                "message": f"Memory usage: {sys_data['memory_percent']}%",
                "threshold": 80,
                "actual": sys_data['memory_percent']
            })
        
        # 5. Check for API quota patterns
        api_calls = current_run.get('api_calls', {})
        for api_name, calls in api_calls.items():
            quota_errors = [c for c in calls if c.get('status') == 403]
            if quota_errors:
                anomalies.append({
                    "type": "api_quota_exhaustion",
                    "severity": "critical",
                    "api": api_name,
                    "message": f"API '{api_name}' returned {len(quota_errors)} quota errors",
                    "error_count": len(quota_errors)
                })
        
        return anomalies


def format_anomaly_report(anomalies: list) -> str:
    """Format anomaly report for display."""
    if not anomalies:
        return "✅ No anomalies detected\n"
    
    report = f"\n⚠️  ANOMALIES DETECTED ({len(anomalies)}):\n"
    report += "=" * 70 + "\n"
    
    # Group by severity
    by_severity = {}
    for anomaly in anomalies:
        severity = anomaly.get('severity', 'info')
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(anomaly)
    
    for severity in ['critical', 'warning', 'info']:
        if severity in by_severity:
            icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}[severity]
            report += f"\n{icon} {severity.upper()}:\n"
            for anomaly in by_severity[severity]:
                report += f"  • {anomaly['message']}\n"
    
    report += "=" * 70 + "\n"
    return report


def get_recommendations(anomalies: list) -> list:
    """Get actionable recommendations based on detected anomalies."""
    recommendations = []
    
    for anomaly in anomalies:
        atype = anomaly.get('type')
        
        if atype == 'performance_degradation':
            recommendations.append("Check for background processes or system load increases")
        
        elif atype == 'elevated_error_rate':
            recommendations.append("Review recent API changes or network stability")
        
        elif atype == 'stage_timeout':
            recommendations.append(f"Optimize stage '{anomaly.get('stage')}' or increase timeout threshold")
        
        elif atype == 'low_disk_space':
            recommendations.append("Clean up old media files and archived jobs")
        
        elif atype == 'high_memory_usage':
            recommendations.append("Reduce batch size or process fewer videos per run")
        
        elif atype == 'api_quota_exhaustion':
            recommendations.append(f"Reduce API calls to '{anomaly.get('api')}' or schedule runs differently")
    
    return list(set(recommendations))  # Deduplicate
