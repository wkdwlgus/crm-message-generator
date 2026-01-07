import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# backend 폴더를 path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.crm_history_service import CRMHistoryService

class TestCRMHistoryService(unittest.TestCase):
    def setUp(self):
        # Mock Supabase Client
        self.mock_sb = MagicMock()
        
        # Patch create_client to return our mock
        patcher = patch('services.crm_history_service.create_client', return_value=self.mock_sb)
        self.mock_create_client = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.service = CRMHistoryService()
        # Ensure the service uses our mock sb
        self.service.sb = self.mock_sb

    def test_generate_signature_consistency(self):
        """Test if signature is consistent for same inputs"""
        params = {
            "brand": "Hera",
            "persona": "Trend Setter",
            "intent": "regular", # [NEW] intent type
            "weather": None,     # [NEW] weather is None for regular
            "beauty_profile": {
                "skin_type": ["Dry", "Sensitive"],
                "skin_concerns": ["Wrinkle"],
                "keywords": ["Anti-aging"],
                "preferred_tone": "Warm",
                "age_group": "30s",
                "gender": "F"
            }
        }
        
        sig1 = self.service._generate_signature(**params)
        sig2 = self.service._generate_signature(**params)
        
        self.assertEqual(sig1, sig2)
        
    def test_generate_signature_sensitivity(self):
        """Test if signature changes when critical param changes"""
        base_params = {
            "brand": "Hera",
            "persona": "Trend Setter",
            "intent": "weather",
            "weather": "Rainy",
            "beauty_profile": {"skin_type": ["Dry"]}
        }
        
        sig_base = self.service._generate_signature(**base_params)
        
        # Change weather
        params_weather = base_params.copy()
        params_weather["weather"] = "Sunny"
        sig_weather = self.service._generate_signature(**params_weather)
        
        self.assertNotEqual(sig_base, sig_weather)
        
    def test_find_message_hit(self):
        """Test find_message returns content when hit"""
        # Mock DB response
        mock_resp = MagicMock()
        mock_resp.data = [{"message_content": "Cached Message"}]
        
        # Mock chain: table -> select -> eq -> limit -> execute
        self.mock_sb.table.return_value \
            .select.return_value \
            .eq.return_value \
            .limit.return_value \
            .execute.return_value = mock_resp
            
        result = self.service.find_message("Brand", "Persona", "Intent", "Weather", {})
        self.assertEqual(result, "Cached Message")

    def test_save_message(self):
        """Test save_message calls insert"""
        self.service.save_message("Brand", "Persona", "Intent", "Weather", {}, "Content")
        
        # Verify insert called
        self.mock_sb.table.assert_called_with("crm_message_history")
        self.mock_sb.table().insert.assert_called()

if __name__ == '__main__':
    unittest.main()
