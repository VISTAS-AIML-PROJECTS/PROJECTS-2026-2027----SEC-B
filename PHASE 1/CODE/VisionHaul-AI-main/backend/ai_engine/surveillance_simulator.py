import os
import cv2
import numpy as np
import time
import random
from datetime import datetime, timezone
from backend.config import Config

class RealTruckSprite:
    """
    Represents a real photographic commercial heavy truck sprite moving down highway lanes.
    """
    def __init__(self, master_meta, lane, y_start=-220, speed_multiplier=1.0):
        self.lane = lane # 0: left lane, 1: center lane, 2: right lane
        self.y = float(y_start)
        self.speed = float(random.uniform(4.0, 7.8) * speed_multiplier)
        self.master_meta = master_meta
        self.plate = master_meta['plate']
        self.truck_type = master_meta['truck_type']
        self.color = master_meta['color']
        self.img_crop = master_meta['crop'] # BGR real cropped photo

        # Initial width and height from crop
        ch, cw = self.img_crop.shape[:2]
        self.aspect_ratio = cw / float(max(1, ch))
        self.base_w = random.randint(120, 160)
        self.base_h = int(self.base_w / self.aspect_ratio)

    def update(self):
        self.y += self.speed
        return self.y < 790

    def get_bbox(self, frame_w=1280, frame_h=720):
        lane_centers = [340, 640, 940]
        base_x = lane_centers[self.lane]
        
        # Perspective scale (0.50 at horizon, 1.45 near camera)
        progress = max(0.0, min(1.0, (self.y + 180) / (frame_h + 180)))
        scale = 0.50 + progress * 0.95
        
        w = max(60, int(self.base_w * scale))
        h = max(60, int(self.base_h * scale))
        
        drift = (base_x - 640) * (scale - 0.50) * 0.35
        cx = int(base_x + drift)
        
        x1 = cx - w // 2
        y1 = int(self.y)
        x2 = x1 + w
        y2 = y1 + h
        return [x1, y1, x2, y2], scale


