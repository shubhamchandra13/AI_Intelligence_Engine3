import sys
import os

# Add parent dir to path to allow importing core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run

if __name__ == "__main__":
    print("Starting Live Paper Trading...")
    run()
