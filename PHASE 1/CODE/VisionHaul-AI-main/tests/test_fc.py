import unittest
from backend.app import create_app
from backend.services.fc_service import fc_service
from backend.database.db import SessionLocal
from backend.database.models import VehicleFCRegistry

class TestFCProcess(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_fc_verification_and_rules(self):
        """Test FC verification logic for over-aged vs renewal eligible vehicles."""
        # 1. Verify plate lookup
        res = fc_service.verify_fc_status('TN38AB1234', db_session=self.db)
        self.assertIn('fc_status', res)
        self.assertIn('vehicle_age_years', res)
        self.assertIn('police_action_required', res)

    def test_fc_renewal_process(self):
        """Test automated RTO multi-point diagnostic and FC renewal workflow."""
        test_plate = 'KA05CD7799'
        
        # Ensure record exists and is eligible for renewal (age < 15)
        record = self.db.query(VehicleFCRegistry).filter(
            VehicleFCRegistry.license_plate == test_plate
        ).first()
        if not record:
            record = fc_service._generate_default_fc_record(test_plate)
            record.vehicle_age_years = 7
            record.fc_status = 'EXPIRED_RENEWAL_REQUIRED'
            record.police_action_required = 'FC_RENEWAL_PROCESS'
            self.db.add(record)
            self.db.commit()
        else:
            record.vehicle_age_years = 7
            record.fc_status = 'EXPIRED_RENEWAL_REQUIRED'
            self.db.commit()

        # Execute renewal via service
        result = fc_service.process_fc_renewal(test_plate, test_metrics={
            'brake_efficiency': 92.5,
            'suspension_rating': 88.0,
            'structural_integrity': 95.0,
            'emission_level': 'BS-VI Pass (CO: 0.11%, HC: 38 ppm)'
        }, db_session=self.db)

        self.assertTrue(result['success'])
        self.assertEqual(result['record']['fc_status'], 'VALID')
        self.assertEqual(result['record']['police_action_required'], 'NONE')
        self.assertEqual(result['record']['fine_amount'], 0.0)
        self.assertIn('rto_cert_id', result['inspection_summary'])

    def test_fc_destruction_order_and_scrapping(self):
        """Test Police Destruction Order issuance and Certificate of Destruction (COD)."""
        import time
        scrap_plate = f"MH12SC{int(time.time()*1000)%90000+10000}"
        
        # Create over-aged vehicle record (18 years)
        record = fc_service._generate_default_fc_record(scrap_plate)
        record.vehicle_age_years = 18
        record.fc_status = 'DESTROY_VEHICLE_SCRAP'
        self.db.add(record)
        self.db.commit()

        # 1. Issue Destruction Order
        order_res = fc_service.issue_destruction_order(
            scrap_plate,
            reason='Exceeded 15-year statutory service life and failed emissions.',
            db_session=self.db
        )
        self.assertTrue(order_res['success'])
        self.assertEqual(order_res['record']['destruction_order_status'], 'ORDER_ISSUED')

        # 2. Confirm Physical Scrapping / Destruction at RVSF
        scrap_res = fc_service.confirm_scrapping_destruction(
            scrap_plate,
            scrapping_facility='RVSF National Heavy Vehicle Scrapping Facility #07',
            officer_badge='SEC-CMD-01',
            db_session=self.db
        )
        self.assertTrue(scrap_res['success'])
        self.assertEqual(scrap_res['record']['destruction_order_status'], 'DESTROYED')
        self.assertIn('certificate_number', scrap_res['certificate'])
        self.assertTrue(scrap_res['certificate']['certificate_number'].startswith('COD-IND-MORTH'))

    def test_fc_fine_payment(self):
        """Test payment of penalty challan for expired FC."""
        import time
        fine_plate = f"DL01FN{int(time.time()*1000)%90000+10000}"
        record = fc_service._generate_default_fc_record(fine_plate)
        record.fine_amount = 5000.0
        self.db.add(record)
        self.db.commit()

        pay_res = fc_service.pay_fc_fine(fine_plate, amount=5000.0, db_session=self.db)
        self.assertTrue(pay_res['success'])
        self.assertEqual(pay_res['record']['fine_amount'], 0.0)
        self.assertIn('receipt_number', pay_res)

    def test_fc_api_endpoints(self):
        """Test Flask REST API routes for FC workflow."""
        # 1. FC Records
        res = self.client.get('/api/fc/records?page=1&limit=5')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('records', data)
        self.assertIn('total', data)

        # 2. FC Stats
        res_stats = self.client.get('/api/fc/stats')
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()
        self.assertIn('compliance_rate', stats)
        self.assertIn('age_distribution', stats)

        # 3. Police Notice
        res_notice = self.client.get('/api/fc/police-notice/TN38AB1234')
        self.assertEqual(res_notice.status_code, 200)
        notice = res_notice.get_json()
        self.assertIn('notice_number', notice)
        self.assertIn('action_summary', notice)

        # 4. FC Renewal Endpoint
        res_renew = self.client.post('/api/fc/renew', json={
            'license_plate': 'KA05CD7799'
        })
        self.assertEqual(res_renew.status_code, 200)
        self.assertTrue(res_renew.get_json()['success'])

if __name__ == '__main__':
    unittest.main()
