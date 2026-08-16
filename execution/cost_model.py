from typing import Dict, Any

class TransactionCostModel:
    """Accurately calculates total NSE transaction charges, taxes, STT, exchange fees, and slippage for Nifty options."""

    def __init__(
        self,
        brokerage_per_order: float = 20.0,
        stt_sell_pct: float = 0.125, # 0.125% on option premium sell
        exchange_txn_fee_pct: float = 0.05, # ~0.05% of turnover
        gst_pct: float = 18.0, # 18% GST on (Brokerage + Txn Charges)
        stamp_duty_buy_pct: float = 0.003, # 0.003% on buy premium
        slippage_points: float = 1.5
    ):
        self.brokerage_per_order = brokerage_per_order
        self.stt_sell_pct = stt_sell_pct
        self.exchange_txn_fee_pct = exchange_txn_fee_pct
        self.gst_pct = gst_pct
        self.stamp_duty_buy_pct = stamp_duty_buy_pct
        self.slippage_points = slippage_points

    def calculate_costs(self, action: str, price: float, quantity: int) -> Dict[str, float]:
        """Calculates breakdown of all taxes, fees, and slippage for an option order."""
        turnover = price * quantity
        brokerage = self.brokerage_per_order

        # STT applies only on SELL side for options premium
        stt = (turnover * (self.stt_sell_pct / 100.0)) if "SELL" in action or action == "EXIT" else 0.0

        # Stamp Duty applies only on BUY side
        stamp_duty = (turnover * (self.stamp_duty_buy_pct / 100.0)) if "BUY" in action else 0.0

        # Exchange Transaction charges
        exchange_charges = turnover * (self.exchange_txn_fee_pct / 100.0)

        # GST on Brokerage + Exchange charges
        gst = (brokerage + exchange_charges) * (self.gst_pct / 100.0)

        # SEBI Turnover fees + IPFT
        sebi_charges = turnover * 0.000001

        total_statutory_taxes = round(brokerage + stt + stamp_duty + exchange_charges + gst + sebi_charges, 2)
        slippage_cost = round(self.slippage_points * quantity, 2)
        total_cost = round(total_statutory_taxes + slippage_cost, 2)

        return {
            "turnover": round(turnover, 2),
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "stamp_duty": round(stamp_duty, 2),
            "exchange_charges": round(exchange_charges, 2),
            "gst": round(gst, 2),
            "sebi_charges": round(sebi_charges, 2),
            "statutory_taxes": total_statutory_taxes,
            "slippage_cost": slippage_cost,
            "total_cost": total_cost
        }
