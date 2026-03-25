"""
Autonomous Error Recovery & Self-Healing Module
Detects known failure patterns and applies automated fixes.
Implements retry logic with exponential backoff and fallback strategies.
"""

import os
import time
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class AutoRepair:
    """Self-healing system for common pipeline failures."""
    
    # Known error patterns and recovery strategies
    RECOVERY_PATTERNS = {
        "quota_exceeded": {
            "keywords": ["quota", "403", "quotaExceeded"],
            "strategy": "wait_and_retry",
            "wait_time": 3600,  # 1 hour
            "max_retries": 2
        },
        "network_timeout": {
            "keywords": ["timeout", "connection refused", "ConnectTimeout"],
            "strategy": "exponential_backoff",
            "max_retries": 3
        },
        "file_not_found": {
            "keywords": ["FileNotFoundError", "No such file"],
            "strategy": "skip_and_log",
            "severity": "warning"
        },
        "invalid_credentials": {
            "keywords": ["Unauthorized", "401", "invalid_grant"],
            "strategy": "alert_and_fail",
            "severity": "critical"
        },
        "memory_overflow": {
            "keywords": ["MemoryError", "out of memory"],
            "strategy": "reduce_batch_size",
            "severity": "warning"
        }
    }
    
    @staticmethod
    def classify_error(error_message: str) -> Optional[str]:
        """Identify error type from error message."""
        error_lower = error_message.lower()
        
        for error_type, pattern_info in AutoRepair.RECOVERY_PATTERNS.items():
            for keyword in pattern_info["keywords"]:
                if keyword.lower() in error_lower:
                    return error_type
        
        return None
    
    @staticmethod
    def retry_with_backoff(fn: Callable, max_attempts: int = 3, base_wait: float = 1.0, backoff_factor: float = 2.0) -> Any:
        """Retry a function with exponential backoff."""
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"🔄 Attempt {attempt + 1}/{max_attempts}")
                return fn()
            except Exception as e:
                last_error = e
                error_type = AutoRepair.classify_error(str(e))
                
                if attempt < max_attempts - 1:
                    wait_time = base_wait * (backoff_factor ** attempt)
                    logger.warning(f"⚠️  Attempt {attempt + 1} failed ({error_type}). Waiting {wait_time:.0f}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_attempts} attempts failed: {e}")
                    raise
        
        return None
    
    @staticmethod
    def quota_aware_retry(fn: Callable, wait_time: int = 3600) -> Any:
        """Special handling for quota errors - wait for reset."""
        try:
            return fn()
        except Exception as e:
            if "quota" in str(e).lower() or "403" in str(e):
                logger.warning(f"⚠️  Quota exceeded. Waiting {wait_time}s for reset...")
                time.sleep(wait_time)
                # Retry once after quota reset
                return fn()
            raise
    
    @staticmethod
    def handle_missing_file(file_path: str, fallback_path: str = None) -> Optional[str]:
        """Handle missing file gracefully with fallback options."""
        if os.path.exists(file_path):
            return file_path
        
        logger.warning(f"⚠️  File not found: {file_path}")
        
        # Try fallback path
        if fallback_path and os.path.exists(fallback_path):
            logger.info(f"📁 Using fallback file: {fallback_path}")
            return fallback_path
        
        logger.error(f"❌ No file found (even fallback)")
        return None
    
    @staticmethod
    def reduce_batch_size(current_size: int, reduction_factor: float = 0.5) -> int:
        """Reduce batch size to avoid memory issues."""
        new_size = max(1, int(current_size * reduction_factor))
        logger.warning(f"↓ Reducing batch size: {current_size} → {new_size}")
        return new_size
    
    @staticmethod
    def get_recovery_suggestion(error_message: str) -> str:
        """Get recovery suggestion based on error type."""
        error_type = AutoRepair.classify_error(error_message)
        
        if error_type == "quota_exceeded":
            return "Quota exceeded. Waiting until reset. Consider optimizing search parameters."
        elif error_type == "network_timeout":
            return "Network timeout. Retrying with exponential backoff."
        elif error_type == "file_not_found":
            return "File not found. Check if previous stage completed successfully."
        elif error_type == "invalid_credentials":
            return "Invalid credentials. Refresh YouTube token in GitHub Secrets."
        elif error_type == "memory_overflow":
            return "Out of memory. Reducing batch size and retrying."
        else:
            return "Unknown error. Check logs for details."


class ResilienceConfig:
    """Configuration for resilience parameters."""
    
    # Retry settings
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 2  # seconds
    BACKOFF_FACTOR = 2.0
    
    # Timeout settings
    SCRIPT_GENERATION_TIMEOUT = 120  # seconds
    VIDEO_ASSEMBLY_TIMEOUT = 600     # seconds
    UPLOAD_TIMEOUT = 900              # seconds
    
    # Resource limits
    MAX_BATCH_SIZE = 50
    MIN_BATCH_SIZE = 1
    MAX_CONCURRENT_JOBS = 3
    
    # Thresholds
    MIN_DISK_FREE_GB = 5.0
    MAX_MEMORY_PERCENT = 85
    MAX_API_ERROR_RATE = 0.2  # 20%
