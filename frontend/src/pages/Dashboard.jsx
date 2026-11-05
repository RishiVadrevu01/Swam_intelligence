import React from 'react';
import { 
  Car, 
  Siren, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  Zap, 
  Compass, 
  Gauge, 
  Radio, 
  AlertCircle 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Cell, 
  PieChart, 
  Pie 
} from 'recharts';

export default function Dashboard({ summary, corridorData, onNavigate }) {
  const kpis = summary?.kpis || {};
  const charts = summary?.charts || {};
  const events = summary?.recent_events || [];

  const cards = [
    {
      title: 'Total Monitored Vehicles',
      value: kpis.total_vehicles ?? 25,
      sub: 'Urban arterial corridor nodes',
      icon: Car,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      title: 'Active Emergency Vehicles',
      value: kpis.active_emergency_vehicles ?? 1,
      sub: `${kpis.emergency_destination || 'INT_5'} (Ambulance)`,
      icon: Siren,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      title: 'Swarm Participants',
      value: kpis.participating_coordination ?? 24,
      sub: 'DPSO coordinated agents',
      icon: Radio,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    },
    {
      title: 'High Trust Vehicles',
      value: kpis.high_trust_vehicles ?? 21,
      sub: 'Authenticated & consistent',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Suspicious / Anomalies',
      value: kpis.suspicious_vehicles ?? 1,
      sub: 'Isolation Forest flagged',
      icon: ShieldAlert,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      title: 'High Compliance Yielders',
      value: kpis.high_compliance_vehicles ?? 18,
      sub: 'XGBoost predicted >0.70',
      icon: CheckCircle2,
      color: 'text-teal-400',
      bg: 'bg-teal-500/10 border-teal-500/20'
    },
    {
      title: 'Corridor Status',
      value: kpis.corridor_status ?? 'ACTIVE',
      sub: 'Multi-agent green wave',
      icon: Zap,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    },
    {
      title: 'Average Corridor Delay',
      value: `${kpis.average_delay_seconds ?? 4.2}s`,
      sub: 'Travel time overhead',
      icon: Clock,
      color: 'text-violet-400',
      bg: 'bg-violet-500/10 border-violet-500/20'
    },
    {
      title: 'Establishment Latency',
      value: `${kpis.establishment_time_seconds ?? 1.84}s`,
      sub: 'DPSO convergence time',
      icon: Gauge,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    }
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border backdrop-blur-sm ${card.bg} transition-all duration-200 hover:scale-[1.01]`}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-slate-400">{card.title}</p>
                <Icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className="text-2xl font-bold tracking-tight text-white">{card.value}</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">{card.sub}</p>
            </div>
          );
        })}
      </div>

      {/* Emergency Corridor Status Banner */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center shrink-0">
            <Siren className="w-7 h-7 text-rose-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white">Emergency Vehicle EV01 Dispatch In Progress</h2>
              <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                Priority 1
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Destination: <span className="text-slate-200 font-semibold">{kpis.emergency_destination || 'Market & 2nd St (Hospital Junction)'}</span> • 
              Route: <span className="text-cyan-400 font-mono">
                {corridorData?.active_route?.route_nodes?.join(' → ') || 'INT_1 → INT_2 → INT_3 → INT_4 → INT_5'}
              </span> • 
              Speed: <span className="text-emerald-400 font-semibold">{kpis.emergency_vehicle_speed || 62.5} km/h</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigate('map')}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 transition"
          >
            Open Live Map
          </button>
          <button
            onClick={() => onNavigate('corridor')}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            Corridor Panel
          </button>
        </div>
      </div>

      {/* Charts & Visual Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trust Distribution Chart */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Vehicle Trust Profile Breakdown</h3>
              <p className="text-xs text-slate-400">Behavioural Model + Isolation Forest Anomaly Detection</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
              T(i) = w₁P + w₂C + w₃F + w₄S
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.trust_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f1f5f9' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {(charts.trust_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill || '#10b981'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Compliance Distribution Chart */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Driver Yielding Compliance Probabilities</h3>
              <p className="text-xs text-slate-400">Trained XGBoost Multi-Class Classifier</p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded border border-cyan-500/20">
              XGBoost Model
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.compliance_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f1f5f9' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {(charts.compliance_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill || '#06b6d4'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Live System Events Log */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
            <h3 className="text-sm font-semibold text-white">Real-Time Coordination & Security Event Stream</h3>
          </div>
          <span className="text-xs text-slate-400">Latest 12 Operations</span>
        </div>

        <div className="divide-y divide-slate-800/80 max-h-72 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No recent events recorded.</p>
          ) : (
            events.map((ev, i) => (
              <div key={i} className="py-2.5 flex items-start justify-between text-xs">
                <div className="flex items-start space-x-3">
                  <span className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase font-bold shrink-0 ${
                    ev.level === 'SUCCESS' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    ev.level === 'WARNING' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                    'bg-slate-800 text-slate-300 border border-slate-700'
                  }`}>
                    {ev.stage || 'EVENT'}
                  </span>
                  <span className="text-slate-300">{ev.message}</span>
                </div>
                <span className="text-slate-500 font-mono shrink-0 ml-4">{ev.formatted_time || 'Just now'}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

