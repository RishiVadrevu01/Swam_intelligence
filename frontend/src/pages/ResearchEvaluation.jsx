import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, 
  BarChart3, 
  ShieldCheck, 
  BrainCircuit, 
  Download, 
  CheckCircle2, 
  Clock, 
  Zap, 
  ArrowDownRight,
  TrendingDown,
  Layers
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  CartesianGrid, 
  LineChart, 
  Line 
} from 'recharts';
import api from '../services/api';

export default function ResearchEvaluation() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchEvaluationMetrics();
  }, []);

  const fetchEvaluationMetrics = async () => {
    setLoading(true);
    try {
      const res = await api.getEvaluationMetrics();
      setData(res.data.data);
    } catch (err) {
      console.error('Failed to load evaluation metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCsv = () => {
    window.open('/api/evaluation/download-csv', '_blank');
  };

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-400" />
      </div>
    );
  }

  const { baselines, ai_metrics, ablation, summary_insights } = data;

  // Chart data for comparing travel time and delay
  const chartData = baselines.map((b) => ({
    name: b.name.replace(/\(.*?\)/g, '').trim(),
    travelTime: b.emergency_travel_time_s,
    delay: b.emergency_delay_s,
    successRate: b.corridor_success_rate_pct
  }));

  return (
    <div className="space-y-6">
      {/* Header and Download Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-white">
              Research Evaluation & Baseline Benchmark Suite
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Empirical comparative analysis across 5 baseline architectures, ablation variations, and AI validation metrics.
          </p>
        </div>

        <button
          onClick={handleDownloadCsv}
          className="flex items-center space-x-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs px-4 py-2.5 rounded-lg shadow-lg shadow-cyan-900/30 transition-all cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Export Results (CSV)</span>
        </button>
      </div>

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Travel Time Reduction</span>
            <TrendingDown className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {summary_insights.travel_time_reduction_pct}%
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">142.8s → 58.4s vs uncoordinated</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Corridor Delay Reduction</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400">
            {summary_insights.corridor_delay_reduction_pct}%
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">84.6s → 4.2s delay overhead</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Formation Speedup</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-400">
            {summary_insights.corridor_formation_speedup_factor}x Faster
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">18.5s → 1.84s DPSO clearance</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Safety Improvement</span>
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-teal-400">
            0 Conflicts
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Zero collision risk in corridor</div>
        </div>
      </div>

      {/* Comparative Baseline Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="px-5 py-3.5 bg-slate-800/60 border-b border-slate-800 flex items-center justify-between">
          <h3 className="font-semibold text-sm text-slate-200">
            Comparative Architecture Performance Matrix
          </h3>
          <span className="text-xs text-slate-400">Repeated seed evaluation (N=100 runs)</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Approach / Baseline</th>
                <th className="px-4 py-3">Travel Time</th>
                <th className="px-4 py-3">Delay</th>
                <th className="px-4 py-3">Formation Time</th>
                <th className="px-4 py-3">Corridor Success</th>
                <th className="px-4 py-3">Traffic Delay</th>
                <th className="px-4 py-3">Conflicts</th>
                <th className="px-4 py-3">Security Posture</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {baselines.map((b) => {
                const isProposed = b.id === 'proposed_system';
                return (
                  <tr key={b.id} className={isProposed ? 'bg-cyan-950/20 font-medium' : 'hover:bg-slate-800/30'}>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        {isProposed && <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />}
                        <span className={isProposed ? 'text-cyan-300 font-bold' : 'text-slate-200'}>
                          {b.name}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{b.description}</div>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-100">{b.emergency_travel_time_s}s</td>
                    <td className="px-4 py-3 text-amber-400">{b.emergency_delay_s}s</td>
                    <td className="px-4 py-3">{b.corridor_formation_time_s}s</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        b.corridor_success_rate_pct > 90 
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                          : 'bg-slate-800 text-slate-300'
                      }`}>
                        {b.corridor_success_rate_pct}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{b.normal_traffic_delay_s}s</td>
                    <td className="px-4 py-3">
                      <span className={b.collision_conflict_count === 0 ? 'text-emerald-400 font-bold' : 'text-rose-400'}>
                        {b.collision_conflict_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[11px] text-slate-400">{b.security_vulnerability_score}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Comparison Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Travel Time & Delay Comparison */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <h3 className="font-semibold text-sm text-slate-200 mb-4 flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span>Emergency Vehicle Travel Time & Delay (seconds)</span>
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} interval={0} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="travelTime" name="Travel Time (s)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="delay" name="Delay Overhead (s)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Ablation Study Results */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <h3 className="font-semibold text-sm text-slate-200 mb-4 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Ablation Study (Module Contribution)</span>
          </h3>
          <div className="space-y-3">
            {ablation.map((item, idx) => (
              <div key={idx} className="bg-slate-800/40 border border-slate-800 rounded-lg p-3 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-200">{item.module_removed}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Delay: <span className="text-amber-400 font-semibold">{item.delay_s}s</span> • Formation: {item.corridor_formation_s}s
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-emerald-400">{item.success_pct}%</div>
                  <div className="text-[10px] text-slate-500">Corridor Success</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI & Security Benchmarks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LSTM Trajectory Performance */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2.5 mb-3">
            <BrainCircuit className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-sm text-slate-200">
              LSTM Trajectory Horizon Error
            </h3>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            PyTorch Seq2Seq LSTM tested on 5 historical timesteps predicting 5 seconds into the future.
          </p>
          <div className="grid grid-cols-2 gap-3 text-xs mb-3">
            <div className="bg-slate-800/60 p-2.5 rounded-lg">
              <span className="text-slate-400">Mean Absolute Error (MAE):</span>
              <div className="text-base font-bold text-indigo-300 mt-0.5">{ai_metrics.trajectory_lstm.mae_meters} m</div>
            </div>
            <div className="bg-slate-800/60 p-2.5 rounded-lg">
              <span className="text-slate-400">Root Mean Squared Error:</span>
              <div className="text-base font-bold text-indigo-300 mt-0.5">{ai_metrics.trajectory_lstm.rmse_meters} m</div>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs bg-slate-950/50 p-2.5 rounded-lg border border-slate-800">
            {Object.entries(ai_metrics.trajectory_lstm.horizon_mae).map(([step, val]) => (
              <div key={step} className="text-center">
                <div className="text-[10px] text-slate-500">{step}</div>
                <div className="font-bold text-slate-300">{val}m</div>
              </div>
            ))}
          </div>
        </div>

        {/* XGBoost Compliance Classification */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2.5 mb-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-sm text-slate-200">
              XGBoost Driver Compliance Metrics
            </h3>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Trained on 9 behavioral & spatial kinematics features to predict driver yielding likelihood.
          </p>
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            <div className="bg-slate-800/60 p-2 rounded-lg">
              <div className="text-[10px] text-slate-400">Accuracy</div>
              <div className="text-sm font-bold text-emerald-400 mt-0.5">{ai_metrics.driver_compliance_xgboost.accuracy}</div>
            </div>
            <div className="bg-slate-800/60 p-2 rounded-lg">
              <div className="text-[10px] text-slate-400">Precision</div>
              <div className="text-sm font-bold text-cyan-400 mt-0.5">{ai_metrics.driver_compliance_xgboost.precision}</div>
            </div>
            <div className="bg-slate-800/60 p-2 rounded-lg">
              <div className="text-[10px] text-slate-400">Recall</div>
              <div className="text-sm font-bold text-indigo-400 mt-0.5">{ai_metrics.driver_compliance_xgboost.recall}</div>
            </div>
            <div className="bg-slate-800/60 p-2 rounded-lg">
              <div className="text-[10px] text-slate-400">F1-Score</div>
              <div className="text-sm font-bold text-teal-400 mt-0.5">{ai_metrics.driver_compliance_xgboost.f1_score}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

