import os
import json
import shutil
import unittest
import tempfile
from app import app, load_settings, save_settings, load_history, save_history

class TestMarkItDownStudioAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Backup existing configurations
        self.orig_settings = load_settings()
        self.orig_history = load_history()
        
        # Setup temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Clear for clean test state
        save_settings({})
        save_history([])

    def tearDown(self):
        # Restore original configurations
        save_settings(self.orig_settings)
        save_history(self.orig_history)
        
        # Cleanup temporary test files
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_settings_persistence(self):
        test_settings = {
            "use_llm": True,
            "api_key": "sk-test-12345",
            "api_base": "https://api.openai.com/v1",
            "llm_model": "gpt-4o",
            "llm_prompt": "Test Prompt"
        }
        res = self.client.post('/api/settings', 
                               data=json.dumps(test_settings),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])
        
        # Load and verify settings
        res_get = self.client.get('/api/settings')
        loaded = res_get.get_json()
        self.assertEqual(loaded.get("api_key"), "sk-test-12345")
        self.assertTrue(loaded.get("use_llm"))
        self.assertEqual(loaded.get("llm_model"), "gpt-4o")

    def test_file_conversion_and_history(self):
        # Create a sample text file
        sample_path = os.path.join(self.temp_dir, "test_doc.txt")
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write("# Document Header\nThis is a sample document for conversion testing.")
            
        # Run conversion via API
        res = self.client.post('/api/convert_file',
                               data=json.dumps({"file_path": sample_path}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()
        self.assertTrue(res_data["success"])
        output_path = res_data["output_path"]
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(res_data["output_name"].endswith(".md"))
        
        # Verify markdown content
        with open(output_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        self.assertIn("Document Header", md_content)
        self.assertIn("This is a sample document", md_content)
        
        # Verify history logs
        res_history = self.client.get('/api/history')
        history = res_history.get_json()
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["source_name"], "test_doc.txt")
        self.assertEqual(history[0]["status"], "success")
        
        # Test read_text_file API
        res_read = self.client.post('/api/read_text_file',
                                    data=json.dumps({"file_path": output_path}),
                                    content_type='application/json')
        self.assertEqual(res_read.status_code, 200)
        self.assertEqual(res_read.get_data(as_text=True), md_content)
        
        # Test clearing history
        res_clear = self.client.post('/api/clear_history')
        self.assertTrue(res_clear.get_json()["success"])
        res_history_cleared = self.client.get('/api/history')
        self.assertEqual(len(res_history_cleared.get_json()), 0)

        # Cleanup generated markdown in downloads directory if created
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass

if __name__ == '__main__':
    unittest.main()
