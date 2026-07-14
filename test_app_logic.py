import os
import shutil
import unittest
import tempfile
from app import PythonAPI, get_config_path

class TestPythonAPILogic(unittest.TestCase):
    def setUp(self):
        # Initialize API
        self.api = PythonAPI()
        # Backup existing configurations
        self.orig_settings = self.api.settings.copy()
        self.orig_history = self.api.history.copy()
        
        # Setup temporary directories for tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Clear for test
        self.api.settings = {}
        self.api.history = []
        self.api._save_settings()
        self.api._save_history()

    def tearDown(self):
        # Restore configuration files
        self.api.settings = self.orig_settings
        self.api.history = self.orig_history
        self.api._save_settings()
        self.api._save_history()
        
        # Cleanup temporary test files
        shutil.rmtree(self.temp_dir)

    def test_settings_persistence(self):
        test_settings = {
            "use_llm": True,
            "api_key": "sk-test-12345",
            "api_base": "https://api.openai.com/v1",
            "llm_model": "gpt-4o",
            "llm_prompt": "Test Prompt"
        }
        res = self.api.save_settings(test_settings)
        self.assertTrue(res["success"])
        
        # Load and verify settings
        loaded_settings = self.api.get_settings()
        self.assertEqual(loaded_settings["api_key"], "sk-test-12345")
        self.assertTrue(loaded_settings["use_llm"])
        self.assertEqual(loaded_settings["llm_model"], "gpt-4o")

    def test_file_conversion_and_history(self):
        # Create a sample text file
        sample_path = os.path.join(self.temp_dir, "test_doc.txt")
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write("# Document Header\nThis is a sample document.")
            
        # Run conversion
        res = self.api.convert_file(sample_path, self.temp_dir)
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["output_path"]))
        self.assertEqual(res["output_name"], "test_doc.md")
        
        # Verify markdown content
        with open(res["output_path"], "r", encoding="utf-8") as f:
            md_content = f.read()
        self.assertIn("Document Header", md_content)
        self.assertIn("This is a sample document.", md_content)
        
        # Verify history logs
        history = self.api.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["source_name"], "test_doc.txt")
        self.assertEqual(history[0]["output_name"], "test_doc.md")
        self.assertEqual(history[0]["status"], "success")
        
        # Test read_text_file
        read_content = self.api.read_text_file(res["output_path"])
        self.assertEqual(read_content, md_content)
        
        # Test clearing history
        clear_res = self.api.clear_history()
        self.assertTrue(clear_res["success"])
        self.assertEqual(len(self.api.get_history()), 0)

if __name__ == '__main__':
    unittest.main()
