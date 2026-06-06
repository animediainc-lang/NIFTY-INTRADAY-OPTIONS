import os
import unittest
from app_config.config_loader import Config
import logging

class TestFoundation(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        # Create a temporary config file for testing
        self.test_config_path = "app_config/test_config.yaml"
        with open(self.test_config_path, 'w') as f:
            f.write("""
test:
  key: "value"
  int_val: 123
  bool_val: true
""")
        self.config.load_config(self.test_config_path)

    def tearDown(self):
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def test_config_loading(self):
        self.assertEqual(self.config.get("test.key"), "value")
        self.assertEqual(self.config.get("test.int_val"), 123)
        self.assertEqual(self.config.get("test.bool_val"), True)

    def test_config_env_override(self):
        os.environ["BOT_TEST_KEY"] = "overridden"
        self.config.load_config(self.test_config_path)
        self.assertEqual(self.config.get("test.key"), "overridden")
        del os.environ["BOT_TEST_KEY"]

    def test_config_default_value(self):
        self.assertEqual(self.config.get("non_existent", "default"), "default")

    def test_logger_creation(self):
        from logger import setup_logger
        test_logger = setup_logger("test_logger", "logs/test.log")
        self.assertIsInstance(test_logger, logging.Logger)
        self.assertTrue(os.path.exists("logs/test.log"))

if __name__ == "__main__":
    unittest.main()
