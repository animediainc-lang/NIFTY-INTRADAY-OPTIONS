import unittest
import os
import sqlite3
from database.db_manager import DatabaseManager

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.test_db = "database/test_trading.db"
        self.db = DatabaseManager(db_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_log_trade(self):
        self.db.log_trade("NIFTY", "StrategyA", "BUY", 19500, 50, status="OPEN")

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, action, entry_price FROM trades")
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], "NIFTY")
        self.assertEqual(row[1], "BUY")
        self.assertEqual(row[2], 19500)

    def test_log_signal(self):
        self.db.log_signal("NIFTY", "StrategyA", "BUY", 19500, 85.5)

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT strategy, ai_score FROM signals")
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], "StrategyA")
        self.assertEqual(row[1], 85.5)

    def test_log_daily_metrics(self):
        metrics = {"pcr": 1.2, "vix": 15.5, "max_pain": 19500, "pdh": 19600, "pdl": 19400}
        self.db.log_daily_metrics(metrics)

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT pcr, vix FROM daily_metrics")
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], 1.2)
        self.assertEqual(row[1], 15.5)

if __name__ == "__main__":
    unittest.main()
