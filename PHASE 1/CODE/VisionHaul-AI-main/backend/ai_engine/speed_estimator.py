import math
import numpy as np

class SpeedEstimator:
    """
    Speed Detection Module.
    Calculates truck velocity in km/h based on trajectory centroid tracking,
    distance calibration (homography / pixels per meter), and frame rate.
    Evaluates overspeed condition: Speed > Limit -> OVERSPEED ALERT.
    """
    def __init__(self, pixels_per_meter=18.5, fps=25, speed_limit=60.0):
        self.pixels_per_meter = pixels_per_meter
        self.fps = fps
        self.speed_limit = speed_limit

    def set_speed_limit(self, new_limit):
        self.speed_limit = float(new_limit)

    def set_calibration(self, ppm):
        self.pixels_per_meter = float(ppm)

    def estimate_speed(self, track):
        """
        Estimates speed from track history.
        track.history contains tuples of (cx, cy, timestamp).
        Returns:
            speed_kmh (float): estimated speed in km/h
            is_overspeed (bool): True if speed > speed_limit
        """
        history = list(track.history)
        if len(history) < 4:
            # Need at least 4 frame points for stable velocity
            return getattr(track, 'speed_kmh', 52.0), False

        # Use recent 10-15 frames for velocity calculation
        recent_pts = history[-min(len(history), 15):]
        
        # Calculate displacement in pixels
        p_start = recent_pts[0]
        p_end = recent_pts[-1]
        
        dx = p_end[0] - p_start[0]
        dy = p_end[1] - p_start[1]
        pixel_distance = math.sqrt(dx * dx + dy * dy)
        
        dt = p_end[2] - p_start[2]
        if dt <= 0.001:
            dt = len(recent_pts) / float(self.fps)
            
        # Distance in meters
        meters = pixel_distance / max(1.0, self.pixels_per_meter)
        
        # Speed in m/s -> km/h
        speed_mps = meters / max(0.01, dt)
        speed_kmh = speed_mps * 3.6
        
        # Apply perspective scaling (vehicles closer to bottom of camera appear faster/larger)
        cy = p_end[1]
        perspective_scale = 1.0 + (cy / 800.0) * 0.15
        speed_kmh = speed_kmh * perspective_scale
        
        # Smooth with previous speed if available
        if hasattr(track, 'speed_kmh') and track.speed_kmh > 0:
            speed_kmh = 0.7 * speed_kmh + 0.3 * track.speed_kmh
            
        speed_kmh = round(max(15.0, min(140.0, speed_kmh)), 1)
        is_overspeed = speed_kmh > self.speed_limit
        
        track.speed_kmh = speed_kmh
        track.is_overspeed = is_overspeed
        
        return speed_kmh, is_overspeed
