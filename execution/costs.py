from typing import Dict, Any

class IndianTransactionCostEngine:
    """Calculates realistic Indian Equity Derivatives transaction charges and taxes for NSE Options"""
    def __init__(self,
                 brokerage_per_order: float = 20.0,
                 stt_sell_pct: float = 0.0625,        # 0.0625% on premium (sell side)
                 exchange_turnover_pct: float = 0.053, # NSE exchange charge % on premium
                 sebi_charge_pct: float = 0.0001,      # SEBI charge %
                 stamp_duty_buy_pct: float = 0.003,   # Stamp duty on buy side premium %
                 gst_pct: float = 18.0,                # 18% GST on brokerage + exchange
                 slippage_points: float = 0.5):        # Slippage in premium points
        self.brokerage_per_order = brokerage_per_order
        self.stt_sell_pct = stt_sell_pct
        self.exchange_turnover_pct = exchange_turnover_pct
        self.sebi_charge_pct = sebi_charge_pct
        self.stamp_duty_buy_pct = stamp_duty_buy_pct
        self.gst_pct = gst_pct
        self.slippage_points = slippage_points

    def calculate_trade_costs(self, buy_price: float, sell_price: float, quantity: int) -> Dict[str, float]:
        """Calculates total charges and net PnL for a complete roundtrip option trade"""
        buy_turnover = buy_price * quantity
        sell_turnover = sell_price * quantity
        total_turnover = buy_turnover + sell_turnover

        # Brokerage (₹20 per order buy + sell)
        brokerage = self.brokerage_per_order * 2

        # STT (0.0625% on sell premium turnover)
        stt = (sell_turnover * self.stt_sell_pct) / 100.0

        # Exchange Turnover Charge
        exchange_charges = (total_turnover * self.exchange_turnover_pct) / 100.0

        # SEBI Turnover Fee
        sebi_charges = (total_turnover * self.sebi_charge_pct) / 100.0

        # Stamp Duty (0.003% on buy side turnover)
        stamp_duty = (buy_turnover * self.stamp_duty_buy_pct) / 100.0

        # GST (18% on brokerage + exchange charges)
        gst = ((brokerage + exchange_charges) * self.gst_pct) / 100.0

        # Slippage Cost (0.5 points per side = 1.0 point total * quantity)
        slippage_cost = (self.slippage_points * 2) * quantity

        total_taxes_and_charges = brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst + slippage_cost
        gross_pnl = (sell_price - buy_price) * quantity
        net_pnl = gross_pnl - total_taxes_and_charges

        return {
            "gross_pnl": round(gross_pnl, 2),
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "exchange_charges": round(exchange_charges, 2),
            "sebi_charges": round(sebi_charges, 2),
            "stamp_duty": round(stamp_duty, 2),
            "gst": round(gst, 2),
            "slippage_cost": round(slippage_cost, 2),
            "total_taxes_and_charges": round(total_taxes_and_charges, 2),
            "net_pnl": round(net_pnl, 2)
        }
