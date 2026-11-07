import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const api = {
  // Dashboard
  getDashboardSummary: () => client.get('/dashboard/summary'),
  getCockpit: () => client.get('/dashboard/cockpit'),
  getDashboardEvents: () => client.get('/dashboard/events'),
  getDashboardMetrics: () => client.get('/dashboard/metrics'),

  // Data & Scenarios
  getVehicles: () => client.get('/data/vehicles'),
  getEmergencyVehicles: () => client.get('/data/emergency-vehicles'),
  getTraffic: () => client.get('/data/traffic'),
  getRoads: () => client.get('/data/roads'),
  generateScenario: (scenario, vehicle_count = 25, seed = 42) =>
    client.post('/data/generate-scenario', { scenario, vehicle_count, seed }),

  // Security & V2X
  signMessage: (payload) => client.post('/security/sign-message', payload),
  verifyMessage: (message) => client.post('/security/verify-message', { message }),
  getSecurityEvents: () => client.get('/security/events'),
  getSecurityKeys: () => client.get('/security/keys'),

  // Digital Twins
  getAllDigitalTwins: () => client.get('/digital-twins'),
  getDigitalTwin: (vehicleId) => client.get(`/digital-twins/${vehicleId}`),
  updateDigitalTwin: (telemetry) => client.post('/digital-twins/update', telemetry),

  // Trust & Anomalies
  getVehicleTrust: () => client.get('/trust/vehicles'),
  getAnomalies: () => client.get('/trust/anomalies'),
  evaluateTrust: (payload) => client.post('/trust/evaluate', payload),

  // AI Prediction
  getPredictionResults: () => client.get('/prediction/results'),
  predictTrajectory: (vehicleId, steps = 5) =>
    client.post('/prediction/trajectory', { vehicle_id: vehicleId, steps }),
  predictCompliance: (payload) => client.post('/prediction/compliance', payload),

  // DPSO Swarm Coordination
  executeCoordination: (config) => client.post('/coordination/execute', config || {}),
  getCoordinationResults: () => client.get('/coordination/results'),
  getCoordinationHistory: () => client.get('/coordination/history'),

  // Routing & Dynamic Replanning
  planRoute: (startNode, destinationNode, blockedRoads = []) =>
    client.post('/routing/plan', { start_node: startNode, destination_node: destinationNode, blocked_roads: blockedRoads }),
  triggerRouteReplan: (failedVehicleId, blockedRoadId) =>
    client.post('/routing/replan', { failed_vehicle_id: failedVehicleId, blocked_road_id: blockedRoadId }),

  // Corridor Management
  initializeCorridor: () => client.post('/corridor/initialize'),
  updateCorridor: () => client.post('/corridor/update'),
  replanCorridor: (vehicleId = null) => client.post('/corridor/replan', { vehicle_id: vehicleId }),
  getCorridorStatus: () => client.get('/corridor/status'),

  // Research Evaluation & Benchmarks
  getEvaluationMetrics: () => client.get('/evaluation/metrics'),
  downloadEvaluationCsv: () => client.get('/evaluation/download-csv', { responseType: 'blob' }),

  // Decentralized Vehicle Agents
  getDecentralizedAgents: () => client.get('/agents'),
  getAgentDetail: (vehicleId) => client.get(`/agents/${vehicleId}`),
  stepAgents: (dt = 1.0) => client.post('/agents/step', { dt }),
  toggleAgentFault: (vehicleId, offline) => client.post(`/agents/${vehicleId}/fault`, { offline }),
  triggerAgentNonCompliance: (vehicleId, refuseYielding = true) =>
    client.post(`/agents/${vehicleId}/non-compliance`, { refuse_yielding: refuseYielding }),
  getAgentNetworkStats: () => client.get('/agents/network-stats')
};

export default api;

