import os
import random
import cv2
import numpy as np
from datetime import datetime, timedelta, timezone

class ImageDatasetGenerator:
    """
    Generates high-definition REAL heavy vehicle CCTV surveillance snapshot images,
    cropped license plate evidence images, and YOLO bounding box annotation files (.txt).
    
    Includes genuine photographic Indian commercial heavy trucks (Tata Signa 10-Wheeler,
    Ashok Leyland Captain Tipper, Bharat Petroleum / IndianOil Fuel Tanker, BharatBenz Container Carrier,
    Tata 1613 Goods Carrier Lorry with All India Permit) alongside international heavy carriers.
    """
    def __init__(self, output_dir=None, master_dir=None):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        
        if output_dir is None:
            self.output_dir = os.path.join(base_dir, 'snapshots')
        else:
            self.output_dir = output_dir

        if master_dir is None:
            self.master_dir = os.path.join(base_dir, 'master_trucks')
        else:
            self.master_dir = master_dir

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.master_dir, exist_ok=True)

        self.width = 1280
        self.height = 720

        # Master Real Truck Definitions (Indian Commercial Trucks + Global SOTA Fleets)
        self.real_truck_templates = [
            # 1. Indian Commercial Trucks
            {
                'file': 'real_indian_tata_signa.jpg',
                'truck_type': 'Tata Signa Goods Carrier',
                'default_color': 'Indian Red / Painted Art',
                'cargo_default': 'Covered National Permit Freight',
                'bbox': [330, 275, 715, 835], # [x1, y1, x2, y2]
                'plate_pos': [392, 742, 38, 16],
                'camera_default': 'CAM-01 [NH-44 HIGHWAY SURVEILLANCE]'
            },
            {
                'file': 'real_indian_ashok_leyland.jpg',
                'truck_type': 'Ashok Leyland Captain Tipper',
                'default_color': 'Blue / Yellow',
                'cargo_default': 'Aggregate Stone Gravel Freight',
                'bbox': [510, 395, 860, 875],
                'plate_pos': [582, 788, 30, 14],
                'camera_default': 'CAM-07 [NAVAYUGA TOLL PLAZA FASTAG]'
            },
            {
                'file': 'real_indian_fuel_tanker.jpg',
                'truck_type': 'Bharat Petroleum Fuel Tanker',
                'default_color': 'Silver / Orange',
                'cargo_default': 'Inflammable Petroleum (Class 3 Hazmat)',
                'bbox': [358, 355, 735, 915],
                'plate_pos': [588, 838, 32, 14],
                'camera_default': 'CAM-07 [NH-48 EXPRESSWAY GANTRY]'
            },
            {
                'file': 'real_indian_bharatbenz_container.jpg',
                'truck_type': 'BharatBenz Container Carrier',
                'default_color': 'White / Blue',
                'cargo_default': 'Sealed Maersk ISO 40ft Container',
                'bbox': [245, 260, 805, 865],
                'plate_pos': [290, 755, 24, 12],
                'camera_default': 'CAM-07 [NH-48 KM 45.2 SPEED RADAR]'
            },
            {
                'file': 'real_indian_goods_lorry.jpg',
                'truck_type': 'Tata 1613 Goods Lorry',
                'default_color': 'Multicolor Traditional Woodwork',
                'cargo_default': 'All India Permit Tarp-Sealed Cargo',
                'bbox': [250, 245, 705, 865],
                'plate_pos': [505, 792, 34, 14],
                'camera_default': 'CAM-0947 [NH-44 CORRIDOR SURVEILLANCE]'
            },
            # 2. Additional Heavy Commercial Vehicles
            {
                'file': 'real_container_scania.jpg',
                'truck_type': 'Container Carrier',
                'default_color': 'Blue',
                'cargo_default': 'Sealed ISO Shipping Container',
                'bbox': [355, 68, 1070, 770],
                'plate_pos': [905, 705, 78, 22],
                'camera_default': 'CAM-04 [HWY-NORTH 1A]'
            },
            {
                'file': 'real_tanker_shell.jpg',
                'truck_type': 'Petroleum Tanker',
                'default_color': 'Silver / Green',
                'cargo_default': 'Bulk Liquid Aviation Fuel',
                'bbox': [320, 275, 905, 895],
                'plate_pos': [790, 785, 58, 18],
                'camera_default': 'CAM-14 [TOLL-LANE 5]'
            },
            {
                'file': 'real_dump_scania.jpg',
                'truck_type': 'Tipper / Dump Truck',
                'default_color': 'Orange / White',
                'cargo_default': 'Loaded Aggregate Gravel Freight',
                'bbox': [315, 305, 720, 810],
                'plate_pos': [368, 715, 48, 16],
                'camera_default': 'CAM-04 [EXPRESSWAY SERVICE]'
            },
            {
                'file': 'real_mixer_aura.jpg',
                'truck_type': 'Concrete Mixer',
                'default_color': 'Yellow / Gold',
                'cargo_default': 'Rotary Ready-Mix Concrete',
                'bbox': [345, 255, 830, 880],
                'plate_pos': [785, 728, 38, 18],
                'camera_default': 'CAM-02 [HWY-I95 NORTH]'
            },
            {
                'file': 'real_flatbed_heavy.jpg',
                'truck_type': 'Flatbed Hauler',
                'default_color': 'Black',
                'cargo_default': 'Industrial Heavy Machinery Crates',
                'bbox': [248, 335, 805, 875],
                'plate_pos': [730, 818, 26, 14],
                'camera_default': 'CAM-07 [I-15 NB MP114]'
            },
            {
                'file': 'real_box_daf.jpg',
                'truck_type': 'Refrigerated Carrier',
                'default_color': 'White',
                'cargo_default': 'Refrigerated Fresh Produce',
                'bbox': [308, 255, 665, 835],
                'plate_pos': [558, 788, 42, 14],
                'camera_default': 'CAM-08 [HIGHWAY EXIT 142]'
            },
            {
                'file': 'real_night_ir_mack.jpg',
                'truck_type': 'Container Carrier',
                'default_color': 'Night Monochrome',
                'cargo_default': 'Sealed Freight Container (Night Transit)',
                'bbox': [180, 275, 780, 755],
                'plate_pos': [745, 690, 24, 12],
                'camera_default': 'CAM-428 [HWY 95S IR-NIGHT]'
            },
            {
                'file': 'real_dusk_volvo.jpg',
                'truck_type': 'Container Carrier',
                'default_color': 'Deep Blue',
                'cargo_default': 'Sealed ISO Shipping Container',
                'bbox': [405, 395, 740, 765],
                'plate_pos': [435, 728, 24, 10],
                'camera_default': 'CAM-08 [DUSK GATEWAY E42]'
            }
        ]

        self.state_codes = ['TN', 'KA', 'MH', 'DL', 'GJ', 'TS', 'HR', 'AP', 'WB', 'UP', 'RJ', 'KL']
        self.preset_blocklisted = ['TN38AB1234', 'KA01MJ9944', 'MH12PK4321', 'DL01TX8822', 'GJ04BC5566']
        self.cameras = [
            'CAM-01 [NH-44 NORTH GATE]',
            'CAM-02 [NH-48 FASTAG PLAZA]',
            'CAM-03 [PORT-TERMINAL-GATE-4]',
            'CAM-04 [EXPRESSWAY SPEED RADAR]'
        ]

    def generate_plate_number(self):
        st = random.choice(self.state_codes)
        dist = f"{random.randint(1, 99):02d}"
        series = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
        num = f"{random.randint(1000, 9999)}"
        return f"{st}{dist}{series}{num}"

    def process_real_truck_frame(self, template, vehicle_meta, index=1):
        """
        Loads the real photographic truck image and renders dynamic CCTV metadata,
        IND license plate mount, telemetry radar watermark, and AI bounding box.
        """
        master_path = os.path.join(self.master_dir, template['file'])
        if not os.path.exists(master_path):
            return None, None, None

        img = cv2.imread(master_path)
        if img is None:
            return None, None, None

        orig_h, orig_w = img.shape[:2]
        
        # Scale to standard 1280x720 CCTV dimensions
        frame = cv2.resize(img, (self.width, self.height), interpolation=cv2.INTER_AREA)

        scale_x = self.width / float(orig_w)
        scale_y = self.height / float(orig_h)

        # Scale base bbox
        bx1, by1, bx2, by2 = template['bbox']
        x1 = int(bx1 * scale_x)
        y1 = int(by1 * scale_y)
        x2 = int(bx2 * scale_x)
        y2 = int(by2 * scale_y)

        # Slight photographic augmentation for distinct dataset instances (lighting, contrast, grain)
        lighting = vehicle_meta.get('lighting', 'DAYLIGHT')
        if lighting == 'DUSK_GOLDEN':
            # Warm golden dusk tint
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_AUTUMN)
            frame = cv2.addWeighted(frame, 0.22, cv2.resize(img, (self.width, self.height)), 0.78, 0)
        elif lighting == 'NIGHT_CCTV_IR':
            # Infrared monochrome CCTV night mode
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            # Add slight CCTV sensor noise
            noise = np.random.normal(0, 4, frame.shape).astype(np.uint8)
            frame = cv2.add(frame, noise)
        elif lighting == 'RAIN_OVERCAST':
            # Cool overcast tone
            frame = cv2.convertScaleAbs(frame, alpha=0.92, beta=-8)

        plate_text = vehicle_meta['license_plate']
        speed = vehicle_meta['speed']
        is_overspeed = vehicle_meta['is_overspeed']
        is_blocked = vehicle_meta['is_blocklisted']
        cam_id = vehicle_meta['camera_id']
        timestamp = vehicle_meta['timestamp']

        # Embed Realistic IND Commercial License Plate on Truck Front Bumper
        px, py, pw, ph = template['plate_pos']
        spx = int(px * scale_x)
        spy = int(py * scale_y)
        spw = max(44, int(pw * scale_x))
        sph = max(14, int(ph * scale_y))

        # Render Plate Mount on Bumper
        if spy + sph < self.height and spx + spw < self.width:
            cv2.rectangle(frame, (spx - 2, spy - 2), (spx + spw + 2, spy + sph + 2), (10, 10, 10), -1)
            cv2.rectangle(frame, (spx, spy), (spx + spw, spy + sph), (245, 245, 245), -1)
            # Blue IND Badge
            ind_w = max(6, spw // 5)
            cv2.rectangle(frame, (spx, spy), (spx + ind_w, spy + sph), (200, 100, 0), -1)
            cv2.putText(frame, plate_text, (spx + ind_w + 3, spy + sph - 3), cv2.FONT_HERSHEY_SIMPLEX, max(0.24, sph * 0.024), (10, 10, 10), 1)

        # Generate High-Resolution Cropped License Plate Image (160x48) for Dossier Evidence
        crop_pw, crop_ph = 160, 48
        plate_crop = np.full((crop_ph, crop_pw, 3), 245, dtype=np.uint8)
        cv2.rectangle(plate_crop, (0, 0), (crop_pw-1, crop_ph-1), (20, 20, 20), 2)
        cv2.rectangle(plate_crop, (2, 2), (24, crop_ph-3), (200, 100, 0), -1)
        cv2.putText(plate_crop, "IND", (4, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
        cv2.putText(plate_crop, plate_text, (32, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (10, 10, 10), 2)

        # Render Real CCTV HUD Telemetry Overlay on Frame
        # Top-Left Camera Header
        cv2.rectangle(frame, (20, 20), (480, 75), (10, 15, 25), -1)
        cv2.rectangle(frame, (20, 20), (480, 75), (56, 189, 248), 1)
        cv2.putText(frame, f"[● REC] {cam_id}", (32, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 242, 254), 1)
        cv2.putText(frame, f"TIME: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} IST | 1280x720 HD CCTV", (32, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (148, 163, 184), 1)

        # Top-Right Telemetry Badge
        cv2.rectangle(frame, (self.width - 320, 20), (self.width - 20, 75), (10, 15, 25), -1)
        cv2.rectangle(frame, (self.width - 320, 20), (self.width - 20, 75), (56, 189, 248), 1)
        sp_col = (0, 0, 255) if is_overspeed else (0, 255, 120)
        cv2.putText(frame, f"RADAR SPEED: {speed:.1f} KM/H", (self.width - 305, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, sp_col, 2)
        stat_text = "STATUS: OVERSPEED VIOLATION" if is_overspeed else ("STATUS: WATCHLIST HIT" if is_blocked else "STATUS: COMPLIANT")
        cv2.putText(frame, stat_text, (self.width - 305, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (240, 240, 240), 1)

        # AI Detection Bounding Box on Vehicle
        box_color = (0, 0, 255) if is_blocked else ((0, 140, 255) if is_overspeed else (0, 242, 254))
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        # Corner brackets
        c_len = 24
        # top-left
        cv2.line(frame, (x1, y1), (x1 + c_len, y1), box_color, 4)
        cv2.line(frame, (x1, y1), (x1, y1 + c_len), box_color, 4)
        # top-right
        cv2.line(frame, (x2, y1), (x2 - c_len, y1), box_color, 4)
        cv2.line(frame, (x2, y1), (x2, y1 + c_len), box_color, 4)
        # bottom-left
        cv2.line(frame, (x1, y2), (x1 + c_len, y2), box_color, 4)
        cv2.line(frame, (x1, y2), (x1, y2 - c_len), box_color, 4)
        # bottom-right
        cv2.line(frame, (x2, y2), (x2 - c_len, y2), box_color, 4)
        cv2.line(frame, (x2, y2), (x2, y2 - c_len), box_color, 4)

        # AI Tag Label Header above Bounding Box
        tag_bg_w = max(260, int((x2 - x1) * 0.7))
        cv2.rectangle(frame, (x1, max(0, y1 - 28)), (x1 + tag_bg_w, max(28, y1)), box_color, -1)
        cv2.putText(frame, f"TRK{index:03d} | {vehicle_meta['truck_type'][:16]} | {plate_text}", (x1 + 6, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (10, 10, 15), 2)

        return frame, [x1, y1, x2, y2], plate_crop

    def generate_dataset(self, target_count=180):
        """
        Generates `target_count` distinct REAL photographic heavy vehicle CCTV snapshots,
        plate crops, and YOLO label files (.txt).
        Returns a list of metadata records.
        """
        print(f"[DATASET] Generating {target_count} REAL High-Definition CCTV Indian & Global Heavy Vehicle Snapshot Records...")
        records = []
        now = datetime.now(timezone.utc)

        lighting_modes = ['DAYLIGHT', 'DAYLIGHT', 'DUSK_GOLDEN', 'NIGHT_CCTV_IR', 'RAIN_OVERCAST']

        for i in range(1, target_count + 1):
            template = self.real_truck_templates[(i - 1) % len(self.real_truck_templates)]
            lighting = random.choice(lighting_modes)
            cam_id = template.get('camera_default', random.choice(self.cameras))

            # 20% blocklisted, 25% overspeed
            is_blocked = (i % 6 == 0)
            if is_blocked:
                plate = random.choice(self.preset_blocklisted)
            else:
                plate = self.generate_plate_number()

            speed = round(random.gauss(55, 12), 1)
            speed = max(28.0, min(108.0, speed))
            is_overspeed = speed > 60.0

            days_ago = random.uniform(0, 30)
            timestamp = now - timedelta(days=days_ago, hours=random.uniform(0, 23), minutes=random.uniform(0, 59))

            track_id = f"TRK{i:03d}"
            base_filename = f"truck_{track_id}_{plate}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            img_filename = f"{base_filename}.jpg"
            plate_filename = f"{base_filename}_plate.jpg"
            label_filename = f"{base_filename}.txt"

            img_path = os.path.join(self.output_dir, img_filename)
            plate_path = os.path.join(self.output_dir, plate_filename)
            label_path = os.path.join(self.output_dir, label_filename)

            vehicle_meta = {
                'track_id': track_id,
                'license_plate': plate,
                'truck_type': template['truck_type'],
                'color': template['default_color'],
                'cargo_attributes': template['cargo_default'],
                'lighting': lighting,
                'speed': speed,
                'is_overspeed': is_overspeed,
                'is_blocklisted': is_blocked,
                'camera_id': cam_id,
                'timestamp': timestamp,
                'snapshot_filename': img_filename,
                'plate_filename': plate_filename
            }

            frame, bbox, plate_crop = self.process_real_truck_frame(template, vehicle_meta, index=i)
            if frame is None:
                continue

            # Save real vehicle snapshot & plate crop
            cv2.imwrite(img_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            cv2.imwrite(plate_path, plate_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

            # Write YOLO format label file (normalized x_center, y_center, width, height)
            # Class 0: truck
            x1, y1, x2, y2 = bbox
            dw = 1.0 / self.width
            dh = 1.0 / self.height
            x_center = ((x1 + x2) / 2.0) * dw
            y_center = ((y1 + y2) / 2.0) * dh
            bw = (x2 - x1) * dw
            bh = (y2 - y1) * dh

            with open(label_path, 'w', encoding='utf-8') as lf:
                lf.write(f"0 {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}\n")

            records.append({
                **vehicle_meta,
                'bbox': bbox,
                'img_path': img_path,
                'plate_path': plate_path,
                'label_path': label_path
            })

        print(f"[DATASET] Successfully generated {len(records)} REAL Indian & global vehicle CCTV snapshots and annotations in {self.output_dir}")
        return records

# Singleton instance
dataset_generator = ImageDatasetGenerator()
