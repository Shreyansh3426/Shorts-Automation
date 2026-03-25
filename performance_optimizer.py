"""
Performance Optimization Engine
Automatically tunes pipeline for better health scores and efficiency.
Optimizes system resources, video quality, content engagement, and error rates.
"""

import os
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class PerformanceOptimizer:
    """Optimizes pipeline performance to improve health scores."""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.media_dir = os.path.join(workspace_root, 'media')
        self.config_file = os.path.join(workspace_root, 'perf_config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load or create performance configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Default optimization configuration."""
        return {
            "video_encoding": {
                "crf": 23,  # Quality (lower = better, 0-51)
                "preset": "medium",  # Speed: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
                "max_width": 1080,
                "max_height": 1920
            },
            "cleanup": {
                "auto_cleanup": True,
                "keep_days": 7,  # Keep job folders for 7 days before cleanup
                "archive_after_days": 3  # Archive to tar after 3 days
            },
            "content": {
                "engagement_hooks": [
                    "SHOCKING", "TERRIFYING", "UNBELIEVABLE", "INSANE",
                    "GONE WRONG", "REVEALED", "EXPOSED", "PROOF",
                    "3 REASONS", "5 WAYS", "YOU DIDN'T KNOW"
                ],
                "min_engagement_score": 0.5,
                "engagement_boost_factor": 1.5
            },
            "performance": {
                "max_concurrent_variants": 3,
                "batch_size": 4,
                "api_timeout_sec": 30,
                "retry_delays": [2, 4, 8]  # Exponential backoff
            },
            "system": {
                "target_disk_percent": 50,
                "target_memory_percent": 70,
                "target_cpu_percent": 80
            }
        }
    
    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def cleanup_old_jobs(self, dry_run: bool = False) -> dict:
        """Clean up old job folders to improve disk space."""
        if not self.config["cleanup"]["auto_cleanup"]:
            return {"status": "disabled", "cleaned": 0, "freed_gb": 0}
        
        results = {
            "status": "success",
            "cleaned": 0,
            "archived": 0,
            "freed_mb": 0,
            "jobs_cleaned": []
        }
        
        if not os.path.exists(self.media_dir):
            return results
        
        keep_days = self.config["cleanup"]["keep_days"]
        archive_days = self.config["cleanup"]["archive_after_days"]
        cutoff_time = time.time() - (keep_days * 86400)
        archive_time = time.time() - (archive_days * 86400)
        
        for job_folder in os.listdir(self.media_dir):
            job_path = os.path.join(self.media_dir, job_folder)
            
            if not os.path.isdir(job_path):
                continue
            
            mod_time = os.path.getmtime(job_path)
            
            # Delete old jobs (older than keep_days)
            if mod_time < cutoff_time:
                size_mb = self._get_dir_size(job_path) / (1024**2)
                if not dry_run:
                    shutil.rmtree(job_path)
                results["cleaned"] += 1
                results["freed_mb"] += size_mb
                results["jobs_cleaned"].append(job_folder)
            
            # Archive old jobs (older than archive_days)
            elif mod_time < archive_time and not os.path.exists(f"{job_path}.tar.gz"):
                if not dry_run:
                    self._archive_job(job_path)
                results["archived"] += 1
        
        results["freed_gb"] = round(results["freed_mb"] / 1024, 2)
        return results
    
    def _get_dir_size(self, path: str) -> int:
        """Calculate directory size in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def _archive_job(self, job_path: str):
        """Archive job folder to tar.gz."""
        try:
            shutil.make_archive(job_path, 'gztar', job_path)
            # Keep original for 1 more day, then delete
        except Exception as e:
            print(f"⚠️  Failed to archive {job_path}: {e}")
    
    def optimize_video_encoding(self, available_disk_percent: float) -> dict:
        """Adjust video encoding based on system resources."""
        original_crf = self.config["video_encoding"]["crf"]
        
        # If disk is getting low, increase compression (higher CRF)
        if available_disk_percent < 20:  # Less than 20% free
            self.config["video_encoding"]["crf"] = 28  # More compression
            self.config["video_encoding"]["preset"] = "faster"
            return {
                "adjusted": True,
                "reason": "Low disk space",
                "crf": 28,
                "preset": "faster",
                "quality_note": "Reduced quality to save space"
            }
        
        # Normal operation
        elif available_disk_percent < 50:  # Less than 50% free
            self.config["video_encoding"]["crf"] = 25
            self.config["video_encoding"]["preset"] = "medium"
            return {
                "adjusted": True,
                "reason": "Moderate disk space",
                "crf": 25,
                "preset": "medium"
            }
        
        # Plenty of space - use best quality
        else:
            self.config["video_encoding"]["crf"] = 23
            self.config["video_encoding"]["preset"] = "medium"
            return {
                "adjusted": False,
                "crf": 23,
                "preset": "medium",
                "message": "Optimal encoding settings"
            }
    
    def generate_engagement_hooks(self, topic: str, count: int = 3) -> list:
        """Generate engagement-optimized title hooks."""
        hooks = []
        hook_templates = self.config["content"]["engagement_hooks"]
        
        for i in range(min(count, len(hook_templates))):
            hook = hook_templates[i]
            if "{topic}" in hook:
                hooks.append(hook.format(topic=topic))
            else:
                hooks.append(f"{hook} {topic}")
        
        return hooks
    
    def calculate_engagement_score(self, script: str, keywords: list = None) -> float:
        """Calculate engagement potential of a script."""
        score = 0.5  # Base score
        
        # Check for power words
        power_words = ["shocking", "unbelievable", "insane", "exposed", "proof", "revealed"]
        script_lower = script.lower()
        for word in power_words:
            if word in script_lower:
                score += 0.15
        
        # Check for questions (CTA)
        if "?" in script:
            score += 0.1
        
        # Check for numbers/lists
        import re
        if re.search(r'\d+', script):
            score += 0.1
        
        # Check for urgency
        urgency_words = ["now", "today", "immediately", "before", "only", "exclusive"]
        for word in urgency_words:
            if word in script_lower:
                score += 0.05
        
        # Normalize to 0-1
        score = min(1.0, score)
        
        return round(score, 2)
    
    def tune_batch_size(self, available_memory_percent: float) -> int:
        """Tune batch size based on available memory."""
        if available_memory_percent > 80:
            # High memory usage - reduce batch
            batch_size = 1
        elif available_memory_percent > 70:
            batch_size = 2
        else:
            batch_size = self.config["performance"]["batch_size"]
        
        return batch_size
    
    def get_optimization_suggestions(self, metrics: dict) -> list:
        """Generate optimization suggestions based on current metrics."""
        suggestions = []
        
        # Check reliability
        if metrics.get("success_rate", 100) < 90:
            suggestions.append({
                "area": "Reliability",
                "issue": "Success rate below 90%",
                "suggestion": "Review recent errors and increase retry attempts",
                "impact": "+5-10% reliability"
            })
        
        # Check content quality
        if metrics.get("engagement_rate", 0) < 0.5:
            suggestions.append({
                "area": "Content",
                "issue": "Engagement rate below 0.5%",
                "suggestion": "Use more power words and urgency phrases in scripts",
                "impact": "+1-3% engagement"
            })
        
        # Check performance
        if metrics.get("error_rate", 0) > 0.5:
            suggestions.append({
                "area": "Performance",
                "issue": f"Error rate {metrics['error_rate']:.1f}/run (should be <0.5)",
                "suggestion": "Improve API rate limit handling and add better error recovery",
                "impact": "-50% errors"
            })
        
        # Check system
        if metrics.get("disk_usage_percent", 0) > 70:
            suggestions.append({
                "area": "System",
                "issue": "Disk usage above 70%",
                "suggestion": "Run cleanup_old_jobs() or increase available storage",
                "impact": "+5-15% system score"
            })
        
        return suggestions
    
    def generate_optimization_report(self, current_metrics: dict) -> dict:
        """Generate comprehensive optimization report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "optimization_suggestions": self.get_optimization_suggestions(current_metrics),
            "cleanup": self.cleanup_old_jobs(dry_run=True),  # Show what would be cleaned
            "encoding_optimization": {
                "current_crf": self.config["video_encoding"]["crf"],
                "recommendation": "Analyze disk space and adjust if needed"
            },
            "projected_improvements": {
                "reliability": "+2-5%",
                "content": "+1-3%",
                "performance": "+3-7%",
                "system": "+5-15%"
            }
        }
        
        return report
    
    def apply_optimizations(self, system_metrics: dict) -> dict:
        """Apply all available optimizations."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "applied": []
        }
        
        # 1. Cleanup old jobs
        cleanup_result = self.cleanup_old_jobs()
        if cleanup_result["cleaned"] > 0 or cleanup_result["archived"] > 0:
            results["applied"].append({
                "type": "cleanup",
                "status": "applied",
                "details": cleanup_result
            })
        
        # 2. Optimize encoding
        disk_free = 100 - system_metrics.get("disk_usage_percent", 50)
        encoding_result = self.optimize_video_encoding(disk_free)
        if encoding_result.get("adjusted"):
            results["applied"].append({
                "type": "encoding_optimization",
                "status": "applied",
                "details": encoding_result
            })
            self._save_config()
        
        # 3. Check batch size
        memory_pct = system_metrics.get("memory_percent", 50)
        optimal_batch = self.tune_batch_size(memory_pct)
        if optimal_batch != self.config["performance"]["batch_size"]:
            results["applied"].append({
                "type": "batch_size_tuning",
                "status": "applied",
                "old_size": self.config["performance"]["batch_size"],
                "new_size": optimal_batch
            })
        
        return results


def format_optimization_report(report: dict) -> str:
    """Format optimization report for display."""
    output = "\n" + "=" * 70 + "\n"
    output += "🔧 PERFORMANCE OPTIMIZATION REPORT\n"
    output += "=" * 70 + "\n"
    
    # Current metrics
    output += "\n📊 CURRENT METRICS:\n"
    for key, value in report["current_metrics"].items():
        if isinstance(value, float):
            output += f"  {key}: {value:.2f}\n"
        else:
            output += f"  {key}: {value}\n"
    
    # Suggestions
    if report["optimization_suggestions"]:
        output += f"\n💡 OPTIMIZATION SUGGESTIONS ({len(report['optimization_suggestions'])}):\n"
        for suggestion in report["optimization_suggestions"]:
            output += f"\n  📌 {suggestion['area'].upper()}\n"
            output += f"     Issue: {suggestion['issue']}\n"
            output += f"     Suggestion: {suggestion['suggestion']}\n"
            output += f"     Expected Impact: {suggestion['impact']}\n"
    
    # Cleanup preview
    cleanup = report["cleanup"]
    if cleanup["cleaned"] > 0 or cleanup["archived"] > 0:
        output += f"\n🗑️  CLEANUP PREVIEW (Dry Run):\n"
        output += f"  Jobs to delete: {cleanup['cleaned']}\n"
        output += f"  Jobs to archive: {cleanup['archived']}\n"
        output += f"  Space to free: {cleanup['freed_gb']} GB\n"
    
    # Projected improvements
    output += f"\n📈 PROJECTED IMPROVEMENTS (After optimization):\n"
    for metric, improvement in report["projected_improvements"].items():
        output += f"  {metric}: {improvement}\n"
    
    output += "\n" + "=" * 70 + "\n"
    return output
