import os
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Tuple
from app.config import MODELS_DIR


class TrajectoryLSTM(nn.Module):
    """
    LSTM sequence-to-sequence model for future vehicle trajectory prediction.
    Input features per step: [normalized_lat, normalized_lon, speed/100, accel/10, heading/360]
    Output: 5 future steps of [delta_lat, delta_lon]
    """
    def __init__(self, input_size: int = 5, hidden_size: int = 64, num_layers: int = 2, output_steps: int = 5):
        super(TrajectoryLSTM, self).__init__()
        self.output_steps = output_steps
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, output_steps * 2)
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        last_hidden = out[:, -1, :]  # shape: (batch, hidden_size)
        preds = self.fc(last_hidden)  # shape: (batch, output_steps * 2)
        return preds.view(-1, self.output_steps, 2)


class TrajectoryPredictor:
    def __init__(self):
        self.model_path = MODELS_DIR / "trajectory_lstm.pt"
        self.device = torch.device("cpu")
        self.model = TrajectoryLSTM().to(self.device)
        self.is_trained = False
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(self.model_path):
            try:
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
                self.model.eval()
                self.is_trained = True
                print("Loaded trained Trajectory LSTM model from disk.")
                return
            except Exception as e:
                print(f"Failed to load saved LSTM model: {e}. Retraining...")
        self.train_and_save()

    def train_and_save(self, epochs: int = 35):
        """
        Generates synthetic trajectory sequences and trains the LSTM model.
        """
        print("Training Trajectory LSTM model...")
        np.random.seed(42)
        torch.manual_seed(42)

        # Generate 1500 trajectory sequences: 5 past steps -> 5 future steps
        num_samples = 1500
        seq_len = 5
        pred_steps = 5

        X_data = []
        Y_data = []

        # Base reference coordinates
        base_lat = 37.7780
        base_lon = -122.4180

        for _ in range(num_samples):
            # random heading 40 - 55 deg (Northeast along Market St)
            heading = np.random.uniform(42.0, 52.0)
            rad = np.radians(heading)
            speed = np.random.uniform(25.0, 60.0)  # km/h
            speed_ms = speed / 3.6
            accel = np.random.uniform(-1.5, 1.5)

            # Generate 10 consecutive steps (dt = 1 sec)
            lat_seq = []
            lon_seq = []
            cur_lat = base_lat + np.random.uniform(-0.005, 0.005)
            cur_lon = base_lon + np.random.uniform(-0.005, 0.005)

            for step in range(seq_len + pred_steps):
                cur_speed = max(5.0, speed_ms + accel * step)
                dist_step = cur_speed * 1.0  # meters
                # 1 degree lat ~ 111,000 meters; 1 degree lon ~ 88,000 meters
                d_lat = (dist_step * np.cos(rad)) / 111000.0
                d_lon = (dist_step * np.sin(rad)) / 88000.0
                cur_lat += d_lat
                cur_lon += d_lon
                lat_seq.append(cur_lat)
                lon_seq.append(cur_lon)

            # Features for 5 input steps
            past_features = []
            for s in range(seq_len):
                past_features.append([
                    lat_seq[s] - base_lat,
                    lon_seq[s] - base_lon,
                    speed / 100.0,
                    accel / 10.0,
                    heading / 360.0
                ])

            # Targets: delta from last input step to future 5 steps
            last_lat = lat_seq[seq_len - 1]
            last_lon = lon_seq[seq_len - 1]
            future_deltas = []
            for s in range(seq_len, seq_len + pred_steps):
                future_deltas.append([
                    lat_seq[s] - last_lat,
                    lon_seq[s] - last_lon
                ])

            X_data.append(past_features)
            Y_data.append(future_deltas)

        X_tensor = torch.tensor(X_data, dtype=torch.float32)
        Y_tensor = torch.tensor(Y_data, dtype=torch.float32)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.005)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss = criterion(outputs, Y_tensor)
            loss.backward()
            optimizer.step()

        self.model.eval()
        self.is_trained = True
        try:
            torch.save(self.model.state_dict(), self.model_path)
            print(f"Trajectory LSTM model trained (final loss: {loss.item():.6f}) and saved to {self.model_path}.")
        except Exception as e:
            print(f"Warning: could not save weights to disk: {e}")

    def predict_trajectory(self, vehicle: Dict[str, Any], steps: int = 5) -> Dict[str, Any]:
        """
        Executes actual LSTM model forward pass on vehicle telemetry to predict future trajectory.
        """
        cur_lat = float(vehicle.get("latitude", 37.7780))
        cur_lon = float(vehicle.get("longitude", -122.4180))
        speed = float(vehicle.get("speed", 40.0))
        accel = float(vehicle.get("acceleration", 0.0))
        heading = float(vehicle.get("heading", 48.0))

        # Reconstruct last 5 historical timesteps from current kinematics
        dt = 1.0
        rad = np.radians(heading)
        speed_ms = speed / 3.6
        dist_per_step = speed_ms * dt
        d_lat_step = (dist_per_step * np.cos(rad)) / 111000.0
        d_lon_step = (dist_per_step * np.sin(rad)) / 88000.0

        hist_points = []
        for i in range(4, -1, -1):
            h_lat = cur_lat - i * d_lat_step
            h_lon = cur_lon - i * d_lon_step
            hist_points.append({"latitude": round(h_lat, 6), "longitude": round(h_lon, 6), "t_step": -i})

        # Base reference coordinates
        base_lat = 37.7780
        base_lon = -122.4180

        # Construct input sequence tensor (1, 5, 5)
        input_seq = []
        for p in hist_points:
            input_seq.append([
                p["latitude"] - base_lat,
                p["longitude"] - base_lon,
                speed / 100.0,
                accel / 10.0,
                heading / 360.0
            ])

        input_tensor = torch.tensor([input_seq], dtype=torch.float32).to(self.device)

        self.model.eval()
        with torch.no_grad():
            preds = self.model(input_tensor)[0].cpu().numpy()  # shape (5, 2)

        predicted_points = []
        uncertainty_radius_base = 1.8  # meters initial uncertainty
        for idx in range(min(steps, len(preds))):
            p_lat = cur_lat + preds[idx][0]
            p_lon = cur_lon + preds[idx][1]
            predicted_points.append({
                "step": idx + 1,
                "seconds_ahead": (idx + 1) * 1.0,
                "latitude": round(float(p_lat), 6),
                "longitude": round(float(p_lon), 6),
                "confidence": round(max(0.60, 0.98 - idx * 0.06), 2)
            })

        return {
            "vehicle_id": vehicle.get("vehicle_id"),
            "historical_points": hist_points,
            "predicted_points": predicted_points,
            "uncertainty_radius_meters": round(uncertainty_radius_base + steps * 0.9, 2),
            "model_used": "PyTorch-LSTM-Seq2Seq",
            "is_actual_model": True
        }


trajectory_predictor = TrajectoryPredictor()

