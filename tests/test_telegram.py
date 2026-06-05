import unittest
from unittest.mock import patch, MagicMock
from telegram.telegram_notifier import TelegramNotifier

class TestTelegram(unittest.TestCase):
    def setUp(self):
        self.notifier = TelegramNotifier()

    @patch('requests.post')
    @patch('app_config.config_loader.config.get')
    def test_send_message(self, mock_get, mock_post):
        mock_get.side_effect = lambda key, default=None: "TEST_TOKEN" if "token" in key else "TEST_CHAT"
        mock_post.return_value.status_code = 200

        self.notifier.send_message("Test Message")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("TEST_TOKEN", args[0])
        self.assertEqual(kwargs['json']['text'], "Test Message")

    @patch('requests.post')
    @patch('app_config.config_loader.config.get')
    def test_notify_trade_entry(self, mock_get, mock_post):
        mock_get.side_effect = lambda key, default=None: "TOKEN" if "token" in key else "CHAT"
        mock_post.return_value.status_code = 200

        trade = {"symbol": "NIFTY", "strategy": "Momentum", "entry_price": 19500, "quantity": 50, "stop_loss": 19450}
        self.notifier.notify_trade_entry(trade)

        self.assertTrue(mock_post.called)
        self.assertIn("NIFTY", mock_post.call_args.kwargs['json']['text'])

if __name__ == "__main__":
    unittest.main()
