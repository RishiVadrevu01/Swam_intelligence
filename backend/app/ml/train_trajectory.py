import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.trajectory_predictor import trajectory_predictor

if __name__ == "__main__":
    print("=== Training Trajectory LSTM Model ===")
    trajectory_predictor.train_and_save(epochs=40)
    print("=== Training Complete ===")

