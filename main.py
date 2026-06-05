from data.breeze_client import breeze_client
from data.pre_market_analyzer import pre_market_analyzer
from data.websocket_manager import ws_manager
from data.candle_manager import candle_manager
from data.option_manager import option_manager
from strategies.momentum_breakout import MomentumBreakout
from strategies.trend_continuation import TrendContinuation
from strategies.opening_range_breakout import OpeningRangeBreakout
from strategies.ai_filter import ai_filter
from risk.risk_manager import risk_manager
from execution.trade_executor import trade_executor
from execution.order_manager import order_manager
from app_config.config_loader import config
from logger import logger
import sys
import time
from datetime import datetime

class TradingBot:
    def __init__(self):
        self.strategies = []
        self.expiry_date = None
        self.spot_symbol = "NIFTY"
        self.pre_market_metrics = {}

    def _load_strategies(self):
        if config.get("trading.strategy_a_enabled"):
            self.strategies.append(MomentumBreakout())
        if config.get("trading.strategy_b_enabled"):
            self.strategies.append(TrendContinuation())
        if config.get("trading.strategy_c_enabled"):
            self.strategies.append(OpeningRangeBreakout())
        logger.info(f"Loaded {len(self.strategies)} strategies.")

    def on_tick_received(self, tick):
        symbol = tick.get("stock_code")
        last_price = float(tick.get("last", 0))
        trade_executor.manage_active_trades({symbol: last_price})
        candle_manager.process_tick(tick)

    def on_candle_closed(self, candle):
        symbol = candle['symbol']

        if symbol == self.spot_symbol:
            for strategy in self.strategies:
                df = candle_manager.get_candles(symbol, candle['interval'])
                strategy.update_data(df)

                signal = strategy.get_signal()

                if signal == "BUY":
                    # 1. Risk Manager Check
                    if not risk_manager.check_execution_risk():
                        continue

                    # 2. AI Decision Filter Check
                    scores = ai_filter.generate_score(strategy.name, symbol, self.pre_market_metrics)
                    logger.info(f"AI Score for {strategy.name}: {scores['quality_score']}")

                    if scores['quality_score'] < 75:
                        logger.warning(f"Trade filtered by AI (Score: {scores['quality_score']})")
                        continue

                    # 3. Execution
                    option_details = option_manager.get_atm_strike(candle['close'], signal)
                    if option_details:
                        logger.info(f"ENTRY SIGNAL: {strategy.name} on {symbol} -> ATM {option_details['right']}")
                        trade_executor.execute_signal(
                            signal="BUY",
                            strategy_name=strategy.name,
                            symbol=symbol,
                            current_price=candle['close'],
                            stop_loss=candle['close'] - 30,
                            expiry_date=self.expiry_date,
                            strike_price=str(option_details['strike']),
                            right=option_details['right'],
                            exchange="NFO"
                        )

                elif signal == "SELL":
                    trade_key = f"{symbol}_{strategy.name}"
                    if trade_key in trade_executor.active_trades:
                        logger.info(f"EXIT SIGNAL: {strategy.name} on {symbol}")
                        trade_executor.execute_signal(
                            signal="SELL",
                            strategy_name=strategy.name,
                            symbol=symbol,
                            current_price=candle['close'],
                            stop_loss=0
                        )

    def start(self):
        try:
            config.load_config("app_config/config.yaml")
            self.spot_symbol = config.get("trading.symbol", "NIFTY")
            self._load_strategies()

            if not breeze_client.generate_session():
                logger.error("Failed to generate session.")
                return

            self.expiry_date = config.get("trading.expiry_date", datetime.now().strftime("%Y-%m-%dT00:00:00.000Z"))
            self.pre_market_metrics = pre_market_analyzer.run_full_analysis(self.expiry_date)
            logger.info(f"Pre-market metrics: {self.pre_market_metrics}")

            candle_manager.add_candle_callback(self.on_candle_closed)
            ws_manager.add_callback(self.on_tick_received)
            ws_manager.connect()

            ws_manager.subscribe(stock_code=self.spot_symbol, exchange_code="NSE", product_type="cash")

            quote = breeze_client.get_quotes(stock_code=self.spot_symbol, exchange_code="NSE", product_type="cash")
            if quote.get("Success"):
                spot_price = float(quote["Success"][0]["last"])
                option_manager.subscribe_selected_options(ws_manager, self.expiry_date, spot_price)

            logger.info("Bot is running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Shutting down... Squaring off positions.")
            order_manager.emergency_square_off()
            ws_manager.disconnect()
        except Exception as e:
            logger.error(f"Error in main bot loop: {e}")

def main():
    bot = TradingBot()
    bot.start()

if __name__ == "__main__":
    main()
