import sys
import time
import pandas as pd
from datetime import datetime
from logger import logger
from app_config.config_loader import ConfigLoader
from data.market_data_manager import MarketDataManager
from data.indicators import TechnicalIndicators
from intelligence.scanners import MarketScanner
from orchestration.consensus import MultiAgentDebateEngine
from risk.risk_manager import RiskEngine
from execution.broker_interface import UnifiedBrokerAdapter
from database.db_manager import DatabaseManager

def main():
    logger.info("=========================================================")
    logger.info("  Starting Multi-Agent Nifty Options Trading System (Paper) ")
    logger.info("=========================================================")

    config = ConfigLoader()
    environment = config.get("system.environment", "paper")
    logger.info(f"System Environment: {environment.upper()}")

    # Initialize components
    db = DatabaseManager()
    market_data = MarketDataManager()
    scanner = MarketScanner()
    debate_engine = MultiAgentDebateEngine()
    risk_engine = RiskEngine(initial_capital=config.get("trading.default_capital", 500000.0))
    broker = UnifiedBrokerAdapter(mode=environment)

    # Simulated Market Loop (Runs 3 iterations with market time 10:30 AM)
    dummy_prices = [24500.0, 24530.0, 24470.0]
    simulated_time = "10:30"

    for i, spot in enumerate(dummy_prices, 1):
        logger.info(f"\n--- Iteration {i} | Nifty Spot Price: ₹{spot} | Time: {simulated_time} ---")

        # 1. Check Risk Time Filters
        allowed, msg = risk_engine.is_trading_allowed(simulated_time)
        if not allowed:
            logger.warning(f"Trading blocked by Risk Engine: {msg}")
            continue

        # 2. Fetch/Simulate Market Data Snapshot
        option_chain = market_data.generate_option_chain(spot)
        pcr = market_data.calculate_pcr(option_chain.contracts)
        max_pain = market_data.calculate_max_pain(option_chain.contracts)
        unusual_events = scanner.scan_unusual_activity(option_chain)

        # Mock Candle DataFrame
        df_candles = pd.DataFrame({
            'high': [spot - 10, spot, spot + 20],
            'low': [spot - 30, spot - 20, spot - 10],
            'close': [spot - 20, spot - 5, spot + 15],
            'volume': [12000, 15000, 22000]
        })
        indicators = TechnicalIndicators.get_latest_indicators(df_candles)

        market_snapshot = {
            "underlying_price": spot,
            "india_vix": 14.5,
            "pcr": pcr,
            "max_pain": max_pain,
            "technical_indicators": indicators,
            "unusual_activities": unusual_events
        }

        # 3. Multi-Agent AI Debate & Consensus
        signal = debate_engine.run_debate(
            market_snapshot=market_snapshot,
            daily_loss_pct=0.0,
            open_positions_count=len(broker.broker.get_positions()),
            max_positions=config.get("trading.max_positions", 2)
        )

        logger.info(f"AI Consensus Action: {signal.action} (Confidence: {signal.overall_confidence*100:.0f}%, Vetoed: {signal.risk_vetoed})")
        logger.info(f"Agent Rationale: {signal.rationale}")

        # 4. Execute Signal via Unified Broker Interface
        if signal.action != "NO_TRADE":
            order_res = broker.execute_signal(signal.model_dump())
            if order_res:
                logger.info(f"Order Placed Successfully: Trade ID {order_res['trade_id']} on {order_res['symbol']}")

        time.sleep(0.5)

    logger.info("\nSimulation run complete. Check dashboard/app.py or SQLite database for logs.")

if __name__ == "__main__":
    main()
