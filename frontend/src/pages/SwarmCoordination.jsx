import React, { useState } from 'react';
import { 
  Network, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  RefreshCw, 
  Zap, 
  Sliders, 
  ShieldCheck 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend 
} from 'recharts';
import api from '../services/api';

export default function SwarmCoordination({ dpsoData = {}, onRefreshDPSO }) {
  const [numParticles, setNumParticles] = useState(25);
  const [maxIters, setMaxIters] = useState(30);
  const [running, setRunning] = useState(false);
  const [liveData, setLiveData] = useState(dpsoData);

  const data = liveData.participating_agents ? liveData : dpsoData;
  const convergence = data?.convergence_history || [];
  const actions = data?.recommended_actions || [];
  const breakdown = data?.objective_breakdown || {};

  const handleRunDPSO = async () => {
    setRunning(true);
    try {
      const res = await api.executeCoordination({
        num_particles: numParticles,
        max_iterations: maxIters
      });
      setLiveData(res.data.data);
      if (onRefreshDPSO) onRefreshDPSO(res.data.data);
    } catch (err) {
      console.error('Failed to run DPSO:', err);
    } finally {
      setRunning(false);
    }
  };

  const getActionBadgeColor = (actionType) => {
    switch (actionType) {
      case 'MOVE_LEFT':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'MOVE_RIGHT':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'REDUCE_SPEED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'MAINTAIN_GAP':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Hyperparameter Controls */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
            <Network className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Distributed Particle Swarm Optimization (DPSO) Swarm Engine</h2>
            <p className="text-xs text-slate-400">
              Multi-agent decentralized coordination identifying safe lateral and longitudinal corridor yields.
            </p>
          </div>
        </div>

        {/* DPSO Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-slate-300">
            <span>Particles:</span>
            <input
              type="number"
              min={10}
              max={60}
              value={numParticles}
              onChange={(e) => setNumParticles(Number(e.target.value))}
              className="w-14 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-xs"
            />
          </div>
          <div className="flex items-center space-x-1.5 text-xs text-slate-300">
            <span>Iterations:</span>
            <input
              type="number"
              min={10}
              max={50}
              value={maxIters}
              onChange={(e) => setMaxIters(Number(e.target.value))}
              className="w-14 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-xs"
            />
          </div>
          <button
            onClick={handleRunDPSO}
            disabled={running}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
            <span>{running ? 'Optimizing...' : 'Run Swarm DPSO'}</span>
          </button>
        </div>
      </div>

      {/* DPSO Execution Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Participating Agents</span>
          <div className="text-2xl font-bold text-white mt-1">
            {data.participating_agents?.length || 24} Nodes
          </div>
          <span className="text-[11px] text-slate-400">Non-quarantined</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Initial Swarm Fitness</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {data.initial_fitness ?? '8.45'}
          </div>
          <span className="text-[11px] text-slate-400">High latency & conflict</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Optimal Best Fitness</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {data.best_fitness ?? '2.14'}
          </div>
          <span className="text-[11px] text-emerald-400 font-semibold">
            {data.initial_fitness ? `${Math.round(((data.initial_fitness - data.best_fitness) / data.initial_fitness) * 100)}% optimized` : 'Minimized'}
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Conflicts Detected</span>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {data.conflicts_detected ?? 0}
          </div>
          <span className="text-[11px] text-cyan-300">Adjacent path conflicts</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Execution Runtime</span>
          <div className="text-2xl font-bold text-violet-400 mt-1">
            {data.execution_time_ms ? `${data.execution_time_ms} ms` : '18.4 ms'}
          </div>
          <span className="text-[11px] text-slate-400">Real-time edge compute</span>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Convergence Chart */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">DPSO Multi-Objective Convergence History</h3>
              <p className="text-xs text-slate-400">Swarm iterations vs. Best & Mean Particle Fitness</p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              w=0.65, c₁=1.4, c₂=1.6
            </span>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={convergence} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <XAxis dataKey="iteration" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                <Line type="monotone" dataKey="best_fitness" name="Best Fitness (gBest)" stroke="#10b981" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="average_fitness" name="Mean Swarm Fitness" stroke="#06b6d4" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Fitness Objective Breakdown */}
          <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800 grid grid-cols-5 gap-2 text-center text-xs">
            <div>
              <span className="text-[10px] text-slate-500">Emergency Delay (α)</span>
              <div className="font-mono text-white mt-0.5">{breakdown.emergency_delay ?? '0.00'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500">Safety Headway (β)</span>
              <div className="font-mono text-white mt-0.5">{breakdown.safety_penalty ?? '0.12'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500">Traffic Delay (γ)</span>
              <div className="font-mono text-white mt-0.5">{breakdown.traffic_delay ?? '0.34'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500">Conflicts (δ)</span>
              <div className="font-mono text-white mt-0.5">{breakdown.conflict_penalty ?? '0.00'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500">Compliance Risk (ε)</span>
              <div className="font-mono text-white mt-0.5">{breakdown.compliance_penalty ?? '0.08'}</div>
            </div>
          </div>
        </div>

        {/* Right Column: Recommended Actions Table */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">Recommended Vehicle Coordination Actions</h3>
              <p className="text-xs text-slate-400">Swarm-optimized movement actions dispatched to vehicles</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">
              {actions.length} Directives
            </span>
          </div>

          <div className="overflow-y-auto max-h-[340px]">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                <tr>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Lane Transition</th>
                  <th className="py-2.5 px-3">Action Directive</th>
                  <th className="py-2.5 px-3">Target Speed</th>
                  <th className="py-2.5 px-3">Headway Margin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {actions.map((act) => (
                  <tr key={act.vehicle_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">{act.vehicle_id}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-200">
                      Lane {act.current_lane} → <span className="text-white font-bold">Lane {act.recommended_lane}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getActionBadgeColor(act.action_type)}`}>
                        {act.action_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-emerald-400">{act.target_speed} km/h</td>
                    <td className="py-2.5 px-3 text-slate-400 font-mono">{act.safety_margin_meters} m</td>
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

