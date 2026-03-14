# ============================================================
# 🧠 SIMULATION ENGINE
# Monte Carlo Capital Stress Testing
# ============================================================

import random
import numpy as np


class SimulationEngine:

    def __init__(self, initial_capital=50000):
        self.initial_capital = initial_capital

    # ============================================================
    # MONTE CARLO SIMULATION
    # ============================================================

    def run_simulation(
        self,
        win_rate=0.55,
        avg_win_r=2.0,
        avg_loss_r=-1.0,
        risk_percent=1.0,
        num_trades=200
    ):

        capital = self.initial_capital
        equity_curve = [capital]

        for _ in range(num_trades):

            risk_amount = capital * (risk_percent / 100)

            if random.random() < win_rate:
                r = random.uniform(avg_win_r * 0.8, avg_win_r * 1.2)
            else:
                r = random.uniform(avg_loss_r * 0.8, avg_loss_r * 1.2)

            pnl = r * risk_amount
            capital += pnl
            equity_curve.append(capital)

        max_dd = self.calculate_drawdown(equity_curve)
        final_capital = capital
        growth_percent = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        return {
            "final_capital": round(final_capital, 2),
            "growth_percent": round(growth_percent, 2),
            "max_drawdown": round(max_dd, 2)
        }

    # ============================================================
    # DRAWDOWN CALCULATION
    # ============================================================

    def calculate_drawdown(self, equity_curve):

        peak = equity_curve[0]
        max_dd = 0

        for value in equity_curve:
            if value > peak:
                peak = value

            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd