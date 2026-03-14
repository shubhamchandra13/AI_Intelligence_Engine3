# ============================================================
# 🏛 PAPER EXECUTION ENGINE – FULLY INTEGRATED VERSION
# Advanced Risk + Adaptive Exit Upgrade
# ✅ Correct Option BUY Logic Applied
# ============================================================

class PaperExecutionEngine:

    def __init__(self, initial_capital=50000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = None
        self.last_closed_trade = None

    # ============================================================
    # ENTER TRADE
    # ============================================================

    def enter_trade(self, index, direction, price,
                    confidence, df,
                    dynamic_risk, target_multiplier):

        # Direction normalization (kept for analytics only)
        if direction in ["CE", "BULLISH"]:
            direction = "BULLISH"
        else:
            direction = "BEARISH"

        risk_amount = self.capital * (dynamic_risk / 100)

        stop_distance = price * 0.10  # 10% premium risk

        # ✅ OPTION BUY LOGIC (WORKS FOR BOTH CE & PE)
        stop = price - stop_distance
        target = price + (stop_distance * target_multiplier)

        self.position = {
            "index": index,
            "direction": direction,
            "entry": price,
            "stop": stop,
            "target": target,
            "risk_amount": risk_amount,
            "risk_distance": abs(price - stop),
            "confidence": confidence,
            "r_multiple_reached": 0
        }

        print("\n🚀 ENTER TRADE")
        print(f"Index ➜ {index}")
        print(f"Direction ➜ {direction}")
        print(f"Entry ➜ {price}")
        print(f"Stop ➜ {round(stop,2)}")
        print(f"Target ➜ {round(target,2)}")
        print(f"Risk % ➜ {dynamic_risk}%")

    # ============================================================
    # TRAILING LOGIC (Premium Based)
    # ============================================================

    def apply_trailing(self, current_price):

        if not self.position:
            return

        entry = self.position["entry"]
        risk_distance = self.position["risk_distance"]

        if risk_distance == 0:
            return

        move = current_price - entry  # ✅ Premium based

        r_multiple = move / risk_distance

        if r_multiple >= 1 and self.position["r_multiple_reached"] < 1:
            self.position["stop"] = entry
            self.position["r_multiple_reached"] = 1
            print("🔒 Stop moved to Breakeven")

        if r_multiple >= 1.5 and self.position["r_multiple_reached"] < 1.5:
            self.position["stop"] = entry + (risk_distance * 0.5)
            self.position["r_multiple_reached"] = 1.5
            print("💰 Locked 0.5R Profit")

        if r_multiple >= 2 and self.position["r_multiple_reached"] < 2:
            self.position["stop"] = current_price - risk_distance
            self.position["r_multiple_reached"] = 2
            print("📈 Aggressive Trailing Activated")

    # ============================================================
    # EXIT CHECK
    # ============================================================

    def check_exit(self, current_price, bias=None, confidence=None):

        if not self.position:
            return None

        self.apply_trailing(current_price)

        stop = self.position["stop"]
        target = self.position["target"]

        exit_reason = None

        # 🔥 Confidence Drop Exit
        if confidence is not None and confidence < 50:
            exit_reason = "CONFIDENCE DROP"

        # 🔥 Bias Flip Exit (optional analytics exit)
        if bias is not None:
            if self.position["direction"] == "BULLISH" and bias == "BEARISH":
                exit_reason = "BIAS FLIP"
            elif self.position["direction"] == "BEARISH" and bias == "BULLISH":
                exit_reason = "BIAS FLIP"

        # ✅ PREMIUM BASED STOP/TARGET
        if not exit_reason:
            if current_price <= stop:
                exit_reason = "STOP HIT"
            elif current_price >= target:
                exit_reason = "TARGET HIT"

        if exit_reason:

            if exit_reason == "STOP HIT":
                pnl = -self.position["risk_amount"]
            else:
                pnl = (
                    (current_price - self.position["entry"])
                    / self.position["risk_distance"]
                ) * self.position["risk_amount"]

            self.capital += pnl

            # ✅ FIXED FOR TRADE LOGGER COMPATIBILITY
            closed_trade = {
                "index": self.position["index"],
                "direction": self.position["direction"],
                "entry_price": self.position["entry"],   # FIX
                "exit_price": current_price,             # FIX
                "pnl": pnl,
                "reason": exit_reason,
                "confidence": self.position["confidence"]
            }

            print(f"\n❌ EXIT: {exit_reason} | PnL: {round(pnl,2)}")

            self.last_closed_trade = closed_trade
            self.position = None

            return closed_trade

        return None

    # ============================================================
    # STATUS
    # ============================================================

    def print_status(self):

        print("\n📂 PORTFOLIO STATUS")
        print(f"Initial Capital ➜ ₹{self.initial_capital}")
        print(f"Current Capital ➜ ₹{round(self.capital,2)}")

        if self.position:
            print("\n📌 OPEN POSITION")
            for k, v in self.position.items():
                if k not in ["risk_amount", "risk_distance"]:
                    print(f"{k} ➜ {v}")
        else:
            print("Open Position ➜ None")

    # ============================================================
    # PROPERTY
    # ============================================================

    @property
    def current_capital(self):
        return self.capital