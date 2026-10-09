import unittest
import json
from backend.app import create_app
from backend.database.db import SessionLocal
from backend.database.models import Base, Blocklist, TruckLog, SystemConfig

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_telemetry_endpoint(self):
        res = self.client.get('/api/stream/telemetry')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('fps', data)
        self.assertIn('active_tracks', data)

    def test_truck_logs_and_stats(self):
        res_logs = self.client.get('/api/trucks/logs?page=1&limit=5')
        self.assertEqual(res_logs.status_code, 200)
        data_logs = res_logs.get_json()
        self.assertIn('logs', data_logs)
        self.assertIn('total', data_logs)

        res_stats = self.client.get('/api/trucks/stats')
        self.assertEqual(res_stats.status_code, 200)
        data_stats = res_stats.get_json()
        self.assertIn('summary', data_stats)
        self.assertIn('daily_trends', data_stats)
        self.assertIn('type_distribution', data_stats)

    def test_alerts_endpoint(self):
        res = self.client.get('/api/alerts')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('alerts', data)

    def test_blocklist_crud(self):
        # 1. Add new blocklist entry
        res_add = self.client.post('/api/blocklist', json={
            'license_plate': 'TEST99ZZ1111',
            'reason': 'Test unauthorized vehicle',
            'severity': 'CRITICAL',
            'added_by': 'Test Inspector'
        })
        self.assertIn(res_add.status_code, [200, 201])
        entry_id = res_add.get_json()['entry']['id']

        # 2. Get blocklist
        res_get = self.client.get('/api/blocklist?search=TEST99ZZ')
        self.assertEqual(res_get.status_code, 200)
        self.assertTrue(any(b['license_plate'] == 'TEST99ZZ1111' for b in res_get.get_json()['blocklist']))

        # 3. Delete entry
        res_del = self.client.delete(f'/api/blocklist/{entry_id}')
        self.assertEqual(res_del.status_code, 200)

    def test_config_endpoints(self):
        res_cfg = self.client.get('/api/config')
        self.assertEqual(res_cfg.status_code, 200)
        data_cfg = res_cfg.get_json()
        self.assertIn('speed_limit', data_cfg)

        # Update speed limit
        res_update = self.client.post('/api/config', json={'speed_limit': 65.0})
        self.assertEqual(res_update.status_code, 200)

    def test_auth_login_endpoints(self):
        # 1. Admin login
        res_admin = self.client.post('/api/auth/login', json={
            'email': 'admin@visionhaul.ai',
            'password': 'admin'
        })
        self.assertEqual(res_admin.status_code, 200)
        data_admin = res_admin.get_json()
        self.assertTrue(data_admin['success'])
        self.assertEqual(data_admin['user']['role'], 'Admin')
        self.assertIn('token', data_admin)

        # 2. Manager login
        res_mgr = self.client.post('/api/auth/login', json={
            'email': 'manager@visionhaul.ai',
            'password': 'manager'
        })
        self.assertEqual(res_mgr.status_code, 200)
        data_mgr = res_mgr.get_json()
        self.assertTrue(data_mgr['success'])
        self.assertEqual(data_mgr['user']['role'], 'Manager')

        # 3. Invalid credentials check
        res_invalid = self.client.post('/api/auth/login', json={
            'email': 'admin@visionhaul.ai',
            'password': 'wrongpassword'
        })
        self.assertEqual(res_invalid.status_code, 401)

    def test_auth_register_endpoints(self):
        import time
        unique_email = f"officer_{int(time.time()*1000)}@defense.gov"
        # 1. Register new Admin profile
        res_reg = self.client.post('/api/auth/register', json={
            'name': 'Captain Robert Shaw',
            'email': unique_email,
            'password': 'secretpassword',
            'role': 'Admin',
            'department': 'Border Tactical Fleet Security'
        })
        self.assertEqual(res_reg.status_code, 201)
        data_reg = res_reg.get_json()
        self.assertTrue(data_reg['success'])
        self.assertEqual(data_reg['user']['role'], 'Admin')
        self.assertEqual(data_reg['user']['name'], 'Captain Robert Shaw')

        # 2. Login with the newly registered user
        res_login = self.client.post('/api/auth/login', json={
            'email': unique_email,
            'password': 'secretpassword'
        })
        self.assertEqual(res_login.status_code, 200)
        self.assertEqual(res_login.get_json()['user']['email'], unique_email)

        # 3. Duplicate email rejection
        res_dup = self.client.post('/api/auth/register', json={
            'name': 'Duplicate User',
            'email': unique_email,
            'password': 'password123',
            'role': 'Manager'
        })
        self.assertEqual(res_dup.status_code, 400)

if __name__ == '__main__':
    unittest.main()
