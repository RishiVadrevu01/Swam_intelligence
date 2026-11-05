import React, { useState } from 'react';
import { 
  Siren, 
  MapPin, 
  Navigation, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  Clock, 
  Compass, 
  Gauge, 
  Route 
} from 'lucide-react';
import api from '../services/api';

export default function EmergencyCorridor({ 
  corridorData = {}, 
  onRefreshCorridor, 
  onTriggerReplan 
}) {
  const [loading, setLoading] = useState(false);
  const [selectedFailedVid, setSelectedFailedVid] = useState('V004');

  const ev = corridorData?.emergency_vehicle || {};
  const activeRoute = corridorData?.active_route || {};
  const originalRoute = corridorData?.original_route || {};
  const replanData = corridorData?.replan_data;
  const isReplanned = corridorData?.status === 'REPLANNING' || Boolean(replanData);

  const handleFullCycle = async () => {
    setLoading(true);
    try {
      const res = await api.initializeCorridor();
      if (onRefreshCorridor) onRefreshCorridor(res.data.data);
    } catch (err) {
      console.error('Failed to trigger corridor cycle:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReplanClick = () => {
    if (onTriggerReplan) {
      onTriggerReplan(selectedFailedVid);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Primary Actions */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center">
            <Siren className="w-6 h-6 text-rose-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-white">Emergency Vehicle Corridor Operations Centre</h2>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                corridorData?.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                corridorData?.status === 'REPLANNING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse' :
                'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
              }`}>
                {corridorData?.status || 'ACTIVE'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Coordinated clearance through distributed DPSO swarm movements and dynamic A* graph routing.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleFullCycle}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Execute Coordination Cycle</span>
          </button>
        </div>
      </div>

      {/* Corridor Metrics Overview Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Yielding Vehicles</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {corridorData?.yielding_vehicles_count ?? 18} Vehicles
          </div>
          <span className="text-[11px] text-slate-400">Vacating Center Corridor</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Non-Yielding Blockages</span>
          <div className="text-2xl font-bold text-rose-400 mt-1">
            {corridorData?.non_yielding_vehicles_count ?? 2} Vehicles
          </div>
          <span className="text-[11px] text-rose-300">Requires Dynamic Replan</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Total Route Distance</span>
          <div className="text-2xl font-bold text-white mt-1">
            {activeRoute?.total_distance_meters ?? 2000} m
          </div>
          <span className="text-[11px] text-cyan-400">{activeRoute?.route_nodes?.length ?? 5} Intersection Waypoints</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Est. EV Transit Time</span>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {activeRoute?.estimated_travel_time_seconds ?? 115.0} s
          </div>
          <span className="text-[11px] text-emerald-400">A* Optimal Free-Flow</span>
        </div>
      </div>

      {/* Dynamic Replanning Interactive Simulator Panel */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Dynamic Replanning & Non-Compliance Simulator</h3>
              <p className="text-xs text-slate-400">
                Simulate a non-yielding driver refusing to vacate Market St, triggering real-time A* re-routing via Mission Bypass.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedFailedVid}
              onChange={(e) => setSelectedFailedVid(e.target.value)}
              className="bg-slate-800 text-slate-200 text-xs rounded-lg border border-slate-700 px-3 py-1.5 focus:outline-none"
            >
              <option value="V004">Vehicle V004 (Market St Core)</option>
              <option value="V008">Vehicle V008 (Market St Approach)</option>
              <option value="V012">Vehicle V012 (Hospital Ramp)</option>
            </select>

            <button
              onClick={handleReplanClick}
              disabled={loading}
              className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition shadow disabled:opacity-50"
            >
              Simulate Failure & Replan
            </button>
          </div>
        </div>

        {/* Dynamic Replanning Details when active */}
        {isReplanned && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs space-y-2">
            <div className="flex items-center justify-between font-bold text-amber-300">
              <span className="flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>DYNAMIC REPLANNING EXECUTED SUCCESSFULLY</span>
              </span>
              <span className="font-mono text-[11px] bg-amber-500/20 px-2 py-0.5 rounded">
                Travel Time Delta: {replanData?.travel_time_delta_seconds ?? '+14.2'}s
              </span>
            </div>
            <p className="text-slate-300">
              {replanData?.replanning_reason || `Vehicle ${corridorData?.failed_yielding_vehicle_id || 'V004'} failed to yield on segment ROAD_02; emergency corridor dynamically redirected via Mission Bypass.`}
            </p>
          </div>
        )}

        {/* Original Route vs Replanned Route Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Original Plan */}
          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300">Original Planned Corridor</span>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">Primary Arterial</span>
            </div>
            <div className="text-xs font-mono text-white py-1">
              {originalRoute?.route_nodes?.join(' → ') || 'INT_1 → INT_2 → INT_3 → INT_4 → INT_5'}
            </div>
            <div className="text-[11px] text-slate-400 flex justify-between pt-1 border-t border-slate-700/60">
              <span>Distance: {originalRoute?.total_distance_meters || 2000}m</span>
              <span>Travel Time: {originalRoute?.estimated_travel_time_seconds || 115}s</span>
            </div>
          </div>

          {/* Current Active Plan */}
          <div className={`p-4 rounded-xl border space-y-2 ${
            isReplanned 
              ? 'bg-amber-950/20 border-amber-800/50' 
              : 'bg-emerald-950/20 border-emerald-800/50'
          }`}>
            <div className="flex items-center justify-between">
              <span className={`text-xs font-bold ${isReplanned ? 'text-amber-400' : 'text-emerald-400'}`}>
                {isReplanned ? 'Active Replanned Bypass Corridor' : 'Active Current Corridor'}
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                isReplanned ? 'text-amber-300 bg-amber-500/20' : 'text-emerald-300 bg-emerald-500/20'
              }`}>
                {isReplanned ? 'Bypass Active' : 'Optimal'}
              </span>
            </div>
            <div className="text-xs font-mono text-white py-1">
              {activeRoute?.route_nodes?.join(' → ') || 'INT_1 → INT_2 → INT_3 → INT_4 → INT_5'}
            </div>
            <div className="text-[11px] text-slate-400 flex justify-between pt-1 border-t border-slate-700/60">
              <span>Distance: {activeRoute?.total_distance_meters || 2000}m</span>
              <span>Travel Time: {activeRoute?.estimated_travel_time_seconds || 115}s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

