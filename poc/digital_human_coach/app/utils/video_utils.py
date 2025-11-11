"""Video processing utilities"""
import subprocess
from pathlib import Path

import cv2
from loguru import logger


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    
    if fps > 0:
        duration = frame_count / fps
        return duration
    return 0


def extract_audio_from_video(video_path: str, audio_path: str) -> str:
    """Extract audio track from video using ffmpeg"""
    try:
        import ffmpeg
        
        # Check if this is the correct ffmpeg-python package
        if hasattr(ffmpeg, 'input'):
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, audio_path, acodec='pcm_s16le', ar='16000', ac='1')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"Extracted audio: {audio_path}")
            return audio_path
        else:
            raise AttributeError("Wrong ffmpeg package installed")
    except (ImportError, AttributeError) as e:
        # Fallback to subprocess
        logger.warning(f"ffmpeg-python not available ({e}), using subprocess")
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',  # Overwrite
            audio_path
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Extracted audio: {audio_path}")
        return audio_path


def resize_video(input_path: str, output_path: str, width: int = 640, height: int = 480) -> str:
    """Resize video to specified dimensions"""
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {input_path}")
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        resized = cv2.resize(frame, (width, height))
        out.write(resized)
    
    cap.release()
    out.release()
    
    logger.info(f"Resized video: {output_path}")
    return output_path
