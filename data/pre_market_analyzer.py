import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from data.breeze_client import breeze_client
from logger import logger

class PreMarketAnalyzer:
    def __init__(self, stock_code: str = "NIFTY"):
        self.stock_code = stock_code
        self.metrics: Dict[str, Any] = {}

    def calculate_pdl_pdh(self) -> Dict[str, float]:
        """Calculates Previous Day High, Low, and Close for the Spot index."""
        try:
            to_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000Z")

            # For Spot indices like NIFTY, product_type should be 'cash'
            response = breeze_client.get_historical_data(
                stock_code=self.stock_code,
                exchange_code="NSE",
                interval="1day",
                from_date=from_date,
                to_date=to_date,
                product_type="cash"
            )

            if response.get("Status") == 200 and response.get("Success"):
                data = pd.DataFrame(response["Success"])
                if not data.empty:
                    last_day = data.iloc[-1]
                    self.metrics["pdh"] = float(last_day["high"])
                    self.metrics["pdl"] = float(last_day["low"])
                    self.metrics["pdc"] = float(last_day["close"])
                    logger.info(f"PDH: {self.metrics['pdh']}, PDL: {self.metrics['pdl']}")
                    return self.metrics
            return {}
        except Exception as e:
            logger.error(f"Error calculating PDH/PDL: {e}")
            return {}

    def get_option_chain_metrics(self, expiry_date: str) -> Dict[str, Any]:
        """Calculates PCR and Max Pain."""
        try:
            response = breeze_client.get_option_chain(
                stock_code=self.stock_code,
                exchange_code="NFO",
                expiry_date=expiry_date
            )

            if response.get("Status") == 200 and response.get("Success"):
                df = pd.DataFrame(response["Success"])
                df['strike_price'] = df['strike_price'].astype(float)
                df['open_interest'] = df['open_interest'].astype(float)

                # PCR Calculation (Total Put OI / Total Call OI)
                puts = df[df['right'] == 'Put']
                calls = df[df['right'] == 'Call']
                total_put_oi = puts['open_interest'].sum()
                total_call_oi = calls['open_interest'].sum()
                self.metrics["pcr"] = total_put_oi / total_call_oi if total_call_oi > 0 else 0

                # Max Pain Calculation
                strikes = sorted(df['strike_price'].unique())
                pain_scores = []
                for strike in strikes:
                    # Call Pain: (Spot - Strike) if Spot > Strike
                    call_pain = calls.apply(lambda x: max(0, strike - x['strike_price']) * x['open_interest'], axis=1).sum()
                    # Put Pain: (Strike - Spot) if Strike > Spot
                    put_pain = puts.apply(lambda x: max(0, x['strike_price'] - strike) * x['open_interest'], axis=1).sum()
                    pain_scores.append(call_pain + put_pain)

                self.metrics["max_pain"] = strikes[pain_scores.index(min(pain_scores))]

                logger.info(f"PCR: {self.metrics['pcr']:.2f}, Max Pain: {self.metrics['max_pain']}")
                return self.metrics
            return {}
        except Exception as e:
            logger.error(f"Error calculating option chain metrics: {e}")
            return {}

    def run_full_analysis(self, expiry_date: str):
        """Runs all pre-market checks."""
        logger.info("Starting Pre-Market Analysis...")
        self.calculate_pdl_pdh()
        self.get_option_chain_metrics(expiry_date)
        logger.info("Pre-Market Analysis Complete.")
        return self.metrics

# Global analyzer
pre_market_analyzer = PreMarketAnalyzer()
