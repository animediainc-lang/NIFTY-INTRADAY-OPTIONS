from typing import Dict, List, Optional
from data.models import OptionContract
from data.greeks import GreeksEngine

class OptionChainManager:
    def __init__(self, risk_free_rate: float = 0.07):
        self.risk_free_rate = risk_free_rate
        self.chain: Dict[float, Dict[str, OptionContract]] = {} # strike -> {"CE": OptionContract, "PE": OptionContract}

    def update_contract(self, contract: OptionContract, spot_price: float, time_to_expiry_years: float) -> None:
        strike = contract.strike_price
        if strike not in self.chain:
            self.chain[strike] = {}

        # Calculate IV and Greeks if price available
        if contract.last_price > 0 and spot_price > 0 and time_to_expiry_years > 0:
            iv = GreeksEngine.calculate_implied_volatility(
                market_price=contract.last_price,
                S=spot_price,
                K=strike,
                T=time_to_expiry_years,
                r=self.risk_free_rate,
                option_type=contract.option_type
            )
            contract.implied_volatility = iv
            greeks = GreeksEngine.calculate_greeks(
                S=spot_price,
                K=strike,
                T=time_to_expiry_years,
                r=self.risk_free_rate,
                sigma=iv if iv > 0 else 0.2,
                option_type=contract.option_type
            )
            contract.delta = greeks["delta"]
            contract.gamma = greeks["gamma"]
            contract.theta = greeks["theta"]
            contract.vega = greeks["vega"]

        self.chain[strike][contract.option_type.upper()] = contract

    def calculate_pcr(self) -> float:
        """Put-Call Ratio based on Total Open Interest across all strikes"""
        total_call_oi = 0
        total_put_oi = 0

        for strike, contracts in self.chain.items():
            if "CE" in contracts:
                total_call_oi += contracts["CE"].open_interest
            if "PE" in contracts:
                total_put_oi += contracts["PE"].open_interest

        if total_call_oi == 0:
            return 1.0
        return round(total_put_oi / total_call_oi, 4)

    def calculate_max_pain(self) -> float:
        """Finds the strike price that results in minimum total loss for option writers"""
        strikes = sorted(list(self.chain.keys()))
        if not strikes:
            return 0.0

        min_loss = float('inf')
        max_pain_strike = strikes[0]

        for test_strike in strikes:
            total_loss = 0.0
            for strike, contracts in self.chain.items():
                if "CE" in contracts:
                    ce_oi = contracts["CE"].open_interest
                    if test_strike > strike:
                        total_loss += (test_strike - strike) * ce_oi
                if "PE" in contracts:
                    pe_oi = contracts["PE"].open_interest
                    if test_strike < strike:
                        total_loss += (strike - test_strike) * pe_oi

            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = test_strike

        return max_pain_strike

    def get_atm_strike(self, spot_price: float) -> float:
        """Find closest strike price to current spot price"""
        strikes = list(self.chain.keys())
        if not strikes:
            # Fallback for Nifty 50 strike interval (50 points)
            return round(spot_price / 50.0) * 50.0
        return min(strikes, key=lambda x: abs(x - spot_price))
