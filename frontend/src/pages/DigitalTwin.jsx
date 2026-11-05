import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Radio, 
  Compass, 
  Clock, 
  ShieldCheck, 
  ShieldAlert, 
  History, 
  MapPin, 
  Gauge, 
  ArrowRight, 
  AlertCircle 
} from 'lucide-react';
import api from '../services/api';

export default function DigitalTwin({ initialVehicleId = 'V001', vehicles = [] }) {
  const [selectedVid, setSelectedVid] = useState(initialVehicleId);
  const [twinData, setTwinData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialVehicleId) {
      setSelectedVid(initialVehicleId);
    }
  }, [initialVehicleId]);

  useEffect(() => {
    fetchTwin(selectedVid);
  }, [selectedVid]);

  const fetchTwin = async (vid) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDigitalTwin(vid);
      setTwinData(res.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load Local Digital Twin');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Selector & Twin Status Banner */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
            <Cpu className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Local Digital Twin (LDT) Inspector</h2>
            <p className="text-xs text-slate-400">
              Each vehicle maintains an isolated onboard world model integrating trust-weighted V2X beacons.
            </p>
          </div>
        </div>

        {/* Vehicle Selector */}
        <div className="flex items-center space-x-2">
          <label className="text-xs font-semibold text-slate-300">Select Vehicle Agent:</label>
          <select
            value={selectedVid}
            onChange={(e) => setSelectedVid(e.target.value)}
            className="bg-slate-800 text-slate-200 text-xs rounded-md border border-slate-700 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
          >
            {vehicles.map((v) => (
              <option key={v.vehicle_id} value={v.vehicle_id}>
                {v.vehicle_id} ({v.vehicle_type || 'Vehicle'} - Lane {v.current_lane})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-400 text-xs">
          Loading Local Digital Twin instance for {selectedVid}...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {twinData && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Column 1: Ego Vehicle Telemetry & Perception */}
          <div className="space-y-4">
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-bold text-white uppercase tracking-wider">Ego Telemetry State</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  twinData.is_stale ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                }`}>
                  {twinData.is_stale ? 'STALE TELEMETRY' : 'REAL-TIME ACTIVE'}
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Node Identifier:</span>
                  <span className="font-bold text-indigo-400 font-mono">{twinData.vehicle_id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Position (Lat, Lon):</span>
                  <span className="font-mono text-slate-200">
                    {twinData.own_position?.latitude?.toFixed(5)}, {twinData.own_position?.longitude?.toFixed(5)}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Current Velocity:</span>
                  <span className="font-semibold text-emerald-400">{twinData.own_speed} km/h</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Current Road Segment:</span>
                  <span className="text-cyan-400">{twinData.road_id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Lateral Lane Occupancy:</span>
                  <span className="font-bold text-white">Lane {twinData.own_lane}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Compass Heading:</span>
                  <span className="text-slate-200">{twinData.own_heading?.toFixed(1)}°</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Distance to Ambulance:</span>
                  <span className="font-bold text-rose-400">
                    {twinData.emergency_vehicle_distance ? `${twinData.emergency_vehicle_distance} meters` : 'Out of range'}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Last Telemetry Timestamp:</span>
                  <span className="font-mono text-slate-400 text-[11px]">
                    {new Date(twinData.last_update_timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Historical Snapshots */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center space-x-2">
                  <History className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-white">Digital Twin State History</span>
                </div>
                <span className="text-[10px] text-slate-500">{twinData.history_count} snapshots</span>
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {(twinData.recent_history || []).length === 0 ? (
                  <p className="text-xs text-slate-500 text-center py-2">No historical states yet.</p>
                ) : (
                  twinData.recent_history.map((snap, i) => (
                    <div key={i} className="p-2 rounded bg-slate-800/50 text-[11px] flex justify-between items-center">
                      <div>
                        <span className="text-slate-300 font-mono">Lane {snap.lane} • {snap.speed} km/h</span>
                        <div className="text-[10px] text-slate-500">
                          EV Dist: {snap.ev_distance ? `${snap.ev_distance.toFixed(1)}m` : 'N/A'} • {snap.nearby_count} neighbors
                        </div>
                      </div>
                      <span className="text-slate-500 font-mono text-[10px]">
                        {new Date(snap.timestamp * 1000).toLocaleTimeString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Column 2 & 3: Localized Neighbor Perception Table */}
          <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Localized Neighbor Vehicles ({twinData.nearby_vehicles?.length || 0})
                </h3>
                <p className="text-xs text-slate-400">
                  Perceived through V2V DSRC/C-V2X broadcast range (&lt;450m), filtered by evaluated trust.
                </p>
              </div>
              <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded border border-indigo-500/20">
                Range: 450m
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                    <th className="py-2.5 px-3">Vehicle ID</th>
                    <th className="py-2.5 px-3">Distance</th>
                    <th className="py-2.5 px-3">Relative Speed</th>
                    <th className="py-2.5 px-3">Lane</th>
                    <th className="py-2.5 px-3">Trust Score</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(twinData.nearby_vehicles || []).length === 0 ? (
                    <tr>
                      <td colSpan="6" className="py-6 text-center text-slate-500">
                        No neighbor vehicles within current V2X communication radius.
                      </td>
                    </tr>
                  ) : (
                    twinData.nearby_vehicles.map((n) => (
                      <tr key={n.vehicle_id} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">{n.vehicle_id}</td>
                        <td className="py-2.5 px-3 text-slate-200">{n.distance_meters} m</td>
                        <td className="py-2.5 px-3">
                          <span className={n.relative_speed > 0 ? 'text-emerald-400' : 'text-slate-300'}>
                            {n.relative_speed > 0 ? `+${n.relative_speed}` : n.relative_speed} km/h
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 font-semibold">Lane {n.lane}</td>
                        <td className="py-2.5 px-3">
                          <span className="font-mono font-semibold text-white">{n.trust_score}</span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            n.is_trusted
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}>
                            {n.is_trusted ? 'TRUSTED' : 'QUARANTINED'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Local Prediction Sub-panel */}
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                <Radio className="w-3.5 h-3.5 text-cyan-400" />
                <span>Onboard Predicted Trajectory Coordinates (5 Future Steps):</span>
              </h4>
              <div className="grid grid-cols-5 gap-2">
                {([1, 2, 3, 4, 5]).map((step) => {
                  const pts = twinData.predicted_trajectories?.[selectedVid];
                  const pt = pts?.[step - 1];
                  return (
                    <div key={step} className="p-2 bg-slate-800/40 rounded border border-slate-800 text-[11px] text-center">
                      <div className="text-slate-500 text-[10px]">t + {step}s</div>
                      <div className="font-mono text-cyan-300 mt-1">
                        {pt ? `${pt.latitude?.toFixed(4)}, ${pt.longitude?.toFixed(4)}` : `Step ${step}`}
                      </div>
                      <div className="text-[10px] text-emerald-400 mt-0.5">
                        {pt?.confidence ? `${Math.round(pt.confidence * 100)}% conf` : 'LSTM model'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

