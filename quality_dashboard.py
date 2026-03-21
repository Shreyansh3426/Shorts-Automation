"""
Quality Dashboard Module
Aggregates all metrics and provides comprehensive quality insights.
Tracks pipeline health, performance, and content quality over time.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import dict, list

class QualityDashboard:
    """Comprehensive quality metrics aggregator."""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.media_dir = os.path.join(workspace_root, 'media')
        self.metrics_file = os.path.join(workspace_root, 'quality_metrics.json')
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> dict:
        """Load or create metrics file."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                return self._init_metrics()
        return self._init_metrics()
    
    def _init_metrics(self) -> dict:
        """Initialize metrics structure."""
        return {
            "pipeline_health": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "success_rate": 0.0,
                "avg_duration_sec": 0
            },
            "content_metrics": {
                "total_videos": 0,
                "total_variants": 0,
                "avg_views": 0,
                "avg_engagement_rate": 0.0,
                "total_views": 0
            },
            "performance": {
                "stage_durations": {},
                "api_calls": {},
                "error_rate": 0.0
            },
            "system_health": {
                "disk_usage_trend": [],
                "memory_usage_trend": [],
                "error_frequency": {}
            },
            "updated_at": datetime.now().isoformat()
        }
    
    def _save_metrics(self):
        """Save metrics to file."""
        self.metrics["updated_at"] = datetime.now().isoformat()
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def update_from_diagnostics(self, diagnostics: dict):
        """Update metrics from diagnostics report."""
        # Update pipeline health
        self.metrics["pipeline_health"]["total_runs"] += 1
        
        if diagnostics.get("status") == "success":
            self.metrics["pipeline_health"]["successful_runs"] += 1
        else:
            self.metrics["pipeline_health"]["failed_runs"] += 1
        
        total = self.metrics["pipeline_health"]["total_runs"]
        successes = self.metrics["pipeline_health"]["successful_runs"]
        self.metrics["pipeline_health"]["success_rate"] = (successes / total * 100) if total > 0 else 0
        
        # Update performance metrics
        duration = diagnostics.get("total_duration_sec", 0)
        avg_duration = self.metrics["pipeline_health"]["avg_duration_sec"]
        self.metrics["pipeline_health"]["avg_duration_sec"] = (
            (avg_duration * (total - 1) + duration) / total
        ) if total > 0 else duration
        
        # Track stage performance
        for stage_name, stage_data in diagnostics.get("stages", {}).items():
            if stage_name not in self.metrics["performance"]["stage_durations"]:
                self.metrics["performance"]["stage_durations"][stage_name] = []
            self.metrics["performance"]["stage_durations"][stage_name].append(
                stage_data.get("duration_sec", 0)
            )
        
        # Track system health
        if "system" in diagnostics:
            sys_data = diagnostics["system"]
            self.metrics["system_health"]["disk_usage_trend"].append({
                "timestamp": datetime.now().isoformat(),
                "usage_percent": sys_data.get("disk_usage_percent", 0)
            })
            self.metrics["system_health"]["memory_usage_trend"].append({
                "timestamp": datetime.now().isoformat(),
                "usage_percent": sys_data.get("memory_percent", 0)
            })
        
        # Track errors
        error_count = len(diagnostics.get("errors", []))
        if error_count > 0:
            self.metrics["performance"]["error_rate"] = (
                (self.metrics["performance"]["error_rate"] * (total - 1) + error_count) / total
            )
        
        self._save_metrics()
    
    def update_from_analytics(self, video_stats: list):
        """Update metrics from YouTube analytics."""
        self.metrics["content_metrics"]["total_videos"] = len(video_stats)
        
        total_views = sum(v.get("total_views", 0) for v in video_stats)
        self.metrics["content_metrics"]["total_views"] = total_views
        
        total_engagement = 0
        total_interactions = 0
        
        for video in video_stats:
            total_interactions += video.get("likes", 0) + video.get("comments", 0)
            video_views = video.get("total_views", 1)
            total_engagement += (video.get("likes", 0) + video.get("comments", 0)) / video_views
        
        if video_stats:
            self.metrics["content_metrics"]["avg_views"] = total_views / len(video_stats)
            self.metrics["content_metrics"]["avg_engagement_rate"] = (
                total_engagement / len(video_stats) * 100
            )
        
        self._save_metrics()
    
    def get_health_score(self) -> dict:
        """Calculate overall system health score (0-100)."""
        scores = {}
        
        # Pipeline reliability score
        success_rate = self.metrics["pipeline_health"]["success_rate"]
        scores["reliability"] = success_rate  # 0-100
        
        # Content quality score
        avg_engagement = self.metrics["content_metrics"]["avg_engagement_rate"]
        scores["content_quality"] = min(100, avg_engagement * 10)  # Normalize to 0-100
        
        # Performance score
        error_rate = self.metrics["performance"]["error_rate"]
        scores["performance"] = max(0, 100 - (error_rate * 10))
        
        # System health score
        disk_trend = self.metrics["system_health"]["disk_usage_trend"]
        if disk_trend:
            disk_usage = disk_trend[-1].get("usage_percent", 0)
            scores["system"] = max(0, 100 - (disk_usage - 50) * 2)  # Penalize high usage
        else:
            scores["system"] = 100
        
        # Overall score
        overall = sum(scores.values()) / len(scores) if scores else 50
        scores["overall"] = overall
        
        return scores
    
    def get_trend_analysis(self) -> dict:
        """Analyze trends in key metrics."""
        trends = {}
        
        # Pipeline success rate trend
        if self.metrics["pipeline_health"]["total_runs"] > 5:
            current_success = self.metrics["pipeline_health"]["success_rate"]
            trends["pipeline_success"] = {
                "current": current_success,
                "direction": "improving" if current_success > 90 else "needs_attention"
            }
        
        # Average views trend
        avg_views = self.metrics["content_metrics"]["avg_views"]
        if avg_views > 0:
            trends["content_views"] = {
                "average": avg_views,
                "status": "growing" if avg_views > 200 else "needs_optimization"
            }
        
        # Engagement rate trend
        avg_engagement = self.metrics["content_metrics"]["avg_engagement_rate"]
        trends["engagement_rate"] = {
            "average": f"{avg_engagement:.2f}%",
            "status": "excellent" if avg_engagement > 1.0 else "good" if avg_engagement > 0.5 else "needs_improvement"
        }
        
        # System resource trends
        disk_trend = self.metrics["system_health"]["disk_usage_trend"]
        if len(disk_trend) > 1:
            current_disk = disk_trend[-1].get("usage_percent", 0)
            prev_disk = disk_trend[-2].get("usage_percent", 0)
            trends["disk_usage"] = {
                "current": current_disk,
                "trend": "increasing" if current_disk > prev_disk else "stable",
                "status": "critical" if current_disk > 85 else "warning" if current_disk > 70 else "healthy"
            }
        
        return trends


