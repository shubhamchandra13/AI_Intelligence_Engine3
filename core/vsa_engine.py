class VSAEngine:
    """
    Volume Spread Analysis (VSA) Engine
    Detects Institutional Footprints like 'Buying Climax', 'Stopping Volume', 'Effort vs Result'
    """
    def __init__(self, lookback=20):
        self.lookback = lookback

    def analyze(self, df):
        """
        Input: DataFrame with 'open', 'high', 'low', 'close', 'volume'
        Returns: Dict with VSA signals
        """
        if len(df) < self.lookback:
            return {"vsa_bias": "NEUTRAL", "strength": 0}

        recent = df.iloc[-1]
        prev = df.iloc[-2]
        avg_vol = df['volume'].tail(self.lookback).mean()
        
        spread = abs(recent['high'] - recent['low'])
        avg_spread = abs(df['high'] - df['low']).tail(self.lookback).mean()
        
        volume_ratio = recent['volume'] / avg_vol if avg_vol > 0 else 1.0
        spread_ratio = spread / avg_spread if avg_spread > 0 else 1.0

        bias = "NEUTRAL"
        signal = "Normal"
        strength = 50

        # 1. Effort vs Result (Bearish Trap)
        if volume_ratio > 1.5 and spread_ratio < 0.7:
            # High Volume but Small Spread = Hidden Selling/Buying
            if recent['close'] > recent['open']:
                bias = "BEARISH"
                signal = "Supply Coming In (Upthrust)"
                strength = 80
            else:
                bias = "BULLISH"
                signal = "Demand Coming In (Stopping Volume)"
                strength = 80

        # 2. Buying Climax
        elif volume_ratio > 2.0 and recent['close'] > prev['close'] and spread_ratio > 1.5:
            bias = "BEARISH"
            signal = "Buying Climax (Potential Top)"
            strength = 75

        # 3. No Demand / No Supply
        elif volume_ratio < 0.5 and spread_ratio < 0.5:
            bias = "NEUTRAL"
            signal = "No Professional Interest"
            strength = 30

        return {
            "vsa_bias": bias,
            "vsa_signal": signal,
            "strength": strength,
            "volume_ratio": round(volume_ratio, 2)
        }
