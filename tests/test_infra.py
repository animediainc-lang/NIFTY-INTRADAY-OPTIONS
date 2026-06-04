import unittest
import os
from pathlib import Path
from core.config_loader import Config, get_config
from utils.logger import setup_logger

class TestInfrastructure(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        # Create a temp config file for testing
        self.test_config_path = self.project_root / "config" / "test_config.yml"
        with open(self.test_config_path, 'w') as f:
            f.write("test_key: test_value\nnested:\n  key: nested_value")

        self.test_log_file = self.project_root / "logs" / "test_bot.log"
        if self.test_log_file.exists():
            self.test_log_file.unlink()

        # Reset singleton state
        Config().reset()

    def tearDown(self):
        if self.test_config_path.exists():
            self.test_config_path.unlink()
        if self.test_log_file.exists():
            # Close handlers before removing file
            logger = setup_logger('test_logger', self.test_log_file)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            self.test_log_file.unlink()

    def test_config_loading(self):
        config = Config()
        config.load_config(self.test_config_path)
        self.assertEqual(config.get("test_key"), "test_value")
        self.assertEqual(config.get("nested.key"), "nested_value")
        self.assertEqual(config.get("non_existent", "default"), "default")

    def test_config_missing_file(self):
        config = Config()
        with self.assertRaises(FileNotFoundError):
            config.load_config("non_existent_path.yml")

    def test_logger_creation(self):
        logger = setup_logger('test_logger', self.test_log_file)
        logger.info("Test log message")

        # Check if log file is created
        self.assertTrue(self.test_log_file.exists())

        # Check if message is in the file
        with open(self.test_log_file, 'r') as f:
            content = f.read()
            self.assertIn("Test log message", content)

if __name__ == '__main__':
    unittest.main()