def format_dashboard(dashboard: QualityDashboard) -> str:
    """Format dashboard for display."""
    health_scores = dashboard.get_health_score()
    trends = dashboard.get_trend_analysis()
    metrics = dashboard.metrics
    
    # Overall health
    overall_score = health_scores.get("overall", 0)
    status_emoji = "🟢" if overall_score > 80 else "🟡" if overall_score > 60 else "🔴"
    
    report = f"\n{status_emoji} QUALITY DASHBOARD\n"
    report += "=" * 70 + "\n"
    
    # Health scores
    report += f"\n📊 HEALTH SCORES:\n"
    report += f"  Overall:        {overall_score:5.1f}/100\n"
    report += f"  Reliability:    {health_scores.get('reliability', 0):5.1f}/100\n"
    report += f"  Content:        {health_scores.get('content_quality', 0):5.1f}/100\n"
    report += f"  Performance:    {health_scores.get('performance', 0):5.1f}/100\n"
    report += f"  System:         {health_scores.get('system', 0):5.1f}/100\n"
    
    # Pipeline statistics
    pipeline = metrics["pipeline_health"]
    report += f"\n🔧 PIPELINE STATISTICS:\n"
    report += f"  Total Runs:     {pipeline['total_runs']}\n"
    report += f"  Success Rate:   {pipeline['success_rate']:.1f}%\n"
    report += f"  Avg Duration:   {pipeline['avg_duration_sec']:.0f}s\n"
    
    # Content statistics
    content = metrics["content_metrics"]
    report += f"\n📹 CONTENT STATISTICS:\n"
    report += f"  Total Videos:   {content['total_videos']}\n"
    report += f"  Total Views:    {content['total_views']}\n"
    report += f"  Avg Per Video:  {content['avg_views']:.0f}\n"
    report += f"  Engagement:     {content['avg_engagement_rate']:.2f}%\n"
    
    # Trends
    report += f"\n📈 TRENDS:\n"
    for trend_name, trend_data in trends.items():
        if isinstance(trend_data, dict):
            report += f"  • {trend_name.replace('_', ' ').title()}:\n"
            for key, value in trend_data.items():
                report += f"      {key}: {value}\n"
    
    report += "=" * 70 + "\n"
    return report


def get_alerts_from_dashboard(dashboard: QualityDashboard) -> list:
    """Generate alerts based on dashboard metrics."""
    alerts = []
    
    health_scores = dashboard.get_health_score()
    metrics = dashboard.metrics
    
    # Alert on low reliability
    if health_scores.get("reliability", 100) < 90:
        alerts.append({
            "severity": "warning",
            "message": f"Pipeline reliability below 90% ({health_scores['reliability']:.0f}%)"
        })
    
    # Alert on high disk usage
    disk_trend = metrics["system_health"]["disk_usage_trend"]
    if disk_trend and disk_trend[-1].get("usage_percent", 0) > 85:
        alerts.append({
            "severity": "critical",
            "message": f"Disk usage critically high ({disk_trend[-1]['usage_percent']:.0f}%)"
        })
    
    # Alert on low engagement
    if metrics["content_metrics"]["avg_engagement_rate"] < 0.3:
        alerts.append({
            "severity": "info",
            "message": "Content engagement rate below 0.3% - consider optimizing script or visuals"
        })
    
    # Alert on high error rate
    if metrics["performance"]["error_rate"] > 1.0:
        alerts.append({
            "severity": "warning",
            "message": f"Elevated error rate ({metrics['performance']['error_rate']:.1f} per run)"
        })
    
    return alerts
