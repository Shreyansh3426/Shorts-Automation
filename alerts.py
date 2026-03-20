import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_slack_alert(message: str):
    """Send alert to Slack webhook if configured."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("⚠️  SLACK_WEBHOOK_URL not configured, skipping Slack alert")
        return
    
    try:
        payload = {"text": message}
        requests.post(webhook_url, json=payload, timeout=5)
        logger.info("📢 Slack alert sent")
    except Exception as e:
        logger.warning(f"⚠️  Failed to send Slack alert: {e}")

def send_failure_alert(job_id: str, error: str, stage: str):
    """Send failure alert with job context."""
    github_run = os.getenv("GITHUB_RUN_ID", "local")
    repo = os.getenv("GITHUB_REPOSITORY", "local/repo")
    
    message = f"""🚨 SHORTS PIPELINE FAILED
Job: {job_id}
Stage: {stage}
Error: {error}
Run: https://github.com/{repo}/actions/runs/{github_run}"""
    
    send_slack_alert(message)
