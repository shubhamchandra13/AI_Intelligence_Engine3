class ExecutionQualityEngine:

    def __init__(
        self,
        max_spread_pct=1.2,
        min_liquidity_score=35.0,
        max_estimated_slippage_pct=0.8,
    ):
        self.max_spread_pct = float(max_spread_pct)
        self.min_liquidity_score = float(min_liquidity_score)
        self.max_estimated_slippage_pct = float(max_estimated_slippage_pct)

    def _to_float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _pick_value(self, container, keys):
        if not isinstance(container, dict):
            return None
        for key in keys:
            if key in container and container.get(key) is not None:
                return container.get(key)
        market_data = container.get("market_data")
        if isinstance(market_data, dict):
            for key in keys:
                if key in market_data and market_data.get(key) is not None:
                    return market_data.get(key)
        return None

    def evaluate(self, option_block=None, live_price=None):
        option_block = option_block or {}

        bid = self._to_float(self._pick_value(option_block, ["bid_price", "bid"]), 0.0)
        ask = self._to_float(self._pick_value(option_block, ["ask_price", "ask"]), 0.0)
        ltp = self._to_float(
            live_price if live_price is not None else self._pick_value(option_block, ["last_price", "ltp"]),
            0.0,
        )
        oi = self._to_float(self._pick_value(option_block, ["oi", "open_interest"]), 0.0)
        volume = self._to_float(self._pick_value(option_block, ["volume", "traded_volume"]), 0.0)

        spread_abs = 0.0
        spread_pct = None
        if bid > 0 and ask > 0 and ask >= bid:
            spread_abs = ask - bid
            mid = (ask + bid) / 2.0
            if mid > 0:
                spread_pct = (spread_abs / mid) * 100.0

        if spread_pct is None and ltp > 0 and spread_abs > 0:
            spread_pct = (spread_abs / ltp) * 100.0
        if spread_pct is None:
            spread_pct = 0.0

        oi_score = min(40.0, (oi / 150000.0) * 40.0)
        volume_score = min(40.0, (volume / 25000.0) * 40.0)
        spread_score = max(0.0, 20.0 - (spread_pct * 12.0))
        liquidity_score = max(0.0, min(100.0, oi_score + volume_score + spread_score))

        estimated_slippage_pct = (spread_pct * 0.5) + max(0.0, (45.0 - liquidity_score) * 0.01)
        estimated_slippage_pct = round(max(0.0, estimated_slippage_pct), 3)

        reasons = []
        tradable = True
        if spread_pct > self.max_spread_pct:
            tradable = False
            reasons.append(f"spread_pct {round(spread_pct, 3)} > {self.max_spread_pct}")
        if liquidity_score < self.min_liquidity_score:
            tradable = False
            reasons.append(f"liquidity_score {round(liquidity_score, 2)} < {self.min_liquidity_score}")
        if estimated_slippage_pct > self.max_estimated_slippage_pct:
            tradable = False
            reasons.append(
                f"estimated_slippage_pct {round(estimated_slippage_pct, 3)} > {self.max_estimated_slippage_pct}"
            )

        risk_multiplier = 1.0
        if not tradable:
            risk_multiplier = 0.5
        else:
            if estimated_slippage_pct >= 0.5:
                risk_multiplier *= 0.8
            elif estimated_slippage_pct >= 0.25:
                risk_multiplier *= 0.9
            if liquidity_score >= 70:
                risk_multiplier *= 1.05

        risk_multiplier = round(max(0.5, min(1.1, risk_multiplier)), 3)

        return {
            "tradable": tradable,
            "reasons": reasons,
            "bid": round(bid, 4) if bid else None,
            "ask": round(ask, 4) if ask else None,
            "ltp": round(ltp, 4) if ltp else None,
            "oi": round(oi, 2),
            "volume": round(volume, 2),
            "spread_abs": round(spread_abs, 4),
            "spread_pct": round(spread_pct, 4),
            "liquidity_score": round(liquidity_score, 2),
            "estimated_slippage_pct": estimated_slippage_pct,
            "risk_multiplier": risk_multiplier,
        }
