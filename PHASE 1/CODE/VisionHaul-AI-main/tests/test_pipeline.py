import unittest
import numpy as np
import time
from backend.ai_engine.tracker import ByteTracker, STrack
from backend.ai_engine.speed_estimator import SpeedEstimator
from backend.ai_engine.plate_ocr import LicensePlateOCR
from backend.ai_engine.vit_classifier import MTLViTClassifier
from backend.services.alert_manager import AlertManager
from backend.services.logistics import LogisticsService
from backend.database.models import Base, TruckLog, AlertLog, Blocklist
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestAIPipeline(unittest.TestCase):
    def setUp(self):
        # Create in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_byte_tracker_persistence(self):
        tracker = ByteTracker()
        # Frame 1 detection
        dets_f1 = [{'bbox': [100, 100, 200, 300], 'confidence': 0.95, 'class_id': 7}]
        tracks_f1 = tracker.update(dets_f1)
        self.assertEqual(len(tracks_f1), 1)
        track_id = tracks_f1[0].track_id
        self.assertTrue(track_id.startswith('TRK'))

        # Frame 2 slightly displaced detection
        dets_f2 = [{'bbox': [102, 115, 202, 315], 'confidence': 0.94, 'class_id': 7}]
        tracks_f2 = tracker.update(dets_f2)
        self.assertEqual(len(tracks_f2), 1)
        # Should maintain same persistent Track ID
        self.assertEqual(tracks_f2[0].track_id, track_id)

    def test_speed_estimator_overspeed(self):
        speed_est = SpeedEstimator(pixels_per_meter=18.5, fps=25, speed_limit=60.0)
        track = STrack([100, 100, 200, 300], 0.9)
        
        # Add high displacement trajectory
        t0 = time.time()
        track.history.append((150, 150, t0))
        track.history.append((150, 250, t0 + 0.1))
        track.history.append((150, 350, t0 + 0.2))
        track.history.append((150, 480, t0 + 0.3))

        speed, is_over = speed_est.estimate_speed(track)
        self.assertGreater(speed, 0)
        self.assertIsInstance(is_over, bool)

    def test_license_plate_ocr_and_blocklist(self):
        ocr = LicensePlateOCR()
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        plate_text, conf, is_real, plate_crop = ocr.extract_plate(frame, [100, 100, 250, 350], 'TRK001')
        
        self.assertIsNotNone(plate_text)
        self.assertGreater(conf, 0.8)

        # Seed a blocklist plate
        self.db.add(Blocklist(license_plate='TN38AB1234', reason='Stolen Vehicle', severity='CRITICAL', active=True))
        self.db.commit()

        is_blocked, reason, severity = ocr.check_blocklist('TN38AB1234', self.db, Blocklist)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, 'Stolen Vehicle')

        is_blocked_clean, _, _ = ocr.check_blocklist('TN09AZ7788', self.db, Blocklist)
        self.assertFalse(is_blocked_clean)

    def test_mtl_vit_classifier(self):
        vit = MTLViTClassifier()
        crop = np.full((150, 100, 3), 200, dtype=np.uint8)
        result = vit.classify(crop, 'TRK005')
        
        self.assertIn('truck_type', result)
        self.assertIn('color', result)
        self.assertIn('cargo_attributes', result)
        self.assertIn(result['truck_type'], vit.truck_types)
        self.assertIn(result['color'], vit.colors)

    def test_alert_manager_and_logistics(self):
        manager = AlertManager()
        alert = manager.trigger_alert(
            alert_type='OVERSPEED',
            track_id='TRK001',
            license_plate='TN38AB1234',
            speed=74.2,
            message='Overspeed detected',
            severity='HIGH',
            db_session=self.db
        )
        self.assertIsNotNone(alert)
        self.assertEqual(alert['license_plate'], 'TN38AB1234')

        # Test Logistics visit increment
        logistics = LogisticsService()
        log1 = logistics.record_truck_event(
            track_id='TRK001', license_plate='KA05CD4433', speed=55.0,
            speed_limit=60.0, is_overspeed=False, truck_type='Flatbed',
            color='Blue', cargo_attributes='Empty Bed', db_session=self.db
        )
        self.assertEqual(log1['visit_count'], 1)

        log2 = logistics.record_truck_event(
            track_id='TRK002', license_plate='KA05CD4433', speed=58.0,
            speed_limit=60.0, is_overspeed=False, truck_type='Flatbed',
            color='Blue', cargo_attributes='Loaded', db_session=self.db
        )
        self.assertEqual(log2['visit_count'], 2)

if __name__ == '__main__':
    unittest.main()
