import logging
from datetime import datetime, date
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ChangeDetector:
    @staticmethod
    def detect_changes(
        existing_map: Dict[str, Dict[str, Any]], 
        incoming_instruments: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Compares incoming normalized instruments against existing database records.
        Detects:
        - newly listed equities
        - new derivative contracts
        - delisted / deactivated securities
        - expired derivatives
        - symbol changes
        - lot size changes
        """
        changes: List[Dict[str, Any]] = []
        now_str = datetime.now().isoformat()
        today_date = date.today().isoformat()
        
        incoming_tokens = set()
        
        stats = {
            "newly_listed": 0,
            "new_derivatives": 0,
            "delisted": 0,
            "expired": 0,
            "lot_size_changes": 0,
            "symbol_changes": 0
        }

        for inst in incoming_instruments:
            token = inst["instrument_token"]
            incoming_tokens.add(token)
            
            # Check if brand new
            if token not in existing_map:
                if inst["instrument_type"] in ("FUTSTK", "OPTSTK", "FUTIDX", "OPTIDX"):
                    stats["new_derivatives"] += 1
                    changes.append({
                        "change_type": "NEW_DERIVATIVE_CONTRACT",
                        "instrument_token": token,
                        "trading_symbol": inst["trading_symbol"],
                        "exchange": inst["exchange"],
                        "old_value": None,
                        "new_value": f"Expiry: {inst.get('expiry')}, Strike: {inst.get('strike')}",
                        "detected_at": now_str
                    })
                else:
                    stats["newly_listed"] += 1
                    changes.append({
                        "change_type": "NEW_LISTING",
                        "instrument_token": token,
                        "trading_symbol": inst["trading_symbol"],
                        "exchange": inst["exchange"],
                        "old_value": None,
                        "new_value": inst["name"],
                        "detected_at": now_str
                    })
            else:
                # Check for changes in existing instrument
                existing = existing_map[token]
                
                # Lot size changes
                if inst.get("lot_size") and existing.get("lot_size") and inst["lot_size"] != existing["lot_size"]:
                    stats["lot_size_changes"] += 1
                    changes.append({
                        "change_type": "LOT_SIZE_CHANGE",
                        "instrument_token": token,
                        "trading_symbol": inst["trading_symbol"],
                        "exchange": inst["exchange"],
                        "old_value": str(existing["lot_size"]),
                        "new_value": str(inst["lot_size"]),
                        "detected_at": now_str
                    })
                
                # Symbol changes
                if inst.get("trading_symbol") != existing.get("trading_symbol"):
                    stats["symbol_changes"] += 1
                    changes.append({
                        "change_type": "SYMBOL_CHANGE",
                        "instrument_token": token,
                        "trading_symbol": inst["trading_symbol"],
                        "exchange": inst["exchange"],
                        "old_value": existing.get("trading_symbol"),
                        "new_value": inst.get("trading_symbol"),
                        "detected_at": now_str
                    })
                    
            # Check expiry for derivatives
            if inst.get("expiry") and inst["expiry"] < today_date:
                inst["is_active"] = 0
                inst["listing_status"] = "EXPIRED"

        # Check for delisted / disappeared active equities
        for token, existing in existing_map.items():
            if existing.get("is_active") == 1:
                # If derivative, check if naturally expired
                if existing.get("expiry") and existing["expiry"] < today_date:
                    stats["expired"] += 1
                elif token not in incoming_tokens and existing.get("instrument_type") == "EQ":
                    stats["delisted"] += 1
                    changes.append({
                        "change_type": "DELISTED",
                        "instrument_token": token,
                        "trading_symbol": existing["trading_symbol"],
                        "exchange": existing["exchange"],
                        "old_value": "ACTIVE",
                        "new_value": "DELISTED",
                        "detected_at": now_str
                    })

        logger.info("Change detection complete: %s", stats)
        return changes, stats
