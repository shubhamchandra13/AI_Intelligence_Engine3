import time
import numpy as np

class OrderBookAnalyzer:
    """
    Analyzes L2 Market Depth (Top 5 Bids/Asks)
    OFI 2.0: Institutional Grade Order Flow Imbalance & Absorption Detection.
    """
    def __init__(self, imbalance_threshold=1.5):
        self.imbalance_threshold = imbalance_threshold
        self.last_depth = None
        self.last_delta = 0
        self.last_time = time.time()
        self.velocity_log = []
        self.ofi_history = []
        self.absorption_events = []

    def analyze(self, depth, current_price=None):
        if not depth or 'buy' not in depth or 'sell' not in depth:
            return {"bias": "NEUTRAL", "imbalance": 1.0, "reason": "No Depth Data"}

        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # 1. PRICE-WEIGHTED IMBALANCE (Orders closer to LTP matter more)
        def calculate_weighted_qty(orders, reference_price):
            if not orders or not reference_price:
                return sum(o['quantity'] for o in orders)
            
            weighted_qty = 0
            for o in orders:
                dist = abs(o['price'] - reference_price)
                # Exponential decay weight: w = 1 / (1 + distance)
                weight = 1.0 / (1.0 + (dist / (reference_price * 0.0001))) 
                weighted_qty += o['quantity'] * weight
            return weighted_qty

        total_buy_qty = sum(item['quantity'] for item in depth['buy'])
        total_sell_qty = sum(item['quantity'] for item in depth['sell'])
        
        weighted_buy = calculate_weighted_qty(depth['buy'], current_price)
        weighted_sell = calculate_weighted_qty(depth['sell'], current_price)
        
        # 2. DELTA & VELOCITY
        current_delta = total_buy_qty - total_sell_qty
        delta_change = current_delta - self.last_delta
        self.last_delta = current_delta
        
        velocity = delta_change / dt if dt > 0 else 0
        self.velocity_log.append(velocity)
        if len(self.velocity_log) > 15: self.velocity_log.pop(0)
        avg_velocity = np.mean(self.velocity_log)

        # 3. ABSORPTION DETECTION (Smart Money absorbing orders)
        # If Price is stable but Delta is heavily changing, someone is absorbing.
        absorption_signal = "NONE"
        if current_price and self.last_depth:
            # We look for high delta change with low price movement
            if abs(avg_velocity) > 800 and abs(delta_change) > 1500:
                absorption_signal = "BULLISH_ABSORPTION" if avg_velocity > 0 else "BEARISH_ABSORPTION"

        # 4. LIQUIDITY VOID DETECTION
        buy_prices = [o['price'] for o in depth['buy']]
        sell_prices = [o['price'] for o in depth['sell']]
        
        avg_spread = abs(min(sell_prices) - max(buy_prices)) if buy_prices and sell_prices else 0
        is_void = avg_spread > (current_price * 0.0005) if current_price else False

        # 5. INSTITUTIONAL BIAS (OFI Index)
        ofi_index = (weighted_buy - weighted_sell) / (weighted_buy + weighted_sell) if (weighted_buy + weighted_sell) > 0 else 0
        self.ofi_history.append(ofi_index)
        if len(self.ofi_history) > 20: self.ofi_history.pop(0)
        smoothed_ofi = np.mean(self.ofi_history)

        bias = "NEUTRAL"
        if smoothed_ofi > 0.3: bias = "BULLISH_OFI"
        elif smoothed_ofi < -0.3: bias = "BEARISH_OFI"
        
        if absorption_signal != "NONE":
            bias = f"STRONG_{absorption_signal}"

        self.last_depth = depth

        return {
            "bias": bias,
            "ofi_index": round(smoothed_ofi, 3),
            "velocity": round(avg_velocity, 2),
            "absorption": absorption_signal,
            "imbalance_ratio": round(weighted_buy / weighted_sell, 2) if weighted_sell > 0 else 5.0,
            "liquidity_void": is_void,
            "hft_alert": abs(avg_velocity) > 1200
        }
