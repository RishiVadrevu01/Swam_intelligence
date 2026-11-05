import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.compliance_predictor import compliance_predictor

if __name__ == "__main__":
    print("=== Training XGBoost Driver Compliance Model ===")
    compliance_predictor.train_and_save(n_samples=2000)
    print("=== Training Complete ===")

