"""
Pose Estimation Service using MediaPipe
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from app.backend.models.schemas import PoseMetrics


class PoseService:
    """MediaPipe-based pose estimation service"""
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        tracking_confidence: float = 0.5
    ):
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=confidence_threshold,
                min_tracking_confidence=tracking_confidence
            )
            self.confidence_threshold = confidence_threshold
            logger.info("Initialized MediaPipe Pose service")
        except ImportError:
            raise ImportError("mediapipe not installed. Install with: pip install mediapipe")
    
    def analyze_video(self, video_path: str) -> PoseMetrics:
        """
        Analyze video for pose metrics
        
        Returns:
            PoseMetrics object with comprehensive analysis
        """
        logger.info(f"Analyzing pose in video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Tracking variables
        frames_analyzed = 0
        successful_detections = 0
        gesture_movements = []
        posture_scores = []
        shoulder_angles = []
        hand_positions = []
        eye_contact_frames = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = self.pose.process(rgb_frame)
            frames_analyzed += 1
            
            if results.pose_landmarks:
                successful_detections += 1
                landmarks = results.pose_landmarks.landmark
                
                # Calculate posture score
                posture_score = self._calculate_posture_score(landmarks)
                posture_scores.append(posture_score)
                
                # Track shoulder alignment
                shoulder_angle = self._calculate_shoulder_angle(landmarks)
                if shoulder_angle is not None:
                    shoulder_angles.append(shoulder_angle)
                
                # Track hand movements
                hand_pos = self._get_hand_positions(landmarks)
                hand_positions.append(hand_pos)
                
                # Estimate eye contact (simplified)
                if self._estimate_eye_contact(landmarks):
                    eye_contact_frames += 1
        
        cap.release()
        
        # Calculate metrics
        gesture_count = self._count_gestures(hand_positions)
        movement_smoothness = self._calculate_smoothness(hand_positions)
        tracking_quality = successful_detections / frames_analyzed if frames_analyzed > 0 else 0
        
        metrics = PoseMetrics(
            posture_score=np.mean(posture_scores) if posture_scores else 5.0,
            gesture_count=gesture_count,
            movement_smoothness=movement_smoothness,
            eye_contact_score=self._calculate_eye_contact_score(
                eye_contact_frames, frames_analyzed
            ),
            body_openness_score=self._calculate_body_openness(shoulder_angles),
            frames_analyzed=frames_analyzed,
            tracking_quality=tracking_quality
        )
        
        logger.info(f"Pose analysis complete: {frames_analyzed} frames, "
                   f"{successful_detections} detections ({tracking_quality:.1%})")
        
        return metrics
    
    def _calculate_posture_score(self, landmarks) -> float:
        """Calculate posture score (0-10) based on spine alignment"""
        try:
            # Get key landmarks
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            
            # Calculate midpoints
            shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
            hip_mid_y = (left_hip.y + right_hip.y) / 2
            
            # Good posture: nose should be aligned above shoulders
            vertical_alignment = abs(nose.x - (left_shoulder.x + right_shoulder.x) / 2)
            
            # Shoulder-hip alignment
            spine_straightness = abs(
                (left_shoulder.x + right_shoulder.x) / 2 -
                (left_hip.x + right_hip.x) / 2
            )
            
            # Score: lower values = better posture
            score = 10 - (vertical_alignment * 20 + spine_straightness * 20)
            return max(0, min(10, score))
        except Exception as e:
            logger.warning(f"Error calculating posture score: {e}")
            return 5.0
    
    def _calculate_shoulder_angle(self, landmarks) -> Optional[float]:
        """Calculate angle of shoulders relative to horizontal"""
        try:
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            angle = np.arctan2(
                right_shoulder.y - left_shoulder.y,
                right_shoulder.x - left_shoulder.x
            ) * 180 / np.pi
            
            return abs(angle)
        except Exception:
            return None
    
    def _get_hand_positions(self, landmarks) -> Tuple[float, float, float, float]:
        """Get normalized hand positions (left_x, left_y, right_x, right_y)"""
        try:
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            return (left_wrist.x, left_wrist.y, right_wrist.x, right_wrist.y)
        except Exception:
            return (0, 0, 0, 0)
    
    def _count_gestures(self, hand_positions: List[Tuple]) -> int:
        """Count significant hand movements as gestures"""
        if len(hand_positions) < 2:
            return 0
        
        gesture_count = 0
        threshold = 0.1  # Movement threshold
        
        for i in range(1, len(hand_positions)):
            prev = hand_positions[i-1]
            curr = hand_positions[i]
            
            # Calculate movement magnitude
            left_movement = np.sqrt((curr[0] - prev[0])**2 + (curr[1] - prev[1])**2)
            right_movement = np.sqrt((curr[2] - prev[2])**2 + (curr[3] - prev[3])**2)
            
            if left_movement > threshold or right_movement > threshold:
                gesture_count += 1
        
        # Normalize to meaningful gestures (group consecutive movements)
        return max(1, gesture_count // 10)
    
    def _calculate_smoothness(self, hand_positions: List[Tuple]) -> float:
        """Calculate movement smoothness (0-10, higher = smoother)"""
        if len(hand_positions) < 3:
            return 5.0
        
        # Calculate acceleration changes (jerk)
        velocities = []
        for i in range(1, len(hand_positions)):
            prev = hand_positions[i-1]
            curr = hand_positions[i]
            vel = np.sqrt(
                (curr[0] - prev[0])**2 + (curr[1] - prev[1])**2 +
                (curr[2] - prev[2])**2 + (curr[3] - prev[3])**2
            )
            velocities.append(vel)
        
        # Calculate variance in velocities
        if len(velocities) > 0:
            variance = np.var(velocities)
            # Lower variance = smoother movement
            smoothness = 10 / (1 + variance * 100)
            return min(10, smoothness)
        
        return 5.0
    
    def _estimate_eye_contact(self, landmarks) -> bool:
        """Estimate if person is making eye contact (facing camera)"""
        try:
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
            left_ear = landmarks[self.mp_pose.PoseLandmark.LEFT_EAR]
            right_ear = landmarks[self.mp_pose.PoseLandmark.RIGHT_EAR]
            
            # If both ears are visible and nose is centered, likely facing camera
            ears_visible = (
                left_ear.visibility > 0.5 and
                right_ear.visibility > 0.5
            )
            nose_centered = 0.3 < nose.x < 0.7
            
            return ears_visible and nose_centered
        except Exception:
            return False
    
    def _calculate_eye_contact_score(
        self,
        eye_contact_frames: int,
        total_frames: int
    ) -> float:
        """Calculate eye contact score (0-10)"""
        if total_frames == 0:
            return 5.0
        
        ratio = eye_contact_frames / total_frames
        return min(10, ratio * 10)
    
    def _calculate_body_openness(self, shoulder_angles: List[float]) -> float:
        """Calculate body openness score based on shoulder position"""
        if not shoulder_angles:
            return 5.0
        
        # Lower angle = more open posture
        avg_angle = np.mean(shoulder_angles)
        # Good range: 0-10 degrees
        openness = 10 - min(10, avg_angle / 2)
        return max(0, openness)
    
    def save_annotated_video(
        self,
        input_path: str,
        output_path: str
    ) -> str:
        """Save video with pose landmarks drawn"""
        logger.info(f"Creating annotated video: {output_path}")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            # Draw landmarks
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )
            
            out.write(frame)
        
        cap.release()
        out.release()
        
        logger.info(f"Annotated video saved: {output_path}")
        return output_path
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'pose'):
            self.pose.close()
