"""
Run Validator Module
Validates pipeline run completeness and output correctness.
Ensures all expected artifacts are generated and valid.
"""

import os
import json
from pathlib import Path
from typing import dict, list, tuple

class RunValidator:
    """Validates pipeline run outputs and completeness."""
    
    def __init__(self, job_folder: str):
        self.job_folder = job_folder
        self.errors = []
        self.warnings = []
        self.validated_artifacts = []
    
    def validate_run(self, topic: str, variant_count: int = 3) -> dict:
        """Validate complete pipeline run."""
        results = {
            "status": "valid",
            "topic": topic,
            "errors": [],
            "warnings": [],
            "artifacts": [],
            "missing": []
        }
        
        # 1. Check voice files
        voice_files_found = 0
        for i in range(variant_count):
            variant = chr(65 + i)  # A, B, C
            voice_file = os.path.join(self.job_folder, f'voice_{variant}.mp3')
            if os.path.exists(voice_file):
                voice_files_found += 1
                results["artifacts"].append(f'voice_{variant}.mp3')
            else:
                results["missing"].append(f'voice_{variant}.mp3')
        
        if voice_files_found < variant_count:
            results["warnings"].append(f"Missing voice files: {variant_count - voice_files_found} variants")
        
        # 2. Check video files
        video_files_found = 0
        for i in range(variant_count):
            variant = chr(65 + i)  # A, B, C
            video_file = os.path.join(self.job_folder, f'final_{variant}.mp4')
            if os.path.exists(video_file):
                video_files_found += 1
                results["artifacts"].append(f'final_{variant}.mp4')
            else:
                results["missing"].append(f'final_{variant}.mp4')
        
        if video_files_found < variant_count:
            results["errors"].append(f"Missing video files: {variant_count - video_files_found} variants")
            results["missing"].extend([f'final_{chr(65+i)}.mp4' for i in range(variant_count)])
        
        # 3. Check thumbnail files
        thumbnail_files_found = 0
        for i in range(variant_count):
            variant = chr(65 + i)  # A, B, C
            thumb_file = os.path.join(self.job_folder, f'thumbnail_{variant}.jpg')
            if os.path.exists(thumb_file):
                thumbnail_files_found += 1
                results["artifacts"].append(f'thumbnail_{variant}.jpg')
            else:
                results["missing"].append(f'thumbnail_{variant}.jpg')
        
        # 4. Check metadata
        metadata_file = os.path.join(self.job_folder, 'metadata.json')
        if os.path.exists(metadata_file):
            results["artifacts"].append('metadata.json')
        else:
            results["warnings"].append('Missing metadata.json')
        
        # Final status determination
        if results["errors"]:
            results["status"] = "invalid"
        elif results["missing"]:
            results["status"] = "incomplete"
        
        return results
    
    def _check_variant_files(self, directory: str, pattern: str, expected_count: int) -> dict:
        """Check for expected variant files."""
        result = {"missing": [], "found": []}
        
        if not os.path.exists(directory):
            result["missing"] = [f"{pattern} ({i+1})" for i in range(expected_count)]
            return result
        
        files = os.listdir(directory)
        for i in range(expected_count):
            variant = chr(65 + i)  # A, B, C
            variants = [
                f"{pattern.replace('*', variant)}",
                f"{pattern.replace('_*', f'_{i+1}')}",
                f"{pattern.replace('*', str(i+1))}"
            ]
            
            found = any(f in files for f in variants)
            if found:
                result["found"].append(variant)
            else:
                result["missing"].append(variant)
        
        return result
    
    def validate_file_integrity(self, file_path: str) -> tuple[bool, str]:
        """Validate file integrity and format."""
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "File is empty"
        
        # Check file types
        if file_path.endswith('.json'):
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
                return True, f"Valid JSON ({file_size} bytes)"
            except Exception as e:
                return False, f"Invalid JSON: {str(e)}"
        
        elif file_path.endswith('.mp3'):
            # Check audio file header
            with open(file_path, 'rb') as f:
                header = f.read(3)
                if header == b'ID3' or header[:2] == b'\xFF\xFB':
                    return True, f"Valid MP3 ({file_size} bytes)"
                return False, "Invalid MP3 file format"
        
        elif file_path.endswith('.mp4'):
            # Check video file header (ftyp box)
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if b'ftyp' in header or b'mdat' in header:
                    return True, f"Valid MP4 ({file_size} bytes)"
                return False, "Invalid MP4 file format"
        
        elif file_path.endswith('.jpg'):
            # Check JPEG header
            with open(file_path, 'rb') as f:
                header = f.read(3)
                if header == b'\xFF\xD8\xFF':
                    return True, f"Valid JPEG ({file_size} bytes)"
                return False, "Invalid JPEG file format"
        
        return True, f"File valid ({file_size} bytes)"


def format_validation_report(validation: dict) -> str:
    """Format validation report for display."""
    status_icon = {
        'valid': '✅',
        'incomplete': '⚠️',
        'invalid': '❌'
    }
    
    report = f"\n{status_icon.get(validation['status'], '❓')} VALIDATION: {validation['status'].upper()}\n"
    report += f"Topic: {validation['topic']}\n"
    report += "=" * 70 + "\n"
    
    if validation['artifacts']:
        report += f"\n✓ Artifacts ({len(validation['artifacts'])}):\n"
        for artifact in validation['artifacts']:
            report += f"  • {artifact}\n"
    
    if validation['warnings']:
        report += f"\n⚠️  Warnings ({len(validation['warnings'])}):\n"
        for warning in validation['warnings']:
            report += f"  • {warning}\n"
    
    if validation['errors']:
        report += f"\n❌ Errors ({len(validation['errors'])}):\n"
        for error in validation['errors']:
            report += f"  • {error}\n"
    
    if validation['missing']:
        report += f"\n🔍 Missing:\n"
        for missing in validation['missing']:
            report += f"  • {missing}\n"
    
    report += "=" * 70 + "\n"
    return report
