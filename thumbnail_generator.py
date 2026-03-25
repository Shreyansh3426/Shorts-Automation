import os
import subprocess
import logging
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def generate_thumbnail(job_id: str, topic: str, clips_json: List[str], variant_id: Optional[str] = None) -> str:
    """
    Generates a high-CTR YouTube Shorts thumbnail using one of the clips.
    Returns the full path to thumbnail.jpg
    """
    job_folder = os.path.join(os.path.dirname(__file__), '..', 'media', f'job_{job_id}')
    os.makedirs(job_folder, exist_ok=True)
    
    if len(clips_json) < 2:
        logger.error(f"❌ Not enough clips ({len(clips_json)})")
        raise ValueError("Need at least 2 clips for thumbnail")
    
    clip_path = clips_json[1]
    if not os.path.exists(clip_path):
        logger.error(f"❌ Clip not found: {clip_path}")
        raise FileNotFoundError(f"Clip not found: {clip_path}")
    
    frame_path = os.path.join(job_folder, 'frame.jpg')
    thumbnail_filename = f'thumbnail_{variant_id}.jpg' if variant_id else 'thumbnail.jpg'
    thumbnail_path = os.path.join(job_folder, thumbnail_filename)
    
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', clip_path,
            '-ss', '2',
            '-vframes', '1',
            frame_path
        ], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg failed: {e.stderr.decode()}")
        raise
    
    try:
        img = Image.open(frame_path)
        width, height = img.size
        
        aspect_ratio = width / height
        target_ratio = 1080 / 1920
        
        if aspect_ratio > target_ratio:
            new_width = int(height * target_ratio)
            crop_left = (width - new_width) // 2
            img = img.crop((crop_left, 0, crop_left + new_width, height))
        else:
            new_height = int(width / target_ratio)
            crop_top = (height - new_height) // 2
            img = img.crop((0, crop_top, width, crop_top + new_height))
        
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    except Exception as e:
        logger.error(f"❌ Image processing failed: {e}")
        raise
    
    shock_text = topic.upper()
    shock_text = shock_text.replace("WHY DO ", "").replace("#SHORTS", "").strip()
    if not shock_text.endswith("?"):
        shock_text += "?"
    
    try:
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
            emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 120)
        except:
            font = ImageFont.load_default()
            emoji_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), shock_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (1080 - text_width) // 2
        text_y = 200
        
        for adj_x in range(-8, 9):
            for adj_y in range(-8, 9):
                if adj_x != 0 or adj_y != 0:
                    draw.text((text_x + adj_x, text_y + adj_y), shock_text, font=font, fill='black')
        
        draw.text((text_x, text_y), shock_text, font=font, fill='white')
        
        emoji = '😱'
        emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
        emoji_width = emoji_bbox[2] - emoji_bbox[0]
        emoji_x = (1080 - emoji_width) // 2
        emoji_y = text_y + 190
        
        draw.text((emoji_x, emoji_y), emoji, font=emoji_font, fill='white')
        
    except Exception as e:
        logger.error(f"❌ Text overlay failed: {e}")
        raise
    
    try:
        img.save(thumbnail_path, 'JPEG', quality=95, optimize=True)
        logger.info(f"✅ Thumbnail generated: {thumbnail_path}")
        return thumbnail_path
    except Exception as e:
        logger.error(f"❌ Thumbnail save failed: {e}")
        raise
