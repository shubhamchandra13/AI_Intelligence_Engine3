# ============================================================
# 📊 PERFORMANCE ANALYTICS ENGINE
# Tracks Win Rate, Drawdown, Equity Curve, Trade Stats
# ============================================================

class PerformanceEngine:

    def __init__(self):
        self.equity_curve = []
        self.closed_trades = []
        self.max_equity = 0
        self.max_drawdown = 0

    # ============================================
    # RECORD CLOSED TRADE
    # ============================================

    def record_trade(self, trade_data, current_capital):

        self.closed_trades.append(trade_data)
        self.equity_curve.append(current_capital)

        if current_capital > self.max_equity:
            self.max_equity = current_capital

        drawdown = self.max_equity - current_capital

        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown

    # ============================================
    # CALCULATE METRICS
    # ============================================

    def calculate_stats(self):

        total = len(self.closed_trades)

        if total == 0:
            return None

        wins = sum(1 for t in self.closed_trades if t["pnl"] > 0)
        losses = sum(1 for t in self.closed_trades if t["pnl"] <= 0)

        win_rate = round((wins / total) * 100, 2)

        avg_profit = round(
            sum(t["pnl"] for t in self.closed_trades if t["pnl"] > 0) / wins,
            2
        ) if wins > 0 else 0

        avg_loss = round(
            sum(t["pnl"] for t in self.closed_trades if t["pnl"] <= 0) / losses,
            2
        ) if losses > 0 else 0

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "max_drawdown": round(self.max_drawdown, 2)
        }

    # ============================================
    # PRINT PERFORMANCE DASHBOARD
    # ============================================

    def print_performance(self):

        stats = self.calculate_stats()

        if stats is None:
            print("\n📊 PERFORMANCE: No closed trades yet.")
            return

        print("\n" + "═" * 75)
        print("📊 PERFORMANCE ANALYTICS DASHBOARD")
        print("═" * 75)

        print(f"📚 Total Trades      ➜ {stats['total_trades']}")
        print(f"🏆 Wins              ➜ {stats['wins']}")
        print(f"❌ Losses            ➜ {stats['losses']}")
        print(f"📈 Win Rate          ➜ {stats['win_rate']}%")
        print(f"💰 Avg Profit        ➜ ₹{stats['avg_profit']}")
        print(f"🔻 Avg Loss          ➜ ₹{stats['avg_loss']}")
        print(f"⚠️ Max Drawdown      ➜ ₹{stats['max_drawdown']}")
        print("═" * 75)