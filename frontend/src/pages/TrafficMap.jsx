import React, { useState, useEffect } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Popup, 
  Polyline, 
  CircleMarker, 
  Tooltip as LeafletTooltip 
} from 'react-leaflet';
import L from 'leaflet';
import { 
  Car, 
  Siren, 
  ShieldAlert, 
  CheckCircle2, 
  Compass, 
  Navigation, 
  Filter, 
  Info, 
  Cpu, 
  ArrowRightCircle, 
  AlertTriangle 
} from 'lucide-react';

// Create custom colored Leaflet HTML markers
const createCustomIcon = (type, isEmergency, isSuspicious, complianceClass) => {
  let bgColor = '#3b82f6'; // default normal blue
  let borderColor = '#1d4ed8';
  let label = 'V';
  let pulse = '';

  if (isEmergency) {
    bgColor = '#ef4444';
    borderColor = '#b91c1c';
    label = '🚑';
    pulse = 'animate-ping opacity-75';
  } else if (isSuspicious) {
    bgColor = '#f59e0b';
    borderColor = '#d97706';
    label = '⚠';
  } else if (complianceClass === 'High') {
    bgColor = '#10b981';
    borderColor = '#047857';
    label = '✓';
  } else if (complianceClass === 'Low') {
    bgColor = '#f43f5e';
    borderColor = '#be123c';
    label = '✕';
  }

  const html = `
    <div style="position: relative; width: 28px; height: 28px;">
      ${isEmergency ? `<div class="${pulse}" style="position: absolute; width: 28px; height: 28px; border-radius: 50%; background-color: ${bgColor};"></div>` : ''}
      <div style="position: relative; width: 28px; height: 28px; border-radius: 50%; background-color: ${bgColor}; border: 2px solid #ffffff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.4);">
        ${label}
      </div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-vehicle-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14]
  });
};

export default function TrafficMap({ 
  vehicles = [], 
  emergencyVehicles = [], 
  roads = [], 
  corridorData = {}, 
  trustData = {}, 
  complianceData = {},
  dpsoActions = [],
  onSelectVehicleForTwin
}) {
  const [filter, setFilter] = useState('ALL');
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  const rawEv = (emergencyVehicles && emergencyVehicles.length > 0 ? emergencyVehicles[0] : null) || corridorData?.emergency_vehicle;
  const ev = (rawEv && rawEv.latitude != null && rawEv.longitude != null) ? rawEv : null;
  const activeRoute = corridorData?.active_route;
  const isReplanned = corridorData?.status === 'REPLANNING' || Boolean(corridorData?.replan_data);

  // Map center: Market St Corridor in SF [37.7815, -122.4150]
  const center = [37.7815, -122.4150];

  const getVehicleAction = (vid) => {
    return dpsoActions.find((a) => a.vehicle_id === vid);
  };

  const getVehicleTrust = (vid) => {
    return trustData[vid] || {};
  };

  const getVehicleCompliance = (vid) => {
    return complianceData[vid] || {};
  };

  // Filtered vehicles list
  const filteredVehicles = vehicles.filter((v) => {
    const vid = v.vehicle_id;
    const t = getVehicleTrust(vid);
    const c = getVehicleCompliance(vid);

    if (filter === 'ALL') return true;
    if (filter === 'EMERGENCY') return false;
    if (filter === 'SUSPICIOUS') return t.trust_category === 'Suspicious' || t.is_anomaly;
    if (filter === 'HIGH_COMPLIANCE') return c.compliance_class === 'High';
    if (filter === 'LOW_COMPLIANCE') return c.compliance_class === 'Low';
    if (filter === 'NORMAL') return t.trust_category !== 'Suspicious' && !t.is_anomaly;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Top Map Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900 border border-slate-800 rounded-xl">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-white">Filter Map Entities:</span>
          <div className="flex flex-wrap gap-1.5">
            {[
              { id: 'ALL', label: `All (${vehicles.length + (ev ? 1 : 0)})` },
              { id: 'EMERGENCY', label: 'Emergency EV01' },
              { id: 'NORMAL', label: 'Normal Traffic' },
              { id: 'HIGH_COMPLIANCE', label: 'High Compliance' },
              { id: 'LOW_COMPLIANCE', label: 'Low Compliance' },
              { id: 'SUSPICIOUS', label: 'Suspicious / Anomalies' }
            ].map((btn) => (
              <button
                key={btn.id}
                onClick={() => setFilter(btn.id)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                  filter === btn.id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-3 text-[11px] text-slate-400">
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block animate-ping"></span>
            <span>Emergency (EV01)</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
            <span>Yielding</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
            <span>Suspicious</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block"></span>
            <span>Non-Yielding</span>
          </span>
        </div>
      </div>

      {/* Main Map Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 h-[600px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative">
          <MapContainer
            center={center}
            zoom={15}
            style={{ width: '100%', height: '100%' }}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Road Segment Polylines */}
            {roads.map((road) => {
              if (!road || road.start_lat == null || road.start_lon == null || road.end_lat == null || road.end_lon == null) {
                return null;
              }
              const positions = [
                [road.start_lat, road.start_lon],
                [road.end_lat, road.end_lon]
              ];
              const isCongested = road.congestion_level === 'High' || road.congestion_level === 'Severe';
              const color = isCongested ? '#f43f5e' : '#475569';

              return (
                <Polyline
                  key={road.road_id}
                  positions={positions}
                  pathOptions={{
                    color: color,
                    weight: isCongested ? 5 : 4,
                    opacity: 0.7,
                    dashArray: isCongested ? '6, 6' : undefined
                  }}
                >
                  <LeafletTooltip sticky>
                    <div className="text-xs">
                      <strong>{road.name}</strong> ({road.road_id})<br />
                      Density: {road.traffic_density} veh/km • Speed: {road.average_speed} km/h<br />
                      Congestion: <span className="font-semibold">{road.congestion_level}</span>
                    </div>
                  </LeafletTooltip>
                </Polyline>
              );
            })}

            {/* Emergency Vehicle Active Corridor Route */}
            {activeRoute?.route_coordinates && activeRoute.route_coordinates.length > 1 && (
              <Polyline
                positions={activeRoute.route_coordinates}
                pathOptions={{
                  color: isReplanned ? '#f59e0b' : '#06b6d4',
                  weight: 6,
                  opacity: 0.9,
                  dashArray: isReplanned ? '8, 8' : undefined
                }}
              >
                <LeafletTooltip sticky>
                  <div className="text-xs">
                    <strong>{isReplanned ? 'Dynamic Replanned Route (Bypass)' : 'Primary Emergency Corridor'}</strong><br />
                    Total Length: {activeRoute.total_distance_meters}m • Est Time: {activeRoute.estimated_travel_time_seconds}s
                  </div>
                </LeafletTooltip>
              </Polyline>
            )}

            {/* Emergency Vehicle Marker */}
            {ev && ev.latitude != null && ev.longitude != null && filter !== 'SUSPICIOUS' && filter !== 'HIGH_COMPLIANCE' && filter !== 'LOW_COMPLIANCE' && filter !== 'NORMAL' && (
              <Marker
                position={[ev.latitude, ev.longitude]}
                icon={createCustomIcon('EMERGENCY', true, false, 'High')}
                eventHandlers={{
                  click: () => setSelectedVehicle({ ...ev, is_emergency: true })
                }}
              >
                <Popup>
                  <div className="text-xs p-1">
                    <div className="flex items-center space-x-1.5 font-bold text-rose-400">
                      <Siren className="w-4 h-4" />
                      <span>{ev.emergency_vehicle_id} ({ev.vehicle_type})</span>
                    </div>
                    <p className="mt-1 text-slate-300">
                      Destination: <strong>{ev.destination}</strong><br />
                      Speed: <strong>{ev.speed} km/h</strong> • Priority: <strong>{ev.priority_level}</strong><br />
                      Corridor Target: <strong>Lane 2 (Center)</strong>
                    </p>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Normal Vehicles Markers */}
            {filter !== 'EMERGENCY' && filteredVehicles.map((v) => {
              if (!v || v.latitude == null || v.longitude == null) return null;
              const vid = v.vehicle_id;
              const t = getVehicleTrust(vid);
              const c = getVehicleCompliance(vid);
              const isSuspicious = t.trust_category === 'Suspicious' || t.is_anomaly;

              return (
                <Marker
                  key={vid}
                  position={[v.latitude, v.longitude]}
                  icon={createCustomIcon('NORMAL', false, isSuspicious, c.compliance_class)}
                  eventHandlers={{
                    click: () => setSelectedVehicle({ ...v, is_emergency: false })
                  }}
                >
                  <Popup>
                    <div className="text-xs p-1 min-w-[190px]">
                      <div className="flex items-center justify-between font-bold border-b border-slate-700 pb-1 mb-1.5">
                        <span className="text-cyan-400">{vid}</span>
                        <span className={`px-1.5 py-0.2 rounded text-[10px] ${
                          isSuspicious ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {isSuspicious ? 'SUSPICIOUS' : 'NORMAL'}
                        </span>
                      </div>
                      <p className="text-slate-300 space-y-0.5">
                        Speed: <strong>{v.speed} km/h</strong> (Lane {v.current_lane})<br />
                        Heading: <strong>{v.heading?.toFixed(1)}°</strong><br />
                        Trust Score: <strong>{t.computed_trust_score ?? '0.85'}</strong><br />
                        Yield Probability: <strong>{c.yielding_probability ?? '0.88'}</strong>
                      </p>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>

          {/* Dynamic Replanning Overlay Alert */}
          {isReplanned && (
            <div className="absolute top-4 left-4 z-[1000] bg-amber-500/90 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs shadow-lg flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4" />
              <span>DYNAMIC REPLAN ACTIVE: Vehicle {corridorData?.failed_yielding_vehicle_id || 'V004'} Non-Compliance Handled</span>
            </div>
          )}
        </div>

        {/* Selected Vehicle Detail Side Panel */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          {selectedVehicle ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {selectedVehicle.is_emergency ? (
                      <Siren className="w-5 h-5 text-rose-400 animate-pulse" />
                    ) : (
                      <Car className="w-5 h-5 text-cyan-400" />
                    )}
                    <h3 className="font-bold text-white text-sm">
                      {selectedVehicle.emergency_vehicle_id || selectedVehicle.vehicle_id}
                    </h3>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {selectedVehicle.vehicle_type || 'Vehicle'}
                  </span>
                </div>
              </div>

              {/* Telemetry Details */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Position Coordinates:</span>
                  <span className="font-mono text-slate-200">
                    {selectedVehicle.latitude?.toFixed(4)}, {selectedVehicle.longitude?.toFixed(4)}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Telemetry Speed:</span>
                  <span className="font-semibold text-emerald-400">{selectedVehicle.speed} km/h</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Current Road Segment:</span>
                  <span className="text-cyan-400">{selectedVehicle.road_id || 'Market St Segment 1'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Current Lane:</span>
                  <span className="text-white font-semibold">Lane {selectedVehicle.current_lane || 2}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Vehicle Heading:</span>
                  <span className="text-slate-200">{selectedVehicle.heading?.toFixed(1) || 48.0}°</span>
                </div>

                {!selectedVehicle.is_emergency && (
                  <>
                    {/* Trust breakdown */}
                    <div className="mt-3 p-2.5 rounded-lg bg-slate-800/60 border border-slate-700">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-300 font-semibold">Trust Evaluation:</span>
                        <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${
                          getVehicleTrust(selectedVehicle.vehicle_id).trust_category === 'Suspicious'
                            ? 'bg-rose-500/20 text-rose-300'
                            : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {getVehicleTrust(selectedVehicle.vehicle_id).trust_category || 'High'} ({getVehicleTrust(selectedVehicle.vehicle_id).computed_trust_score || '0.88'})
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">
                        {getVehicleTrust(selectedVehicle.vehicle_id).recommended_handling || 'Accept full telemetry'}
                      </p>
                    </div>

                    {/* DPSO Action Recommendation */}
                    {getVehicleAction(selectedVehicle.vehicle_id) && (
                      <div className="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/50">
                        <div className="flex justify-between items-center text-xs text-cyan-300 font-semibold">
                          <span>DPSO Recommended Action:</span>
                          <span className="text-white font-bold">
                            {getVehicleAction(selectedVehicle.vehicle_id).action_type}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300 mt-1">
                          {getVehicleAction(selectedVehicle.vehicle_id).reason} (Target: Lane {getVehicleAction(selectedVehicle.vehicle_id).recommended_lane})
                        </p>
                      </div>
                    )}

                    <button
                      onClick={() => onSelectVehicleForTwin(selectedVehicle.vehicle_id)}
                      className="w-full mt-2 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center space-x-1.5 shadow transition"
                    >
                      <Cpu className="w-3.5 h-3.5" />
                      <span>Inspect Local Digital Twin</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-4">
              <Info className="w-8 h-8 text-slate-600 mb-2" />
              <p className="text-xs font-medium text-slate-400">Click any vehicle marker on the map to inspect its real-time telemetry, Local Digital Twin, trust score and DPSO recommended movement.</p>
            </div>
          )}

          <div className="border-t border-slate-800 pt-3 mt-4 text-[11px] text-slate-500 text-center">
            Synthetic Urban Coordinate Grid • Real-Time V2X Simulation
          </div>
        </div>
      </div>
    </div>
  );
}

