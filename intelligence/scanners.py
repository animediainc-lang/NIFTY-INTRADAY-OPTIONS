from typing import List, Dict, Any
from data.models import OptionChain, OptionType
from logger import logger

class MarketScanner:
    """Scans option chain for unusual activity, OI spikes, and aggressive buying/selling."""

    def __init__(self, oi_spike_threshold_pct: float = 20.0, volume_spike_multiplier: float = 2.5):
        self.oi_spike_threshold_pct = oi_spike_threshold_pct
        self.volume_spike_multiplier = volume_spike_multiplier

    def scan_unusual_activity(self, option_chain: OptionChain) -> List[Dict[str, Any]]:
        unusual_events = []

        for key, contract in option_chain.contracts.items():
            # Check for significant OI building up relative to existing OI
            if contract.oi > 0:
                oi_change_pct = (contract.change_in_oi / contract.oi) * 100.0
                if oi_change_pct >= self.oi_spike_threshold_pct and contract.change_in_oi > 25000:
                    unusual_events.append({
                        "type": "OI_SPIKE",
                        "strike": contract.strike,
                        "option_type": contract.option_type.value,
                        "oi_change_pct": round(oi_change_pct, 2),
                        "change_in_oi": contract.change_in_oi,
                        "ltp": contract.ltp,
                        "description": f"Unusual OI buildup of {round(oi_change_pct,1)}% ({contract.change_in_oi} contracts) on {contract.strike} {contract.option_type.value}"
                    })

            # Check for unusual heavy volume near ATM
            distance_from_atm = abs(contract.strike - option_chain.atm_strike)
            if distance_from_atm <= 150 and contract.volume > 50000:
                unusual_events.append({
                    "type": "HIGH_VOLUME_ATM",
                    "strike": contract.strike,
                    "option_type": contract.option_type.value,
                    "volume": contract.volume,
                    "ltp": contract.ltp,
                    "description": f"Heavy ATM volume spike ({contract.volume} lots) detected at {contract.strike} {contract.option_type.value}"
                })

        return unusual_events
