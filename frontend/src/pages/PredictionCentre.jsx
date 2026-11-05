import React, { useState } from 'react';
import { 
  BrainCircuit, 
  TrendingUp, 
  CheckCircle2, 
  HelpCircle, 
  XCircle, 
  Target, 
  Navigation, 
  Sparkles, 
  Clock, 
  Shield 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Cell 
} from 'recharts';

export default function PredictionCentre({ 
  predictionData = {}, 
  vehicles = [], 
  trajectoryData = {} 
}) {
  const [selectedVid, setSelectedVid] = useState('V001');

  const complianceMap = predictionData?.compliance_predictions || {};
  const featureImportances = predictionData?.feature_importances || {};
  const selectedCompliance = complianceMap[selectedVid] || {};
  const selectedTrajectory = trajectoryData[selectedVid] || {};

  // Format feature importances for Recharts bar chart
  const importanceChartData = Object.entries(featureImportances).map(([k, v]) => ({
    name: k.replace(/_/g, ' '),
    importance: Math.round(v * 100)
  })).sort((a, b) => b.importance - a.importance);

  return (
    <div className="space-y-6">
      {/* Top AI Module Banner */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <BrainCircuit className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">AI Prediction Centre (Trained LSTM & XGBoost Engines)</h2>
            <p className="text-xs text-slate-400">
              Real-time forward kinematic sequence forecasting via PyTorch LSTM and driver yielding compliance prediction via XGBoost.
            </p>
          </div>
        </div>

        {/* Vehicle Selector for deep-dive */}
        <div className="flex items-center space-x-2">
          <label className="text-xs font-semibold text-slate-300">Vehicle Focus:</label>
          <select
            value={selectedVid}
            onChange={(e) => setSelectedVid(e.target.value)}
            className="bg-slate-800 text-slate-200 text-xs rounded-md border border-slate-700 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 cursor-pointer"
          >
            {vehicles.map((v) => (
              <option key={v.vehicle_id} value={v.vehicle_id}>
                {v.vehicle_id} (Lane {v.current_lane} • {v.speed} km/h)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* SECTION 1: TRAJECTORY PREDICTION (LSTM) */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Navigation className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">
              Kinematic Trajectory Prediction (PyTorch LSTM Seq2Seq) — {selectedVid}
            </h3>
          </div>
          <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
            Uncertainty Radius: ±{selectedTrajectory.uncertainty_radius_meters ?? '6.3'}m
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {(selectedTrajectory.predicted_points || []).map((pt, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/80 space-y-1 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-slate-400 font-bold">t + {pt.seconds_ahead}s</span>
                <span className="text-[10px] font-bold text-emerald-400">{Math.round(pt.confidence * 100)}% conf</span>
              </div>
              <div className="font-mono text-white text-xs pt-1">
                {pt.latitude?.toFixed(5)}
              </div>
              <div className="font-mono text-slate-300 text-xs">
                {pt.longitude?.toFixed(5)}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                Horizon Step #{pt.step}
              </div>
            </div>
          ))}
        </div>

        {/* Historical vs Predicted Summary */}
        <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-800 text-xs text-slate-400 flex flex-wrap justify-between items-center gap-2">
          <span>
            Model: <strong className="text-white">PyTorch LSTM 2-Layer Recurrent Neural Network</strong>
          </span>
          <span>
            Input Window: <strong className="text-cyan-400">5 historical timesteps</strong> (lat, lon, speed, accel, heading)
          </span>
          <span>
            Forecast Horizon: <strong className="text-emerald-400">5 seconds ahead</strong> (dt = 1.0s)
          </span>
        </div>
      </div>

      {/* SECTION 2: DRIVER COMPLIANCE PREDICTION (XGBoost) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* XGBoost Feature Importance Bar Chart */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">XGBoost Feature Importances</h3>
              <p className="text-xs text-slate-400">Key drivers determining yielding compliance</p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              Gini Gain %
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={importanceChartData} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <XAxis type="number" stroke="#64748b" fontSize={10} domain={[0, 40]} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={10} width={90} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f1f5f9' }}
                />
                <Bar dataKey="importance" fill="#06b6d4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Selected Vehicle Compliance Breakdown */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white">Yielding Propensity — {selectedVid}</h3>
            <p className="text-xs text-slate-400">XGBoost Multi-Class Probability Output</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-2">
            <span className="text-xs text-slate-400">Yielding Probability:</span>
            <div className="text-3xl font-bold font-mono text-cyan-400">
              {selectedCompliance.yielding_probability ?? '0.85'}
            </div>
            <div className="flex items-center space-x-2 pt-1">
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                selectedCompliance.compliance_class === 'High' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                selectedCompliance.compliance_class === 'Medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}>
                {selectedCompliance.compliance_class || 'High'} Compliance
              </span>
              <span className="text-xs text-slate-400">
                ({Math.round((selectedCompliance.compliance_confidence || 0.8) * 100)}% model confidence)
              </span>
            </div>
          </div>

          {/* Raw features */}
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Distance from EV:</span>
              <span className="font-mono text-white">{selectedCompliance.raw_features?.distance_from_ev ?? '120.0'} m</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Current Velocity:</span>
              <span className="font-mono text-white">{selectedCompliance.raw_features?.vehicle_speed ?? '42.0'} km/h</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Available Yielding Space:</span>
              <span className="font-mono text-white">{selectedCompliance.raw_features?.available_space ?? '65.0'}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Historical Yielding Actions:</span>
              <span className="font-mono text-emerald-400 font-bold">{selectedCompliance.raw_features?.previous_yielding_actions ?? '7'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Driver Response Time:</span>
              <span className="font-mono text-cyan-400 font-bold">{selectedCompliance.raw_features?.response_time ?? '2.1'}s</span>
            </div>
          </div>
        </div>

        {/* Global Vehicle-wise Prediction Table */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white">Fleet Compliance Roster</h3>
            <p className="text-xs text-slate-400">XGBoost prediction results across all vehicles</p>
          </div>

          <div className="overflow-y-auto max-h-72">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                <tr>
                  <th className="py-2 px-2">Vehicle</th>
                  <th className="py-2 px-2">Yield Prob</th>
                  <th className="py-2 px-2">Class</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {Object.values(complianceMap).map((c) => (
                  <tr
                    key={c.vehicle_id}
                    onClick={() => setSelectedVid(c.vehicle_id)}
                    className={`cursor-pointer transition hover:bg-slate-800/60 ${
                      selectedVid === c.vehicle_id ? 'bg-cyan-950/40 text-cyan-300' : ''
                    }`}
                  >
                    <td className="py-2 px-2 font-mono font-bold">{c.vehicle_id}</td>
                    <td className="py-2 px-2 font-mono text-white">{c.yielding_probability}</td>
                    <td className="py-2 px-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        c.compliance_class === 'High' ? 'text-emerald-400 bg-emerald-500/10' :
                        c.compliance_class === 'Medium' ? 'text-amber-400 bg-amber-500/10' :
                        'text-rose-400 bg-rose-500/10'
                      }`}>
                        {c.compliance_class}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

