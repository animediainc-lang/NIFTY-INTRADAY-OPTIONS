from data.breeze_client import breeze_client
from data.pre_market_analyzer import pre_market_analyzer
from data.websocket_manager import ws_manager
from data.candle_manager import candle_manager
from data.option_manager import option_manager
from strategies.momentum_breakout import MomentumBreakout
from risk.risk_manager import risk_manager
from app_config.config_loader import config
from logger import logger
import sys
import time
from datetime import datetime

class TradingBot:
    def __init__(self):
        self.strategies = [MomentumBreakout()]
        self.expiry_date = None

    def on_candle_closed(self, candle):
        """Callback executed when a candle completes."""
        logger.info(f"Candle closed: {candle['symbol']} {candle['interval']}m @ {candle['timestamp']} Close: {candle['close']}")

        # Risk Check before processing any signals
        if not risk_manager.check_execution_risk():
            return

        for strategy in self.strategies:
            df = candle_manager.get_candles(candle['symbol'], candle['interval'])
            strategy.update_data(df)

            signal = strategy.get_signal()
            if signal:
                logger.info(f"SIGNAL DETECTED: {signal} by {strategy.name} for {candle['symbol']}")
                # Future Module: execution_engine.execute(signal, strategy)

    def start(self):
        try:
            config.load_config("app_config/config.yaml")
            if not breeze_client.generate_session():
                logger.error("Failed to generate session.")
                return

            # Pre-Market
            self.expiry_date = config.get("trading.expiry_date", datetime.now().strftime("%Y-%m-%dT00:00:00.000Z"))
            metrics = pre_market_analyzer.run_full_analysis(self.expiry_date)
            logger.info(f"Pre-market metrics: {metrics}")

            # Volatility Filter (Example using pre-market or live VIX if available)
            # if not risk_manager.validate_volatility(metrics.get('vix', 0)):
            #    return

            # Wiring
            candle_manager.add_candle_callback(self.on_candle_closed)
            ws_manager.add_callback(candle_manager.process_tick)
            ws_manager.connect()

            # Subscriptions
            symbol = config.get("trading.symbol", "NIFTY")
            ws_manager.subscribe(stock_code=symbol, exchange_code="NSE", product_type="cash")

            # Fetch LTP to select options
            quote = breeze_client.get_quotes(stock_code=symbol, exchange_code="NSE", product_type="cash")
            if quote.get("Success"):
                spot_price = float(quote["Success"][0]["last"])
                option_manager.subscribe_selected_options(ws_manager, self.expiry_date, spot_price)

            logger.info("Bot is running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            ws_manager.disconnect()
        except Exception as e:
            logger.error(f"Error in main bot loop: {e}")

def main():
    bot = TradingBot()
    bot.start()

if __name__ == "__main__":
    main()
