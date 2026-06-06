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
from database.db_manager import db_manager
from telegram.telegram_notifier import notifier
from app_config.config_loader import config
from logger import logger
import sys
import time
from datetime import datetime
import threading
import argparse

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
        symbol_key = candle_manager.get_instrument_key(tick)
        last_price = float(tick.get("last", 0))
        trade_executor.manage_active_trades({symbol_key: last_price})
        candle_manager.process_tick(tick)

    def on_candle_closed(self, candle):
        symbol_key = candle['symbol_key']
        if symbol_key == f"{self.spot_symbol}_0_Spot":
            for strategy in self.strategies:
                df = candle_manager.get_candles(symbol_key, candle['interval'])
                strategy.update_data(df)
                signal = strategy.get_signal()
                if signal == "BUY":
                    if not risk_manager.check_execution_risk():
                        continue
                    scores = ai_filter.generate_score(strategy.name, symbol_key, self.pre_market_metrics)
                    db_manager.log_signal(symbol_key, strategy.name, "BUY", candle['close'], scores['quality_score'])
                    if scores['quality_score'] < 75:
                        logger.warning(f"Trade filtered by AI (Score: {scores['quality_score']})")
                        continue
                    option_details = option_manager.get_atm_strike(candle['close'], signal)
                    if option_details:
                        logger.info(f"ENTRY SIGNAL: {strategy.name} -> ATM {option_details['right']}")
                        trade_executor.execute_signal(
                            signal="BUY",
                            strategy_name=strategy.name,
                            symbol=self.spot_symbol,
                            current_price=candle['close'],
                            stop_loss=candle['close'] - 30,
                            expiry_date=self.expiry_date,
                            strike_price=str(option_details['strike']),
                            right=option_details['right'],
                            exchange="NFO"
                        )
                elif signal == "SELL":
                    for trade_key in list(trade_executor.active_trades.keys()):
                        if trade_key.startswith(self.spot_symbol) and strategy.name in trade_key:
                            logger.info(f"EXIT SIGNAL: {strategy.name} on {symbol_key}")
                            trade_executor.execute_signal(
                                signal="SELL",
                                strategy_name=strategy.name,
                                symbol=self.spot_symbol,
                                current_price=candle['close'],
                                stop_loss=0
                            )

    def start(self):
        try:
            config.load_config("app_config/config.yaml")
            mode = config.get("trading.mode", "paper").upper()
            if mode == "LIVE":
                logger.critical("!!! BOT STARTING IN LIVE TRADING MODE !!!")
                time.sleep(2)
            else:
                logger.info("Bot starting in PAPER TRADING mode.")

            self.spot_symbol = config.get("trading.symbol", "NIFTY")
            self._load_strategies()
            if not breeze_client.generate_session():
                logger.error("Failed to generate session.")
                notifier.notify_error("Failed to generate Breeze session.")
                return
            self.expiry_date = config.get("trading.expiry_date", datetime.now().strftime("%Y-%m-%dT00:00:00.000Z"))
            self.pre_market_metrics = pre_market_analyzer.run_full_analysis(self.expiry_date)
            db_manager.log_daily_metrics(self.pre_market_metrics)
            notifier.notify_market_open(self.pre_market_metrics)
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
            notifier.send_message("🛑 *Bot Shutdown* initiated.")
        except Exception as e:
            logger.error(f"Error in main bot loop: {e}")
            notifier.notify_error(str(e))

def run_dashboard():
    from dashboard.app import app
    app.run_server(debug=False, port=8050, use_reloader=False)

def main():
    parser = argparse.ArgumentParser(description="Nifty Trading Bot")
    parser.add_argument("--no-dashboard", action="store_true", help="Start without the web dashboard")
    args = parser.parse_args()

    if not args.no_dashboard:
        threading.Thread(target=run_dashboard, daemon=True).start()
        logger.info("Web Dashboard started at http://127.0.0.1:8050")

    bot = TradingBot()
    bot.start()

if __name__ == "__main__":
    main()
