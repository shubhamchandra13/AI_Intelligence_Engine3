class PortfolioAllocationEngine:

    def __init__(
        self,
        default_target_capital_pct=0.22,
        max_symbol_exposure_pct=0.30,
        min_target_capital_pct=0.08,
    ):
        self.default_target_capital_pct = float(default_target_capital_pct)
        self.max_symbol_exposure_pct = float(max_symbol_exposure_pct)
        self.min_target_capital_pct = float(min_target_capital_pct)

    def _regime_score(self, regime_name):
        regime_name = str(regime_name or "UNKNOWN")
        if "TREND" in regime_name and "HIGH_VOL" not in regime_name:
            return 1.15
        if "TREND" in regime_name and "HIGH_VOL" in regime_name:
            return 1.0
        if "RANGE" in regime_name:
            return 0.85
        if "EXPLOSIVE" in regime_name:
            return 0.8
        return 0.9

    def _confidence_score(self, confidence):
        try:
            c = float(confidence or 0)
        except Exception:
            c = 0.0
        return max(0.1, min(1.5, c / 60.0))

    def _open_exposure_by_index(self, open_positions, total_equity):
        result = {}
        total_equity = float(total_equity or 0)
        if total_equity <= 0:
            return result
        for pos in open_positions or []:
            idx = str(pos.get("index") or "UNKNOWN")
            capital_used = float(pos.get("capital_used") or 0.0)
            result[idx] = result.get(idx, 0.0) + (capital_used / total_equity) * 100.0
        return result

    def decide_allocation(
        self,
        analysis_map,
        best_index,
        open_positions=None,
        total_equity=0,
        ai_decision=None,
    ):
        if not analysis_map or not best_index or best_index not in analysis_map:
            return {
                "available": False,
                "reason": "insufficient_analysis_map",
            }

        scores = {}
        for symbol, data in analysis_map.items():
            confidence = ((data.get("confidence") or {}).get("confidence")) or 0.0
            regime_name = ((data.get("regime") or {}).get("regime")) or "UNKNOWN"
            rel = float(data.get("relative_score") or 0.0)
            rel_factor = max(0.4, min(1.3, rel / 100.0))
            score = self._confidence_score(confidence) * self._regime_score(regime_name) * rel_factor
            scores[symbol] = max(0.01, score)

        score_sum = sum(scores.values()) or 1.0
        weights = {k: (v / score_sum) for k, v in scores.items()}

        open_exp = self._open_exposure_by_index(open_positions, total_equity)
        current_symbol_exposure = float(open_exp.get(best_index, 0.0))
        remaining_symbol_capacity = max(0.0, (self.max_symbol_exposure_pct * 100.0) - current_symbol_exposure)

        base_target_pct = weights.get(best_index, 0.0) * 100.0
        blended_target = (base_target_pct * 0.55) + (self.default_target_capital_pct * 100.0 * 0.45)
        target_capital_pct = max(self.min_target_capital_pct * 100.0, blended_target)
        target_capital_pct = min(target_capital_pct, remaining_symbol_capacity)

        ai_risk_multiplier = 1.0
        if isinstance(ai_decision, dict):
            try:
                ai_risk_multiplier = float(ai_decision.get("risk_multiplier", 1.0))
            except Exception:
                ai_risk_multiplier = 1.0

        normalized_vs_default = target_capital_pct / max(1.0, self.default_target_capital_pct * 100.0)
        portfolio_risk_multiplier = max(0.5, min(1.3, normalized_vs_default))
        final_risk_multiplier = max(0.35, min(1.35, portfolio_risk_multiplier * ai_risk_multiplier))

        return {
            "available": True,
            "best_index": best_index,
            "symbol_weights": {k: round(v, 4) for k, v in weights.items()},
            "base_target_capital_pct": round(base_target_pct, 2),
            "target_capital_pct": round(target_capital_pct, 2),
            "current_symbol_exposure_pct": round(current_symbol_exposure, 2),
            "remaining_symbol_capacity_pct": round(remaining_symbol_capacity, 2),
            "portfolio_risk_multiplier": round(portfolio_risk_multiplier, 3),
            "final_risk_multiplier": round(final_risk_multiplier, 3),
        }
