"""
Advanced Pipeline Diagnostics & Health Monitoring
Continuously tracks system health, performance, and anomalies.
Generates diagnostic reports that enable autonomous issue detection.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class DiagnosticsCollector:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = time.time()
        self.total_duration_sec = None
        self.validation_result = None
        self.metrics = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "system": {},
            "errors": [],
            "warnings": [],
            "performance": {},
            "api_calls": {}
        }
    
    def check_system_resources(self) -> dict:
        """Check available disk, memory, and API quota."""
        try:
            import psutil
        except ImportError:
            # Fallback if psutil not available
            return {"status": "psutil_unavailable", "warning": "Install psutil for detailed monitoring"}
        
        disk = psutil.disk_usage('/')
        memory = psutil.virtual_memory()
        
        checks = {
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "issues": []
        }
        
        if disk.percent > 80:
            checks["issues"].append(f"⚠️ Low disk space: {disk.percent}% used")
        if memory.percent > 80:
            checks["issues"].append(f"⚠️ High memory usage: {memory.percent}% used")
        
        self.metrics["system"] = checks
        return checks
    
    def stage_start(self, stage_name: str):
        """Mark start of a pipeline stage."""
        self.metrics["stages"][stage_name] = {
            "status": "in_progress",
            "start_time": time.time(),
            "end_time": None,
            "duration_sec": None,
            "status_code": None
        }
    
    def stage_complete(self, stage_name: str, status_code: int = 0, error: str = None, success: bool = None):
        """Mark completion of a pipeline stage."""
        if stage_name in self.metrics["stages"]:
            stage = self.metrics["stages"][stage_name]
            stage["end_time"] = time.time()
            stage["duration_sec"] = stage["end_time"] - stage["start_time"]
            stage["status_code"] = status_code
            
            if success is not None:
                stage["status"] = "success" if success else "failed"
            else:
                stage["status"] = "success" if status_code == 0 else "failed"
            
            if error:
                stage["error"] = error
                self.metrics["errors"].append(f"{stage_name}: {error}")
            
            # Warn if stage took too long
            if stage["duration_sec"] > 300:  # 5 minutes
                self.metrics["warnings"].append(f"⚠️ {stage_name} took {stage['duration_sec']:.0f}s (expected <5min)")
    
    def log_error(self, message: str, stage: str = None, error_type: str = None):
        """Log an error with optional stage and error type."""
        error_msg = message
        if stage:
            error_msg = f"{stage}: {message}"
        if error_type:
            error_msg = f"[{error_type}] {error_msg}"
        self.metrics["errors"].append(error_msg)
    
    def log_warning(self, message: str):
        """Log a warning message."""
        self.metrics["warnings"].append(message)
    
    def check_file_exists(self, file_path: str) -> bool:
        """Verify critical output files exist."""
        exists = os.path.exists(file_path)
        if not exists:
            self.metrics["errors"].append(f"Missing file: {file_path}")
        return exists
    
    def check_file_size(self, file_path: str, min_bytes: int = 1000, min_kb: int = None) -> bool:
        """Verify file is not corrupted (has reasonable size)."""
        if not os.path.exists(file_path):
            return False
        
        # Support both min_bytes and min_kb parameters
        if min_kb is not None:
            min_bytes = min_kb * 1024
        
        size_bytes = os.path.getsize(file_path)
        if size_bytes < min_bytes:
            size_mb = size_bytes / (1024**2)
            min_mb = min_bytes / (1024**2)
            self.metrics["errors"].append(f"File too small: {file_path} ({size_mb:.2f} MB, expected >{min_mb:.2f} MB)")
            return False
        return True
    
    def log_api_call(self, api_name: str, status: int = 200, duration: float = None, **kwargs):
        """Track API call performance."""
        if api_name not in self.metrics["api_calls"]:
            self.metrics["api_calls"][api_name] = []
        
        call_data = {
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if duration is not None:
            call_data["duration"] = duration
        
        # Add any additional kwargs (results, error, video_id, etc.)
        call_data.update(kwargs)
        
        self.metrics["api_calls"][api_name].append(call_data)
        
        if status == 403:
            self.metrics["warnings"].append(f"⚠️ API quota exceeded: {api_name}")
        elif status >= 400:
            self.metrics["errors"].append(f"API error: {api_name} ({status})")
    
    def generate_report(self) -> dict:
        """Generate comprehensive diagnostic report."""
        if self.total_duration_sec is None:
            self.total_duration_sec = time.time() - self.start_time
        
        self.metrics["total_duration_sec"] = self.total_duration_sec
        self.metrics["run_status"] = "success" if not self.metrics["errors"] else "failed"
        self.metrics["error_count"] = len(self.metrics["errors"])
        self.metrics["warning_count"] = len(self.metrics["warnings"])
        
        if self.validation_result:
            self.metrics["validation"] = self.validation_result
        
        return self.metrics
    
    def save_report(self, output_path: str = None):
        """Save diagnostic report to JSON file."""
        if output_path is None:
            job_folder = os.path.join(os.path.dirname(__file__), 'media', f'job_{self.job_id}')
            output_path = os.path.join(job_folder, 'diagnostics.json')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Diagnostic report saved: {output_path}")
        return output_path


def print_diagnostic_summary(report: dict):
    """Pretty-print diagnostic summary."""
    print("\n" + "=" * 70)
    print("📊 PIPELINE DIAGNOSTICS SUMMARY")
    print("=" * 70)
    print(f"Job ID: {report['job_id']}")
    print(f"Status: {report['run_status'].upper()}")
    print(f"Duration: {report['total_duration_sec']:.1f}s")
    print(f"Errors: {report['error_count']} | Warnings: {report['warning_count']}")
    
    if report["errors"]:
        print(f"\n❌ ERRORS ({len(report['errors'])}):")
        for error in report["errors"][:5]:
            print(f"   - {error}")
        if len(report["errors"]) > 5:
            print(f"   ... and {len(report['errors']) - 5} more")
    
    if report["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
        for warning in report["warnings"][:5]:
            print(f"   - {warning}")
        if len(report["warnings"]) > 5:
            print(f"   ... and {len(report['warnings']) - 5} more")
    
    print("\n📈 STAGE PERFORMANCE:")
    for stage_name, stage_data in report["stages"].items():
        status_icon = "✅" if stage_data["status"] == "success" else "❌"
        print(f"   {status_icon} {stage_name}: {stage_data['duration_sec']:.1f}s")
    
    print("\n💾 SYSTEM RESOURCES:")
    sys_data = report.get("system", {})
    print(f"   Disk: {sys_data.get('disk_usage_percent', 'N/A')}% used")
    print(f"   Memory: {sys_data.get('memory_percent', 'N/A')}% used")
    print(f"   CPU: {sys_data.get('cpu_percent', 'N/A')}%")
    
    print("\n" + "=" * 70)


# Alias for use in pipeline.py
format_diagnostic_summary = print_diagnostic_summary
