import os
import unittest
from backend.app import create_app
from backend.config import Config

class TestImageDatabaseAndTraining(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_truck_logs_have_snapshots(self):
        res = self.client.get('/api/trucks/logs?page=1&limit=10')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(data['total'], 0)
        logs = data['logs']
        self.assertTrue(len(logs) > 0)
        # Check that snapshots exist
        first_snap = logs[0].get('snapshot_path')
        self.assertIsNotNone(first_snap)
        self.assertTrue(first_snap.endswith('.jpg'))

        # Test snapshot image retrieval
        snap_res = self.client.get(f'/api/trucks/snapshots/{first_snap}')
        self.assertEqual(snap_res.status_code, 200)
        self.assertEqual(snap_res.content_type, 'image/jpeg')
        self.assertGreater(len(snap_res.data), 1000)

    def test_dataset_stats_and_gallery(self):
        stats_res = self.client.get('/api/dataset/stats')
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.get_json()
        self.assertGreaterEqual(stats['total_images'], 100)
        self.assertGreaterEqual(stats['total_plate_crops'], 100)
        self.assertGreaterEqual(stats['annotated_ratio'], 0)

        gal_res = self.client.get('/api/dataset/gallery?page=1&limit=6')
        self.assertEqual(gal_res.status_code, 200)
        gal = gal_res.get_json()
        self.assertEqual(len(gal['images']), 6)
        self.assertIn('snapshot_url', gal['images'][0])

    def test_training_and_export(self):
        # Trigger training simulation
        train_res = self.client.post('/api/dataset/train', json={
            'model_type': 'YOLOv26-Truck',
            'epochs': 5,
            'batch_size': 16,
            'learning_rate': 0.001
        })
        self.assertEqual(train_res.status_code, 200)

        status_res = self.client.get('/api/dataset/training_status')
        self.assertEqual(status_res.status_code, 200)
        status = status_res.get_json()
        self.assertIn('status', status)

        # Test dataset export ZIP
        export_res = self.client.get('/api/dataset/export')
        self.assertEqual(export_res.status_code, 200)
        self.assertEqual(export_res.content_type, 'application/zip')
        self.assertGreater(len(export_res.data), 1000)

if __name__ == '__main__':
    unittest.main()
