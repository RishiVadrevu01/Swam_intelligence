import React, { useState, useEffect } from 'react';
import { 
  Car, 
  Siren, 
  Gauge, 
  MapPin, 
  CheckCircle2, 
  Layers, 
  Check, 
  CornerUpRight, 
  ShieldCheck, 
  Cpu, 
  Network, 
  Play, 
  Pause, 
  RotateCcw, 
  AlertTriangle,
  ArrowUp,
  FileSpreadsheet
} from 'lucide-react';

export default function CockpitDashboard({ 
  cockpitData, 
  activeScenario, 
  onSelectScenario, 
  onTriggerReplan, 
  onResetScenario,
  loading 
}) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [pulseTick, setPulseTick] = useState(0);

  // Animation ticker for dynamic vehicle positions and radar pulses
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setPulseTick((prev) => (prev + 1) % 100);
    }, 150);
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Extract cockpit telemetry
  const isEmergency = cockpitData?.has_emergency_vehicle ?? (activeScenario !== "Scenario A: Normal Traffic" && !activeScenario.includes("Scenario A:"));
  const speed = cockpitData?.speed_kmh ?? (isEmergency ? 32 : 42);
  const distance = cockpitData?.distance_to_dest_km ?? (isEmergency ? 2.6 : 2.8);
  const congestion = cockpitData?.congestion_level ?? (isEmergency ? "Moderate" : "Low");
  const rec = cockpitData?.recommendation || {};

  // Vehicles for the 2D traffic road view
  // Coordinates in percentage: { lane: 1..5, yPercent: 0..100 }
  // Lane 1 = Leftmost shoulder, Lane 2 = Left Lane, Lane 3 = Center Lane (Corridor), Lane 4 = Right Lane, Lane 5 = Right shoulder
  const nearbyVehicles = [
    { id: 'V002', lane: 2, y: 28, color: '#38bdf8' },
    { id: 'V003', lane: 4, y: 35, color: '#38bdf8' },
    { id: 'V004', lane: 1, y: 46, color: '#38bdf8' },
    { id: 'V005', lane: 4, y: 62, color: '#38bdf8' },
    { id: 'V006', lane: 2, y: 68, color: '#38bdf8' },
    { id: 'V007', lane: 1, y: 78, color: '#38bdf8' }
  ];

  // Subtle floating motion when playing
  const floatOffset = isPlaying ? Math.sin(pulseTick * 0.15) * 2 : 0;

  return (
    <div className="w-full flex flex-col space-y-4">
      {/* 1. TOP HEADER BAR (Exact match to reference image) */}
      <header className="w-full bg-[#0a162b] border border-blue-900/60 rounded-xl px-4 py-2.5 shadow-2xl flex flex-wrap items-center justify-between gap-3 text-white">
        {/* Left branding */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600/30 border border-blue-400/40 flex items-center justify-center text-cyan-300 shadow-md shadow-blue-500/20">
            <Car className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex items-center space-x-3">
            <h1 className="font-bold text-base sm:text-lg tracking-tight text-slate-100">
              Trust-Aware Emergency Corridor Coordination System
            </h1>
            <span className="text-slate-600 font-light hidden md:inline">|</span>
          </div>
        </div>

        {/* Right Status Indicator Pills */}
        <div className="flex items-center flex-wrap gap-2 text-xs font-medium">
          {/* Local Digital Twin */}
          <div className="flex items-center space-x-2 bg-[#0d203f] border border-blue-800/60 rounded-lg px-3 py-1.5 text-slate-200">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Local Digital Twin</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/80 animate-pulse" />
          </div>

          {/* Trust & Compliance */}
          <div className="flex items-center space-x-2 bg-[#0d203f] border border-blue-800/60 rounded-lg px-3 py-1.5 text-slate-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Trust & Compliance</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/80 animate-pulse" />
          </div>

          {/* Swarm Coordination */}
          <div className="flex items-center space-x-2 bg-[#0d203f] border border-blue-800/60 rounded-lg px-3 py-1.5 text-slate-200">
            <Network className="w-3.5 h-3.5 text-indigo-400" />
            <span>Swarm Coordination</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/80 animate-pulse" />
          </div>

          {/* System Active Badge */}
          <div className="flex items-center space-x-2 bg-emerald-600/20 border border-emerald-500/50 rounded-full px-3.5 py-1 text-emerald-300 font-semibold shadow-sm shadow-emerald-900/30">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping mr-0.5" />
            <span>System Active</span>
          </div>
        </div>
      </header>

      {/* 2. SCENARIO SWITCHER & SIMULATION CONTROLS */}
      <div className="bg-[#0b172e] border border-blue-900/50 rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 shadow-md">
        <div className="flex items-center space-x-3">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
            Active Scenario:
          </span>
          <select
            value={activeScenario}
            onChange={(e) => onSelectScenario(e.target.value)}
            disabled={loading}
            aria-label="Select Traffic Scenario"
            className="bg-[#122345] text-slate-100 text-xs font-semibold rounded-lg border border-blue-700/60 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-cyan-400 cursor-pointer shadow-inner"
          >
            <option value="Scenario A: Normal Traffic">Scenario A: Normal Traffic (No Ambulance)</option>
            <option value="Scenario B: Ambulance Enters Communication Range">Scenario B: Ambulance Approaching (120m Behind)</option>
            <option value="Scenario C: Heavy Congestion">Scenario C: Heavy Congestion & High Density</option>
            <option value="Scenario D: Driver Non-Compliance">Scenario D: Driver Non-Compliance & A* Replanning</option>
            <option value="Scenario E: Unreliable Vehicle Information">Scenario E: Unreliable / Suspicious Vehicle Info</option>
            <option value="Scenario F: Combined Emergency Scenario">Scenario F: Combined Multi-Agent Corridor</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          {/* Simulation Toggle */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all ${
              isPlaying 
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20' 
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
            }`}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'Pause Sim' : 'Resume Sim'}</span>
          </button>

          {/* Trigger Dynamic Replanning */}
          <button
            onClick={onTriggerReplan}
            disabled={loading}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-rose-600/20 border border-rose-500/40 text-rose-300 hover:bg-rose-600/30 transition-all disabled:opacity-50"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>Simulate Driver Non-Compliance</span>
          </button>

          {/* Reset */}
          <button
            onClick={onResetScenario}
            disabled={loading}
            aria-label="Reset Scenario"
            className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 transition-all"
            title="Reset Scenario"
          >
            <RotateCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 3. MAIN COCKPIT VIEW: TWO EQUAL COLUMNS (50% LEFT / 50% RIGHT) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
        
        {/* ======================================================== */}
        {/* LEFT CARD (50%): LOCAL DIGITAL TWIN (TRAFFIC VIEW) */}
        {/* ======================================================== */}
        <div className="bg-[#0c1a33] border-2 border-blue-900/80 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
          {/* Card Title Banner */}
          <div className="bg-gradient-to-r from-[#0b2447] to-[#19376d] px-5 py-3 border-b border-blue-800/80 flex items-center space-x-2.5">
            <Layers className="w-5 h-5 text-cyan-300" />
            <h2 className="text-white font-bold text-base tracking-wide">
              Local Digital Twin (Traffic View)
            </h2>
          </div>

          {/* Road Visualizer Canvas */}
          <div className="relative w-full h-[480px] bg-[#0d1629] overflow-hidden flex justify-center items-center select-none">
            {/* Road Asphalt Container */}
            <div className="relative w-full max-w-[420px] h-full bg-[#111e38] border-x-4 border-slate-600/70 shadow-2xl flex">
              {/* Lane 1 */}
              <div className="flex-1 border-r border-dashed border-slate-400/30 relative h-full" />
              {/* Lane 2 */}
              <div className="flex-1 border-r border-dashed border-slate-400/40 relative h-full" />
              {/* Lane 3 (Center Corridor Lane) */}
              <div className="flex-1 border-r border-dashed border-slate-400/40 relative h-full bg-blue-950/20" />
              {/* Lane 4 */}
              <div className="flex-1 border-r border-dashed border-slate-400/40 relative h-full" />
              {/* Lane 5 */}
              <div className="flex-1 relative h-full" />

              {/* Destination Marker at Top Center */}
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center shadow-lg shadow-emerald-500/50">
                  <div className="w-3 h-3 rounded-full bg-white" />
                </div>
              </div>

              {/* Planned Route Line (Cyan Dashed Line pointing to destination) */}
              <div className="absolute left-1/2 -translate-x-1/2 top-14 bottom-[170px] w-0.5 border-l-2 border-dashed border-cyan-400 z-10 flex flex-col items-center justify-around">
                <ArrowUp className="w-4 h-4 text-cyan-300 animate-bounce -ml-[7px]" />
                <ArrowUp className="w-4 h-4 text-cyan-300/80 -ml-[7px]" />
              </div>

              {/* Surrounding Normal Vehicles (Light Blue Circular Nodes) */}
              {nearbyVehicles.map((v) => {
                // Map lane 1..5 to horizontal percentage: 10%, 30%, 50%, 70%, 90%
                const leftPercent = (v.lane - 0.5) * 20;
                return (
                  <div
                    key={v.id}
                    className="absolute z-15 -translate-x-1/2 -translate-y-1/2 transition-all duration-300"
                    style={{
                      left: `${leftPercent}%`,
                      top: `${v.y + floatOffset}%`
                    }}
                  >
                    <div className="w-7 h-7 rounded-full bg-sky-200/90 border-2 border-sky-400/80 shadow-md shadow-sky-500/30 flex items-center justify-center">
                      <div className="w-2.5 h-2.5 rounded-full bg-sky-600/70" />
                    </div>
                  </div>
                );
              })}

              {/* Your Vehicle (Ego Vehicle - Glowing Blue circle with white center and cyan ring) */}
              <div
                className="absolute left-1/2 top-[58%] -translate-x-1/2 -translate-y-1/2 z-25 transition-all duration-300"
                style={{
                  top: `${58 + floatOffset}%`
                }}
              >
                <div className="relative flex items-center justify-center">
                  {/* Outer glowing halo ring */}
                  <div className="absolute w-12 h-12 rounded-full border border-cyan-400/60 bg-cyan-400/10 animate-pulse" />
                  {/* Vehicle Body */}
                  <div className="w-8 h-8 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center shadow-xl shadow-cyan-400/40">
                    <div className="w-3 h-3 rounded-full bg-white" />
                  </div>
                </div>
              </div>

              {/* Emergency Ambulance (Rendered when Emergency Vehicle is active in communication range) */}
              {isEmergency && (
                <div
                  className="absolute left-1/2 top-[84%] -translate-x-1/2 -translate-y-1/2 z-25 transition-all duration-300"
                  style={{
                    top: `${84 + floatOffset}%`
                  }}
                >
                  <div className="relative flex items-center justify-center">
                    {/* Concentric Pulsing Red Radar Waves */}
                    <div className="absolute w-28 h-28 rounded-full border-2 border-rose-500/30 bg-rose-500/10 animate-ping pointer-events-none" />
                    <div className="absolute w-20 h-20 rounded-full border border-rose-500/50 bg-rose-500/10 animate-pulse pointer-events-none" />
                    <div className="absolute w-14 h-14 rounded-full border border-rose-400/70 pointer-events-none" />

                    {/* Ambulance Vehicle Marker */}
                    <div className="w-10 h-10 rounded-full bg-rose-600 border-2 border-white flex items-center justify-center shadow-2xl shadow-rose-600/80">
                      <Siren className="w-5 h-5 text-white animate-pulse" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* RIGHT CARDS (50%): TRIP INFO & SYSTEM RECOMMENDATION */}
        {/* ======================================================== */}
        <div className="flex flex-col space-y-5">
          
          {/* -------------------------------------------------------- */}
          {/* CARD 1: TRIP INFORMATION (Exact layout from reference image) */}
          {/* -------------------------------------------------------- */}
          <div className="bg-[#0c1a33] border-2 border-blue-900/80 rounded-2xl overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#0b2447] to-[#19376d] px-5 py-3 border-b border-blue-800/80 flex items-center space-x-2.5">
              <Gauge className="w-5 h-5 text-cyan-300" />
              <h2 className="text-white font-bold text-base tracking-wide">
                Trip Information
              </h2>
            </div>

            {/* 3 Metric Cards in a Row */}
            <div className="p-4 bg-slate-100">
              <div className="grid grid-cols-3 gap-3">
                {/* 1. Speed */}
                <div className="bg-white rounded-xl border border-slate-200 p-3.5 flex flex-col justify-between shadow-sm">
                  <div className="flex items-center space-x-2 text-slate-500 mb-2">
                    <Gauge className="w-5 h-5 text-slate-700" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Speed</span>
                  </div>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {speed} <span className="text-sm font-semibold text-slate-500">km/h</span>
                  </div>
                </div>

                {/* 2. Distance to Destination */}
                <div className="bg-white rounded-xl border border-slate-200 p-3.5 flex flex-col justify-between shadow-sm">
                  <div className="flex items-center space-x-2 text-slate-500 mb-2">
                    <MapPin className="w-5 h-5 text-sky-600" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 truncate">
                      Distance to Dest
                    </span>
                  </div>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {distance} <span className="text-sm font-semibold text-slate-500">km</span>
                  </div>
                </div>

                {/* 3. Traffic Congestion */}
                <div className="bg-white rounded-xl border border-slate-200 p-3.5 flex flex-col justify-between shadow-sm">
                  <div className="flex items-center space-x-2 text-slate-500 mb-1">
                    {/* Realistic Traffic Light Graphic */}
                    <div className="w-4 h-9 bg-slate-900 rounded-md p-0.5 flex flex-col justify-between items-center shadow-inner">
                      <div className={`w-2.5 h-2.5 rounded-full ${congestion === 'High' ? 'bg-rose-500 shadow-sm shadow-rose-500' : 'bg-rose-950'}`} />
                      <div className={`w-2.5 h-2.5 rounded-full ${congestion === 'Moderate' ? 'bg-amber-400 shadow-sm shadow-amber-400' : 'bg-amber-950'}`} />
                      <div className={`w-2.5 h-2.5 rounded-full ${congestion === 'Low' ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-emerald-950'}`} />
                    </div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 truncate">
                      Congestion
                    </span>
                  </div>

                  <div className="mt-1">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-extrabold text-white shadow-sm ${
                      congestion === 'Low' 
                        ? 'bg-emerald-600' 
                        : congestion === 'Moderate' 
                          ? 'bg-amber-500' 
                          : 'bg-rose-600'
                    }`}>
                      {congestion}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* -------------------------------------------------------- */}
          {/* CARD 2: SYSTEM RECOMMENDATION (Exact states from reference image) */}
          {/* -------------------------------------------------------- */}
          <div className="bg-[#0c1a33] border-2 border-blue-900/80 rounded-2xl overflow-hidden shadow-2xl flex-1 flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#0b2447] to-[#19376d] px-5 py-3 border-b border-blue-800/80 flex items-center space-x-2.5">
              <CornerUpRight className="w-5 h-5 text-cyan-300" />
              <h2 className="text-white font-bold text-base tracking-wide">
                System Recommendation
              </h2>
            </div>

            {/* Content area */}
            <div className="p-5 bg-slate-100 flex-1 flex flex-col justify-center">
              {!isEmergency ? (
                /* ======================================================== */
                /* STATE 1: NORMAL TRAFFIC (No Emergency Vehicles Nearby)   */
                /* ======================================================== */
                <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-center justify-between shadow-sm">
                  <div className="flex items-center space-x-4">
                    {/* Green Car Icon */}
                    <div className="w-14 h-14 rounded-full bg-emerald-100 border border-emerald-300 flex items-center justify-center shrink-0">
                      <Car className="w-8 h-8 text-emerald-600" />
                    </div>
                    {/* Guidance Text */}
                    <div>
                      <h3 className="text-lg sm:text-xl font-bold text-slate-900">
                        No Emergency Vehicles Nearby
                      </h3>
                      <p className="text-sm font-medium text-slate-600 mt-1">
                        Continue on the planned route to the destination.
                      </p>
                    </div>
                  </div>

                  {/* Big Green Checkmark on the right */}
                  <div className="shrink-0 ml-4">
                    <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                  </div>
                </div>
              ) : (
                /* ======================================================== */
                /* STATE 2: EMERGENCY VEHICLE DETECTED                      */
                /* ======================================================== */
                <div className="flex flex-col space-y-3">
                  {/* Emergency Alert Banner */}
                  <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-center justify-between shadow-sm">
                    <div className="flex items-center space-x-3.5">
                      <div className="w-12 h-12 rounded-full bg-rose-100 border border-rose-300 flex items-center justify-center shrink-0">
                        <Siren className="w-7 h-7 text-rose-600 animate-pulse" />
                      </div>
                      <div>
                        <h3 className="text-base sm:text-lg font-bold text-rose-600">
                          Emergency Vehicle Detected
                        </h3>
                        <p className="text-xs sm:text-sm font-semibold text-slate-700 mt-0.5">
                          1 vehicle (Ambulance) <span className="text-rose-600 font-bold">behind</span> at 120 m
                        </p>
                      </div>
                    </div>

                    {/* Red Pill Distance Badge */}
                    <div className="shrink-0 bg-rose-600 text-white font-bold text-xs sm:text-sm px-3.5 py-1.5 rounded-full flex items-center space-x-1 shadow-md shadow-rose-600/30">
                      <MapPin className="w-4 h-4" />
                      <span>120 m</span>
                    </div>
                  </div>

                  {/* Action Guidance & Checklist Box */}
                  <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                    <div className="flex items-center space-x-3.5">
                      <div className="w-12 h-12 rounded-full bg-emerald-100 border border-emerald-300 flex items-center justify-center shrink-0">
                        <CornerUpRight className="w-7 h-7 text-emerald-600" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                          Recommended Movement
                        </div>
                        <div className="text-lg sm:text-xl font-extrabold text-emerald-700">
                          {rec.movement || "Move to the Right Lane"}
                        </div>
                      </div>
                    </div>

                    {/* Instructions Checklist */}
                    <div className="flex flex-col space-y-1.5 text-xs font-semibold text-slate-700 md:border-l md:border-emerald-200 md:pl-5">
                      <div className="flex items-center space-x-2">
                        <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>Give way and keep the lane clear.</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>Reduce speed smoothly.</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>Maintain a safe distance (≥ 50 m).</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