class SurveillanceSimulator:
    """
    Simulates a high-definition Indian National Highway CCTV surveillance camera feed.
    Renders realistic asphalt highways, overhead FASTag gantries, and renders REAL
    photographic commercial truck imagery onto the live stream.
    """
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.trucks = []
        self.last_spawn = time.time()
        self.camera_name = "CAM-01 [NH-44 HIGHWAY SURVEILLANCE]"
        
        self.master_dir = os.path.join(os.path.dirname(Config.SNAPSHOT_DIR), 'master_trucks')
        self.real_sprites_pool = []
        self._load_real_truck_masters()

    def _load_real_truck_masters(self):
        """Loads and extracts real photographic truck crops from master images."""
        templates = [
            {'file': 'real_indian_tata_signa.jpg', 'truck_type': 'Tata Signa Goods Carrier', 'plate': 'TN38AB1234', 'color': 'Indian Red / Painted Art', 'bbox': [330, 275, 715, 835]},
            {'file': 'real_indian_ashok_leyland.jpg', 'truck_type': 'Ashok Leyland Captain Tipper', 'plate': 'KA01MJ9944', 'color': 'Blue / Yellow', 'bbox': [510, 395, 860, 875]},
            {'file': 'real_indian_fuel_tanker.jpg', 'truck_type': 'Bharat Petroleum Fuel Tanker', 'plate': 'MH12PK4321', 'color': 'Silver / Orange', 'bbox': [358, 355, 735, 915]},
            {'file': 'real_indian_bharatbenz_container.jpg', 'truck_type': 'BharatBenz Container Carrier', 'plate': 'DL01TX8822', 'color': 'White / Blue', 'bbox': [245, 260, 805, 865]},
            {'file': 'real_indian_goods_lorry.jpg', 'truck_type': 'Tata 1613 Goods Lorry', 'plate': 'GJ04BC5566', 'color': 'Multicolor Traditional', 'bbox': [250, 245, 705, 865]},
            {'file': 'real_container_scania.jpg', 'truck_type': 'Container Carrier', 'plate': 'TS08EE9911', 'color': 'Blue', 'bbox': [355, 68, 1070, 770]},
            {'file': 'real_tanker_shell.jpg', 'truck_type': 'Petroleum Tanker', 'plate': 'WB19GH2233', 'color': 'Silver / Green', 'bbox': [320, 275, 905, 895]},
            {'file': 'real_dump_scania.jpg', 'truck_type': 'Tipper / Dump Truck', 'plate': 'AP21XY9876', 'color': 'Orange / White', 'bbox': [315, 305, 720, 810]},
            {'file': 'real_flatbed_heavy.jpg', 'truck_type': 'Flatbed Hauler', 'plate': 'HR26BR4001', 'color': 'Black', 'bbox': [248, 335, 805, 875]},
            {'file': 'real_box_daf.jpg', 'truck_type': 'Refrigerated Carrier', 'plate': 'KL07QR3344', 'color': 'White', 'bbox': [308, 255, 665, 835]}
        ]

        for t in templates:
            p = os.path.join(self.master_dir, t['file'])
            if os.path.exists(p):
                img = cv2.imread(p)
                if img is not None:
                    bx1, by1, bx2, by2 = t['bbox']
                    # Safety bounds
                    ih, iw = img.shape[:2]
                    bx1 = max(0, min(iw - 10, bx1))
                    by1 = max(0, min(ih - 10, by1))
                    bx2 = max(bx1 + 10, min(iw, bx2))
                    by2 = max(by1 + 10, min(ih, by2))
                    crop = img[by1:by2, bx1:bx2].copy()
                    
                    self.real_sprites_pool.append({
                        'truck_type': t['truck_type'],
                        'plate': t['plate'],
                        'color': t['color'],
                        'crop': crop
                    })

    def step(self):
        now = time.time()
        if now - self.last_spawn > random.uniform(2.0, 3.5) and len(self.trucks) < 4:
            if self.real_sprites_pool:
                master = random.choice(self.real_sprites_pool)
                lane = random.choice([0, 1, 2])
                if not any(t.lane == lane and t.y < 120 for t in self.trucks):
                    speed_mult = 1.35 if random.random() < 0.25 else 1.0
                    self.trucks.append(RealTruckSprite(master, lane=lane, y_start=-200, speed_multiplier=speed_mult))
                    self.last_spawn = now

        self.trucks = [t for t in self.trucks if t.update()]
        frame = self._render_scene()
        detections = []

        for t in self.trucks:
            bbox, scale = t.get_bbox(self.width, self.height)
            if bbox[3] > 0 and bbox[1] < self.height:
                self._draw_real_truck(frame, bbox, t, scale)
                if bbox[1] > 20 and bbox[3] < self.height + 60:
                    detections.append({
                        'bbox': bbox,
                        'confidence': round(0.94 + random.uniform(0.01, 0.05), 2),
                        'class_id': 7,
                        'label': 'truck',
                        '_ground_truth_plate': t.plate,
                        '_ground_truth_type': t.truck_type
                    })

        self._draw_cctv_hud(frame)
        return frame, detections

    def _render_scene(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Horizon & Sky
        frame[0:220, :] = [45, 42, 38]
        
        # Asphalt Multi-Lane Highway
        pts_road = np.array([[120, 720], [1160, 720], [860, 220], [420, 220]], np.int32)
        cv2.fillPoly(frame, [pts_road], (48, 50, 52))
        
        # Shoulders / Greenery
        pts_left_shoulder = np.array([[0, 720], [120, 720], [420, 220], [280, 220]], np.int32)
        pts_right_shoulder = np.array([[1160, 720], [1280, 720], [1000, 220], [860, 220]], np.int32)
        cv2.fillPoly(frame, [pts_left_shoulder], (32, 58, 32))
        cv2.fillPoly(frame, [pts_right_shoulder], (32, 58, 32))
        
        # Moving Lane Dividers
        t_offset = int((time.time() * 60) % 80)
        self._draw_dashed_lane(frame, (420 + (860-420)/3, 220), (120 + (1160-120)/3, 720), t_offset)
        self._draw_dashed_lane(frame, (420 + 2*(860-420)/3, 220), (120 + 2*(1160-120)/3, 720), t_offset)
        
        # Overhead FASTag Gantry Frame
        cv2.line(frame, (60, 210), (1220, 210), (120, 130, 140), 6)
        cv2.line(frame, (60, 210), (60, 480), (100, 110, 120), 8)
        cv2.line(frame, (1220, 210), (1220, 480), (100, 110, 120), 8)
        
        # FASTag Speed Trap Detection Zone
        cv2.line(frame, (280, 360), (1000, 360), (0, 180, 255), 1)
        cv2.line(frame, (200, 520), (1080, 520), (0, 220, 100), 1)
        cv2.putText(frame, "FASTAG SPEED TRAP ZONE [CALIBRATED: 25.0m]", (210, 510), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 100), 1)

        return frame

    def _draw_dashed_lane(self, frame, pt1, pt2, offset):
        x1, y1 = pt1
        x2, y2 = pt2
        num_segments = 12
        for i in range(num_segments):
            frac1 = (i * 80 + offset) / 960.0
            frac2 = ((i + 0.5) * 80 + offset) / 960.0
            if 0.0 <= frac1 <= 1.0 and 0.0 <= frac2 <= 1.0:
                sx1 = int(x1 + (x2 - x1) * frac1)
                sy1 = int(y1 + (y2 - y1) * frac1)
                sx2 = int(x1 + (x2 - x1) * frac2)
                sy2 = int(y1 + (y2 - y1) * frac2)
                thickness = max(2, int(2 + frac1 * 4))
                cv2.line(frame, (sx1, sy1), (sx2, sy2), (235, 235, 235), thickness)

    def _draw_real_truck(self, frame, bbox, truck, scale):
        """Blends the real photographic truck crop onto the highway scene."""
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        if w <= 10 or h <= 10:
            return

        # Shadow beneath truck
        cv2.ellipse(frame, ((x1 + x2)//2, min(self.height - 5, y2)), (w//2 + 10, max(6, int(16 * scale))), 0, 0, 360, (18, 18, 18), -1)

        # Resize real photo crop
        resized_crop = cv2.resize(truck.img_crop, (w, h), interpolation=cv2.INTER_AREA)

        # Clipping bounds
        target_x1 = max(0, x1)
        target_y1 = max(0, y1)
        target_x2 = min(self.width, x2)
        target_y2 = min(self.height, y2)

        crop_x1 = target_x1 - x1
        crop_y1 = target_y1 - y1
        crop_x2 = crop_x1 + (target_x2 - target_x1)
        crop_y2 = crop_y1 + (target_y2 - target_y1)

        if target_x2 > target_x1 and target_y2 > target_y1:
            frame[target_y1:target_y2, target_x1:target_x2] = resized_crop[crop_y1:crop_y2, crop_x1:crop_x2]

    def _draw_cctv_hud(self, frame):
        cv2.rectangle(frame, (0, 0), (self.width, 38), (15, 18, 24), -1)
        cv2.line(frame, (0, 38), (self.width, 38), (0, 242, 254), 1)
        
        now_dt = datetime.now(timezone.utc)
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(frame, (25, 19), 6, (0, 0, 255), -1)
        cv2.putText(frame, "LIVE REC", (38, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1)
        cv2.putText(frame, self.camera_name, (140, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 242, 254), 1)
        time_str = now_dt.strftime("%Y-%m-%d  %H:%M:%S.%f")[:-4] + " IST"
        cv2.putText(frame, time_str, (self.width - 290, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
