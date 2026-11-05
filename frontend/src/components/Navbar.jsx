import React from 'react';
import { 
  Siren, 
  Map, 
  Cpu, 
  ShieldCheck, 
  BrainCircuit, 
  Network, 
  Activity, 
  RefreshCw, 
  AlertTriangle,
  RotateCcw,
  Gauge,
  FileSpreadsheet
} from 'lucide-react';

export const SCENARIOS = [
  "Scenario A: Normal Traffic",
  "Scenario B: Ambulance Enters Communication Range",
  "Scenario C: Heavy Congestion",
  "Scenario D: Driver Non-Compliance",
  "Scenario E: Unreliable Vehicle Information",
  "Scenario F: Combined Emergency Scenario"
];

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  activeScenario, 
  onSelectScenario, 
  corridorStatus, 
  onTriggerReplan, 
  onResetScenario,
  loading 
}) {
  const navItems = [
    { id: 'cockpit', label: 'Cockpit View (Reference)', icon: Gauge },
    { id: 'dashboard', label: 'Executive Overview', icon: Activity },
    { id: 'map', label: 'Live Traffic Map', icon: Map },
    { id: 'digital-twins', label: 'Local Digital Twins', icon: Cpu },
    { id: 'security-trust', label: 'Security & Trust', icon: ShieldCheck },
    { id: 'predictions', label: 'AI Predictions', icon: BrainCircuit },
    { id: 'swarm', label: 'Swarm DPSO', icon: Network },
    { id: 'corridor', label: 'Corridor Operations', icon: Siren },
    { id: 'evaluation', label: 'Research Evaluation', icon: FileSpreadsheet },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'REPLANNING':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse';
      case 'COORDINATING':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur border-b border-slate-800 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Header Row */}
        <div className="flex items-center justify-between h-16 border-b border-slate-800/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-rose-900/20">
              <Siren className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">CORRIDOR-X</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  V2X Swarm v1.0
                </span>
                <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${getStatusColor(corridorStatus)}`}>
                  {corridorStatus || 'INITIALIZING'}
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Decentralised Emergency Vehicle Coordination • Local Digital Twins • DPSO & A*
              </p>
            </div>
          </div>

          {/* Controls: Scenario Selector & Quick Actions */}
          <div className="flex items-center space-x-3">
            <div className="relative">
              <select
                value={activeScenario}
                onChange={(e) => onSelectScenario(e.target.value)}
                disabled={loading}
                aria-label="Select Traffic Scenario"
                className="bg-slate-800 text-slate-200 text-xs rounded-md border border-slate-700 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 pr-8 cursor-pointer disabled:opacity-50"
              >
                {SCENARIOS.map((sc) => (
                  <option key={sc} value={sc}>
                    {sc}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={onResetScenario}
              disabled={loading}
              title="Reset Scenario to Initial Seed"
              className="px-2.5 py-1.5 rounded-md bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700 text-xs flex items-center space-x-1 transition disabled:opacity-50"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden md:inline">Reset</span>
            </button>

            <button
              onClick={onTriggerReplan}
              disabled={loading}
              className="px-3 py-1.5 rounded-md bg-rose-600/20 text-rose-300 hover:bg-rose-600 hover:text-white border border-rose-500/40 text-xs font-medium flex items-center space-x-1.5 transition shadow-sm disabled:opacity-50"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              <span>Simulate Replan</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs Row */}
        <div className="flex space-x-1 overflow-x-auto py-2 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-all duration-150 ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}

