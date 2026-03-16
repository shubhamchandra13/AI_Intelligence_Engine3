import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.config_evolution_engine import ConfigEvolutionEngine

def run_evolution():
    print("Initializing Config Evolution...")
    evolution_engine = ConfigEvolutionEngine()
    evolution_engine.evaluate_and_evolve()

if __name__ == "__main__":
    run_evolution()
