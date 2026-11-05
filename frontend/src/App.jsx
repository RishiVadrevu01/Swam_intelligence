import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import TrafficMap from './pages/TrafficMap';
import DigitalTwin from './pages/DigitalTwin';
import SecurityTrust from './pages/SecurityTrust';
import PredictionCentre from './pages/PredictionCentre';
import SwarmCoordination from './pages/SwarmCoordination';
import EmergencyCorridor from './pages/EmergencyCorridor';
import api from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeScenario, setActiveScenario] = useState('Scenario A: Normal Emergency Corridor');
  const [loading, setLoading] = useState(false);
  const [selectedVehicleForTwin, setSelectedVehicleForTwin] = useState('V001');

  // Backend state stores
  const [summary, setSummary] = useState(null);
  const [corridorData, setCorridorData] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [emergencyVehicles, setEmergencyVehicles] = useState([]);
  const [roads, setRoads] = useState([]);
  const [trustMap, setTrustMap] = useState({});
  const [predictionData, setPredictionData] = useState({});
  const [dpsoData, setDpsoData] = useState({});

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [
        summaryRes,
        corridorRes,
        vehiclesRes,
        evRes,
        roadsRes,
        trustRes,
        predRes,
        dpsoRes
      ] = await Promise.all([
        api.getDashboardSummary(),
        api.getCorridorStatus(),
        api.getVehicles(),
        api.getEmergencyVehicles(),
        api.getRoads(),
        api.getVehicleTrust(),
        api.getPredictionResults(),
        api.getCoordinationResults().catch(() => ({ data: { data: {} } }))
      ]);

      setSummary(summaryRes.data);
      setCorridorData(corridorRes.data.data);
      setVehicles(vehiclesRes.data.data || []);
      setEmergencyVehicles(evRes.data.data || []);
      setRoads(roadsRes.data.data || []);

      // Build trust map
      const tMap = {};
      (trustRes.data.data || []).forEach((t) => {
        tMap[t.vehicle_id] = t;
      });
      setTrustMap(tMap);

      setPredictionData(predRes.data);
      setDpsoData(dpsoRes.data.data || {});
    } catch (err) {
      console.error('Failed to fetch full application state:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectScenario = async (scenarioName) => {
    setLoading(true);
    try {
      await api.generateScenario(scenarioName);
      setActiveScenario(scenarioName);
      await fetchAllData();
    } catch (err) {
      console.error('Failed to change scenario:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResetScenario = async () => {
    await handleSelectScenario(activeScenario);
  };

  const handleTriggerReplan = async (vehicleId = 'V004') => {
    setLoading(true);
    try {
      await api.replanCorridor(vehicleId);
      await fetchAllData();
    } catch (err) {
      console.error('Failed to trigger replan:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectTwinFromMap = (vehicleId) => {
    setSelectedVehicleForTwin(vehicleId);
    setActiveTab('digital-twins');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeScenario={activeScenario}
        onSelectScenario={handleSelectScenario}
        corridorStatus={corridorData?.status}
        onTriggerReplan={() => handleTriggerReplan('V004')}
        onResetScenario={handleResetScenario}
        loading={loading}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <Dashboard
            summary={summary}
            corridorData={corridorData}
            onNavigate={setActiveTab}
          />
        )}

        {activeTab === 'map' && (
          <TrafficMap
            vehicles={vehicles}
            emergencyVehicles={emergencyVehicles}
            roads={roads}
            corridorData={corridorData}
            trustData={trustMap}
            complianceData={predictionData?.compliance_predictions || {}}
            dpsoActions={dpsoData?.recommended_actions || []}
            onSelectVehicleForTwin={handleInspectTwinFromMap}
          />
        )}

        {activeTab === 'digital-twins' && (
          <DigitalTwin
            initialVehicleId={selectedVehicleForTwin}
            vehicles={vehicles}
          />
        )}

        {activeTab === 'security-trust' && (
          <SecurityTrust
            trustData={trustMap}
            vehicles={vehicles}
          />
        )}

        {activeTab === 'predictions' && (
          <PredictionCentre
            predictionData={predictionData}
            vehicles={vehicles}
            trajectoryData={predictionData?.trajectory_predictions || {}}
          />
        )}

        {activeTab === 'swarm' && (
          <SwarmCoordination
            dpsoData={dpsoData}
            onRefreshDPSO={(newData) => setDpsoData(newData)}
          />
        )}

        {activeTab === 'corridor' && (
          <EmergencyCorridor
            corridorData={corridorData}
            onRefreshCorridor={(newData) => setCorridorData(newData)}
            onTriggerReplan={handleTriggerReplan}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        Decentralised Emergency Vehicle Corridor Coordination Framework • FastAPI + React + DPSO + A* + PyTorch LSTM + XGBoost
      </footer>
    </div>
  );
}

