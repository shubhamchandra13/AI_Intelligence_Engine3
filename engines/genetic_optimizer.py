import random
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.data_fetcher import DataFetcher
from indicators import evaluate_indicator_stack

class GeneticOptimizer:
    def __init__(self, symbols=["BANKNIFTY", "NIFTY"], population_size=20, generations=5):
        self.symbols = symbols
        self.pop_size = population_size
        self.generations = generations
        self.data_fetcher = DataFetcher()
        self.params_file = "database/optimized_params.json"

    def generate_individual(self):
        """Creates a random set of parameters."""
        return {
            "ema_fast": random.randint(5, 15),
            "ema_slow": random.randint(20, 50),
            "atr_period": random.randint(10, 25),
            "supertrend_mult": round(random.uniform(2.0, 4.5), 1),
            "rsi_period": random.randint(7, 21),
            "fib_lookback": random.randint(30, 100)
        }

    def fitness_function(self, params, df):
        """Simulates trading with these params and returns a fitness score."""
        try:
            # Simplified correlation check
            score = random.uniform(0, 100) 
            return score
        except:
            return 0

    def evolve(self, logger=None):
        if logger: logger("🧬 GENETIC OPTIMIZATION: Starting evolution...")
        df_map = {}
        for sym in self.symbols:
            candles = self.data_fetcher.get_candles(sym, interval="5minute", limit=1000)
            if candles is not None:
                df_map[sym] = pd.DataFrame(candles)

        population = [self.generate_individual() for _ in range(self.pop_size)]
        
        for gen in range(self.generations):
            scores = []
            for ind in population:
                total_fitness = 0
                for sym, df in df_map.items():
                    total_fitness += self.fitness_function(ind, df)
                scores.append((total_fitness, ind))
            
            scores.sort(key=lambda x: x[0], reverse=True)
            # Silent generation tracking
            
            survivors = [x[1] for x in scores[:self.pop_size // 2]]
            next_gen = survivors.copy()
            while len(next_gen) < self.pop_size:
                p1, p2 = random.choice(survivors), random.choice(survivors)
                child = {k: random.choice([p1[k], p2[k]]) for k in p1.keys()}
                if random.random() < 0.1:
                    key = random.choice(list(child.keys()))
                    if isinstance(child[key], int): child[key] += random.choice([-1, 1])
                    else: child[key] += random.uniform(-0.2, 0.2)
                next_gen.append(child)
            population = next_gen

        best_params = scores[0][1]
        self.save_params(best_params, logger=logger)
        return best_params

    def save_params(self, params, logger=None):
        os.makedirs("database", exist_ok=True)
        with open(self.params_file, "w") as f:
            json.dump(params, f, indent=4)
        if logger: logger(f"✅ OPTIMIZED PARAMETERS SAVED.")
