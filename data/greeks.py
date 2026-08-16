import math
from scipy.stats import norm

class GreeksEngine:
    @staticmethod
    def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        if T <= 0 or sigma <= 0:
            return 0.0
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    @staticmethod
    def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        if T <= 0 or sigma <= 0:
            return 0.0
        return GreeksEngine._d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

    @classmethod
    def calculate_price(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> float:
        """Black-Scholes Option Pricing"""
        if T <= 0 or sigma <= 0:
            return max(0.0, S - K) if option_type.upper() == "CE" else max(0.0, K - S)

        d1 = cls._d1(S, K, T, r, sigma)
        d2 = cls._d2(S, K, T, r, sigma)

        if option_type.upper() == "CE":
            return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    @classmethod
    def calculate_greeks(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> dict:
        """Returns Delta, Gamma, Theta, Vega for an option"""
        if T <= 0 or sigma <= 0:
            return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

        d1 = cls._d1(S, K, T, r, sigma)
        d2 = cls._d2(S, K, T, r, sigma)
        pdf_d1 = norm.pdf(d1)

        gamma = pdf_d1 / (S * sigma * math.sqrt(T))
        vega = S * pdf_d1 * math.sqrt(T) / 100.0  # Normalized per 1% IV change

        if option_type.upper() == "CE":
            delta = norm.cdf(d1)
            theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365.0
        else:
            delta = norm.cdf(d1) - 1.0
            theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365.0

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega": round(vega, 4)
        }

    @classmethod
    def calculate_implied_volatility(cls, market_price: float, S: float, K: float, T: float, r: float, option_type: str = "CE") -> float:
        """Newton-Raphson method to estimate Implied Volatility"""
        if T <= 0 or market_price <= 0:
            return 0.0

        sigma = 0.2  # Initial guess 20%
        for _ in range(100):
            price = cls.calculate_price(S, K, T, r, sigma, option_type)
            vega = cls.calculate_greeks(S, K, T, r, sigma, option_type)["vega"] * 100.0
            diff = price - market_price

            if abs(diff) < 1e-4:
                return round(sigma, 4)
            if vega < 1e-6:
                break

            sigma -= diff / vega
            if sigma <= 0.001:
                sigma = 0.001

        return round(sigma, 4)
