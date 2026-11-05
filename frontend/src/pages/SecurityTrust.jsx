import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Key, 
  Lock, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  FileText, 
  Search 
} from 'lucide-react';
import api from '../services/api';

export default function SecurityTrust({ trustData = {}, vehicles = [] }) {
  const [securityEvents, setSecurityEvents] = useState([]);
  const [keys, setKeys] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSecurityData();
  }, []);

  const fetchSecurityData = async () => {
    setLoading(true);
    try {
      const [eventsRes, keysRes] = await Promise.all([
        api.getSecurityEvents(),
        api.getSecurityKeys()
      ]);
      setSecurityEvents(eventsRes.data.data || []);
      setKeys(keysRes.data.data || []);
    } catch (err) {
      console.error('Failed to load security events:', err);
    } finally {
      setLoading(false);
    }
  };

  const trustList = Object.values(trustData);
  const anomaliesList = trustList.filter((t) => t.is_anomaly || t.trust_category === 'Suspicious');

  const filteredTrustList = trustList.filter((t) => 
    t.vehicle_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.trust_category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <Lock className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">V2X Cryptographic Security & Behavioural Trust Intelligence</h2>
            <p className="text-xs text-slate-400">
              ECDSA (NIST P-256) signature verification, sequence replay prevention, and Isolation Forest anomaly detection.
            </p>
          </div>
        </div>

        <button
          onClick={fetchSecurityData}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center space-x-2 transition self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Audit Logs</span>
        </button>
      </div>

      {/* Security Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Public Key Infrastructure</span>
          <div className="text-xl font-bold text-white mt-1">{keys.length} Registered Nodes</div>
          <span className="text-[11px] text-emerald-400">ECDSA SECP256R1</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Replay Defense</span>
          <div className="text-xl font-bold text-cyan-400 mt-1">Active Monitored</div>
          <span className="text-[11px] text-slate-400">Sequence gap &lt; 100</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Isolation Forest Anomalies</span>
          <div className="text-xl font-bold text-rose-400 mt-1">{anomaliesList.length} Flagged</div>
          <span className="text-[11px] text-rose-300">Kinematic violations</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Trust Formula Weights</span>
          <div className="text-xs font-mono text-indigo-400 mt-1.5">w₁=0.35, w₂=0.25, w₃=0.20, w₄=0.20</div>
          <span className="text-[10px] text-slate-500">Plausibility + Consistency + Freshness + Sensor</span>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Vehicle Trust Scores & Anomaly Classifications */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">Evaluated Vehicle Trust Directory</h3>
              <p className="text-xs text-slate-400">Multi-component behavioural trust T(i) and Isolation Forest scores</p>
            </div>
            <div className="relative">
              <input
                type="text"
                placeholder="Search vehicle or status..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-slate-800 text-slate-200 text-xs rounded-lg border border-slate-700 pl-8 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <div className="overflow-x-auto max-h-[460px]">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                <tr>
                  <th className="py-2.5 px-3">Vehicle</th>
                  <th className="py-2.5 px-3">Trust Score</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3">Components (P/C/F/S)</th>
                  <th className="py-2.5 px-3">Anomaly Status</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTrustList.map((t) => {
                  const isSuspicious = t.trust_category === 'Suspicious' || t.is_anomaly;
                  return (
                    <tr key={t.vehicle_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">{t.vehicle_id}</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-white">
                        {t.computed_trust_score}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          t.trust_category === 'High' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          t.trust_category === 'Medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}>
                          {t.trust_category}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">
                        {t.components?.position_consistency} / {t.components?.movement_consistency} / {t.components?.message_freshness} / {t.components?.sensor_consistency}
                      </td>
                      <td className="py-2.5 px-3">
                        {t.is_anomaly ? (
                          <span className="flex items-center space-x-1 text-rose-400 font-semibold text-[11px]">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Isolation Forest Flagged</span>
                          </span>
                        ) : (
                          <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Normal Kinematics</span>
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <button
                          onClick={() => setSelectedVehicle(t)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-semibold border border-slate-700 transition"
                        >
                          Audit
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: V2X Cryptographic Verification Events */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">V2X Verification Stream</h3>
              <p className="text-xs text-slate-400">ECDSA signatures, timestamps & replays</p>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Live Audit
            </span>
          </div>

          <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
            {securityEvents.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No security verification events recorded yet.</p>
            ) : (
              securityEvents.map((ev, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-800/50 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-cyan-400">{ev.vehicle_id}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      ev.status === 'SUCCESS' || ev.status === 'ACCEPTED'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {ev.status}
                    </span>
                  </div>
                  <div className="text-slate-300 text-[11px] font-medium">{ev.event_type}</div>
                  <p className="text-slate-400 text-[10px]">{ev.details}</p>
                  <div className="text-[9px] text-slate-500 font-mono text-right">
                    {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Vehicle Investigation Modal */}
      {selectedVehicle && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                <h3 className="font-bold text-white text-sm">Security & Trust Audit: {selectedVehicle.vehicle_id}</h3>
              </div>
              <button
                onClick={() => setSelectedVehicle(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-slate-800"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-slate-400">Calculated Trust Score:</span>
                <div className="text-2xl font-bold text-white font-mono">{selectedVehicle.computed_trust_score}</div>
                <div className="text-slate-400 text-[11px]">
                  Classification: <span className="text-white font-semibold">{selectedVehicle.trust_category}</span> • 
                  Handling: <span className="text-cyan-400 font-semibold">{selectedVehicle.recommended_handling}</span>
                </div>
              </div>

              {selectedVehicle.anomaly_reasons && selectedVehicle.anomaly_reasons.length > 0 && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 space-y-1">
                  <div className="flex items-center space-x-1.5 text-rose-300 font-semibold">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Isolation Forest Violation Reasons:</span>
                  </div>
                  <ul className="list-disc list-inside text-rose-300/80 space-y-0.5 text-[11px] pt-1">
                    {selectedVehicle.anomaly_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
                  <span className="text-slate-400">Position Plausibility (P):</span>
                  <div className="text-white font-mono font-bold mt-0.5">{selectedVehicle.components?.position_consistency}</div>
                </div>
                <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
                  <span className="text-slate-400">Movement Consistency (C):</span>
                  <div className="text-white font-mono font-bold mt-0.5">{selectedVehicle.components?.movement_consistency}</div>
                </div>
                <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
                  <span className="text-slate-400">Message Freshness (F):</span>
                  <div className="text-white font-mono font-bold mt-0.5">{selectedVehicle.components?.message_freshness}</div>
                </div>
                <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
                  <span className="text-slate-400">Sensor Consistency (S):</span>
                  <div className="text-white font-mono font-bold mt-0.5">{selectedVehicle.components?.sensor_consistency}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

