
/* ============================================================
   THERMOSAFE AI — SIH26162 — NTRO
   Blue/White GIS Intelligence Platform
   Full Integration: Live FastAPI Backend + Graceful Demo Fallback
   ============================================================ */

(function () {
  'use strict';

  /* ========== EVENT COLOR SYSTEM (consistent everywhere) ========== */
  const EVENT_COLORS = {
    'Critical Industrial Fire':   { hex:'#DC2626', cls:'risk-critical',   clsShort:'critical'   },
    'Industrial Fire':            { hex:'#DC2626', cls:'risk-critical',   clsShort:'critical'   },
    'High-Risk Thermal Event':    { hex:'#EA580C', cls:'risk-high',       clsShort:'high'       },
    'High-Risk Thermal':          { hex:'#EA580C', cls:'risk-high',       clsShort:'high'       },
    'Gas Flare':                  { hex:'#CA8A04', cls:'risk-gas',        clsShort:'gas'        },
    'Persistent Thermal Source':  { hex:'#7C3AED', cls:'risk-persistent', clsShort:'persistent' },
    'Low-Risk Thermal Activity':  { hex:'#16A34A', cls:'risk-low',        clsShort:'low'        },
    'Low Risk':                   { hex:'#16A34A', cls:'risk-low',        clsShort:'low'        },
    'Industrial Facility':        { hex:'#2563EB', cls:'risk-facility',   clsShort:'facility'   },
    'Agricultural Burning':       { hex:'#16A34A', cls:'risk-low',        clsShort:'low'        },
    'Mining Activity':            { hex:'#CA8A04', cls:'risk-gas',        clsShort:'gas'        },
    'Wildfire':                   { hex:'#EA580C', cls:'risk-high',       clsShort:'high'       },
    'Thermal Power Activity':     { hex:'#EA580C', cls:'risk-high',       clsShort:'high'       },
    'Unknown':                    { hex:'#7A8699', cls:'risk-low',        clsShort:'low'        },
    'INDUSTRIAL_FIRE':                     { hex:'#DC2626', cls:'risk-critical',   clsShort:'critical'   },
    'FOREST_OR_WILDFIRE':                  { hex:'#EA580C', cls:'risk-high',       clsShort:'high'       },
    'AGRICULTURAL_BURNING':                { hex:'#16A34A', cls:'risk-low',        clsShort:'low'        },
    'GAS_FLARE':                           { hex:'#CA8A04', cls:'risk-gas',        clsShort:'gas'        },
    'MINING_THERMAL_ACTIVITY':             { hex:'#D97706', cls:'risk-gas',        clsShort:'gas'        },
    'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE':{ hex:'#7C3AED', cls:'risk-persistent', clsShort:'persistent'},
    'OTHER_THERMAL_EVENT':                 { hex:'#64748B', cls:'risk-low',        clsShort:'low'        }
  };

  const RISK_COLORS = {
    CRITICAL: '#DC2626',
    HIGH: '#EA580C',
    MEDIUM: '#CA8A04',
    LOW: '#16A34A',
    INFORMATIONAL: '#2563EB',
    PERSISTENT: '#7C3AED'
  };

  function getEventColor(event) {
    if (!event) return EVENT_COLORS['Low-Risk Thermal Activity'];
    if (EVENT_COLORS[event.classification]) return EVENT_COLORS[event.classification];
    const cl = (event.classification || '').toLowerCase();
    if (cl.includes('critical') || (cl.includes('fire') && event.risk === 'CRITICAL')) return EVENT_COLORS['Critical Industrial Fire'];
    if (cl.includes('fire')) return EVENT_COLORS['Industrial Fire'];
    if (cl.includes('high')) return EVENT_COLORS['High-Risk Thermal Event'];
    if (cl.includes('flare')) return EVENT_COLORS['Gas Flare'];
    if (cl.includes('persistent')) return EVENT_COLORS['Persistent Thermal Source'];
    if (cl.includes('low') || cl.includes('normal')) return EVENT_COLORS['Low-Risk Thermal Activity'];
    if (event.risk === 'CRITICAL') return EVENT_COLORS['Critical Industrial Fire'];
    if (event.risk === 'HIGH') return EVENT_COLORS['High-Risk Thermal Event'];
    if (event.risk === 'MEDIUM') return EVENT_COLORS['Gas Flare'];
    if (event.risk === 'LOW') return EVENT_COLORS['Low-Risk Thermal Activity'];
    return EVENT_COLORS['Unknown'];
  }

  function getRiskColor(risk) {
    const r = (risk || 'LOW').toUpperCase();
    return RISK_COLORS[r] || RISK_COLORS.LOW;
  }

  function riskBadge(risk) {
    const r = (risk || 'LOW').toUpperCase();
    const cls = {
      CRITICAL: 'risk-critical',
      HIGH: 'risk-high',
      MEDIUM: 'risk-gas',
      LOW: 'risk-low',
      INFORMATIONAL: 'risk-facility',
      PERSISTENT: 'risk-persistent'
    }[r] || 'risk-low';
    return `<span class="risk-badge ${cls}">${r}</span>`;
  }

  function classBadge(classification) {
    const c = EVENT_COLORS[classification] || EVENT_COLORS['Unknown'];
    return `<span class="risk-badge ${c.cls}">${classification}</span>`;
  }

    /* ========== DETERMINISTIC BUILT-IN DEMO DATA STORE ========== */
  const BUILTIN_DEMO_EVENTS = [
    // 1. India - Industrial Fire (Jamnagar)
    {
      id: 'DEMO-IN-001',
      event_id: 'DEMO-IN-001',
      lat: 22.3524,
      latitude: 22.3524,
      lng: 69.8652,
      longitude: 69.8652,
      city: 'Jamnagar',
      country: 'India',
      state: 'Gujarat',
      classification: 'INDUSTRIAL_FIRE',
      eventType: 'Industrial Fire',
      event_type: 'INDUSTRIAL_FIRE',
      industrial_natural_group: 'Industrial',
      risk: 'CRITICAL',
      riskPriority: 'CRITICAL',
      risk_priority: 'CRITICAL',
      score: 96,
      riskScore: 96,
      risk_score: 96,
      confidence: 96,
      frp: 840.5,
      intensity: 'CRITICAL (840.5 MW)',
      thermal_intensity: '840.5 MW',
      persistence: '4.8 hours',
      facility: 'Jamnagar Petrochemical Complex',
      facility_name: 'Jamnagar Petrochemical Complex',
      facilityType: 'Refinery & Petrochemicals',
      facilityOperator: 'Reliance Petroleum Ltd.',
      facilityDistance: 0.9,
      landcover: 'Heavy Industrial',
      land_cover: 'Heavy Industrial',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 10:15',
      detected_at: '2026-02-14T10:15:00',
      evidence: 'High thermal intensity with spatial expansion signature in proximity to chemical storage tanks.',
      explanation: 'Critical thermal intensity with high persistence within petrochemical facility boundary.',
      factors: [
        { label: 'Proximity to Chemical Tank Farm', pct: 40 },
        { label: 'Thermal Intensity (840 MW)', pct: 30 },
        { label: 'Persistence (>4 hours)', pct: 20 },
        { label: 'Industrial Land Cover', pct: 10 }
      ]
    },
    // 2. India - Industrial Fire (Visakhapatnam)
    {
      id: 'DEMO-IN-002',
      event_id: 'DEMO-IN-002',
      lat: 17.6868,
      latitude: 17.6868,
      lng: 83.2185,
      longitude: 83.2185,
      city: 'Visakhapatnam',
      country: 'India',
      state: 'Andhra Pradesh',
      classification: 'INDUSTRIAL_FIRE',
      eventType: 'Industrial Fire',
      event_type: 'INDUSTRIAL_FIRE',
      industrial_natural_group: 'Industrial',
      risk: 'CRITICAL',
      riskPriority: 'CRITICAL',
      risk_priority: 'CRITICAL',
      score: 92,
      riskScore: 92,
      risk_score: 92,
      confidence: 94,
      frp: 620.0,
      intensity: 'HIGH (620.0 MW)',
      thermal_intensity: '620.0 MW',
      persistence: '3.7 hours',
      facility: 'Visakhapatnam Petrochemical Complex',
      facility_name: 'Visakhapatnam Petrochemical Complex',
      facilityType: 'Petrochemical Plant',
      facilityOperator: 'HPCL',
      facilityDistance: 1.1,
      landcover: 'Industrial Area',
      land_cover: 'Industrial Area',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Aqua (Demo Reference)',
      detected: '2026-02-14 09:40',
      detected_at: '2026-02-14T09:40:00',
      evidence: 'Sustained thermal signature verified against petrochemical facility coordinates.',
      explanation: 'High thermal radiance in coastal industrial corridor with hazardous material proximity.',
      factors: [
        { label: 'Industrial Proximity', pct: 35 },
        { label: 'Thermal Radiance', pct: 30 },
        { label: 'Persistence Duration', pct: 25 },
        { label: 'Meteorological Vulnerability', pct: 10 }
      ]
    },
    // 3. India - Gas Flare (Mumbai)
    {
      id: 'DEMO-IN-003',
      event_id: 'DEMO-IN-003',
      lat: 19.0760,
      latitude: 19.0760,
      lng: 72.8777,
      longitude: 72.8777,
      city: 'Mumbai',
      country: 'India',
      state: 'Maharashtra',
      classification: 'GAS_FLARE',
      eventType: 'Gas Flare',
      event_type: 'GAS_FLARE',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 72,
      riskScore: 72,
      risk_score: 72,
      confidence: 89,
      frp: 310.2,
      intensity: 'MEDIUM (310.2 MW)',
      thermal_intensity: '310.2 MW',
      persistence: '6.5 hours',
      facility: 'Mumbai Refinery',
      facility_name: 'Mumbai Refinery',
      facilityType: 'Oil Refinery',
      facilityOperator: 'BPCL',
      facilityDistance: 0.6,
      landcover: 'Refinery Stack Perimeter',
      land_cover: 'Refinery Stack Perimeter',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-21 (Demo Reference)',
      detected: '2026-02-14 08:30',
      detected_at: '2026-02-14T08:30:00',
      evidence: 'Stationary high-temperature anomaly aligning with refinery elevated flare stack coordinates.',
      explanation: 'Routine regulated flaring activity monitored for threshold compliance.',
      factors: [
        { label: 'Stack Coordinate Match', pct: 45 },
        { label: 'Radiance Profile', pct: 30 },
        { label: 'Continuous Operation', pct: 25 }
      ]
    },
    // 4. India - Mining Thermal Activity (Korba)
    {
      id: 'DEMO-IN-004',
      event_id: 'DEMO-IN-004',
      lat: 22.3595,
      latitude: 22.3595,
      lng: 82.7501,
      longitude: 82.7501,
      city: 'Korba',
      country: 'India',
      state: 'Chhattisgarh',
      classification: 'MINING_THERMAL_ACTIVITY',
      eventType: 'Mining Activity',
      event_type: 'MINING_THERMAL_ACTIVITY',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 64,
      riskScore: 64,
      risk_score: 64,
      confidence: 82,
      frp: 215.0,
      intensity: 'MODERATE (215.0 MW)',
      thermal_intensity: '215.0 MW',
      persistence: '8.2 hours',
      facility: 'Gevra Open Cast Coal Mine',
      facility_name: 'Gevra Open Cast Coal Mine',
      facilityType: 'Open Cast Coal Mining',
      facilityOperator: 'SECL / Coal India',
      facilityDistance: 1.4,
      landcover: 'Open Pit Barren Ground',
      land_cover: 'Open Pit Barren Ground',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Terra (Demo Reference)',
      detected: '2026-02-14 07:15',
      detected_at: '2026-02-14T07:15:00',
      evidence: 'Slow-burning overburden seam and heavy machinery thermal signature in open-cast basin.',
      explanation: 'Sub-surface coal seam thermal dissipation in active mining concession.',
      factors: [
        { label: 'Open Pit Concession Match', pct: 50 },
        { label: 'Sub-surface Seam Radiance', pct: 30 },
        { label: 'Equipment Heat Exchanger', pct: 20 }
      ]
    },
    // 5. India - Agricultural Burning (Ludhiana)
    {
      id: 'DEMO-IN-005',
      event_id: 'DEMO-IN-005',
      lat: 30.9010,
      latitude: 30.9010,
      lng: 75.8573,
      longitude: 75.8573,
      city: 'Ludhiana',
      country: 'India',
      state: 'Punjab',
      classification: 'AGRICULTURAL_BURNING',
      eventType: 'Agricultural Burning',
      event_type: 'AGRICULTURAL_BURNING',
      industrial_natural_group: 'Natural / Rural',
      risk: 'LOW',
      riskPriority: 'LOW',
      risk_priority: 'LOW',
      score: 42,
      riskScore: 42,
      risk_score: 42,
      confidence: 76,
      frp: 85.0,
      intensity: 'LOW (85.0 MW)',
      thermal_intensity: '85.0 MW',
      persistence: '1.2 hours',
      facility: 'Rural Agricultural Belt',
      facility_name: 'Rural Agricultural Belt',
      facilityType: 'Agricultural Land',
      facilityOperator: 'Agricultural Cooperative',
      facilityDistance: 8.5,
      landcover: 'Cropland Farmland',
      land_cover: 'Cropland Farmland',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS SNPP (Demo Reference)',
      detected: '2026-02-14 11:20',
      detected_at: '2026-02-14T11:20:00',
      evidence: 'Transient low-radiance thermal cluster on harvested agricultural plots.',
      explanation: 'Post-harvest crop residue clearing in rural district far from industrial infrastructure.',
      factors: [
        { label: 'Cropland Land Cover', pct: 60 },
        { label: 'Low Radiance Density', pct: 25 },
        { label: 'Short Duration', pct: 15 }
      ]
    },
    // 6. India - Forest Fire (Similipal)
    {
      id: 'DEMO-IN-006',
      event_id: 'DEMO-IN-006',
      lat: 21.8687,
      latitude: 21.8687,
      lng: 86.3812,
      longitude: 86.3812,
      city: 'Mayurbhanj',
      country: 'India',
      state: 'Odisha',
      classification: 'FOREST_OR_WILDFIRE',
      eventType: 'Forest Fire',
      event_type: 'FOREST_OR_WILDFIRE',
      industrial_natural_group: 'Natural / Rural',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 84,
      riskScore: 84,
      risk_score: 84,
      confidence: 91,
      frp: 540.0,
      intensity: 'HIGH (540.0 MW)',
      thermal_intensity: '540.0 MW',
      persistence: '5.1 hours',
      facility: 'Similipal Biosphere Reserve',
      facility_name: 'Similipal Biosphere Reserve',
      facilityType: 'Protected Forest Area',
      facilityOperator: 'Odisha Forest Department',
      facilityDistance: 12.0,
      landcover: 'Dense Deciduous Forest',
      land_cover: 'Dense Deciduous Forest',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Aqua (Demo Reference)',
      detected: '2026-02-14 06:45',
      detected_at: '2026-02-14T06:45:00',
      evidence: 'Linear front thermal anomaly advancing through dense canopy cover.',
      explanation: 'Spreading dry-season forest fire front requiring airborne containment.',
      factors: [
        { label: 'Dense Forest Fuel Load', pct: 45 },
        { label: 'Wind-driven Propagation', pct: 30 },
        { label: 'Distance to Human Settlement', pct: 25 }
      ]
    },
    // 7. India - Persistent Industrial Thermal Source (Dahej)
    {
      id: 'DEMO-IN-007',
      event_id: 'DEMO-IN-007',
      lat: 21.7125,
      latitude: 21.7125,
      lng: 72.5833,
      longitude: 72.5833,
      city: 'Dahej',
      country: 'India',
      state: 'Gujarat',
      classification: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      eventType: 'Persistent Thermal Source',
      event_type: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      industrial_natural_group: 'Industrial',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 82,
      riskScore: 82,
      risk_score: 82,
      confidence: 95,
      frp: 410.0,
      intensity: 'HIGH (410.0 MW)',
      thermal_intensity: '410.0 MW',
      persistence: '14.2 hours',
      facility: 'Dahej Petrochemical SEZ Hub',
      facility_name: 'Dahej Petrochemical SEZ Hub',
      facilityType: 'Chemical & LNG Processing',
      facilityOperator: 'Petronet LNG / OPAL',
      facilityDistance: 0.7,
      landcover: 'Industrial SEZ',
      land_cover: 'Industrial SEZ',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 05:10',
      detected_at: '2026-02-14T05:10:00',
      evidence: 'Persistent high-heat signature detected across >5 consecutive satellite overpasses.',
      explanation: 'Continuous thermal dissipation from industrial cracking furnaces and reforming towers.',
      factors: [
        { label: 'Persistent Multi-orbit Signature', pct: 45 },
        { label: 'Chemical Reactor Confinement', pct: 35 },
        { label: 'Industrial Zone Boundary', pct: 20 }
      ]
    },
    // 8. India - Other Thermal Event (Tuticorin)
    {
      id: 'DEMO-IN-008',
      event_id: 'DEMO-IN-008',
      lat: 8.7642,
      latitude: 8.7642,
      lng: 78.1348,
      longitude: 78.1348,
      city: 'Tuticorin',
      country: 'India',
      state: 'Tamil Nadu',
      classification: 'OTHER_THERMAL_EVENT',
      eventType: 'Other Thermal Event',
      event_type: 'OTHER_THERMAL_EVENT',
      industrial_natural_group: 'Industrial',
      risk: 'LOW',
      riskPriority: 'LOW',
      risk_priority: 'LOW',
      score: 38,
      riskScore: 38,
      risk_score: 38,
      confidence: 70,
      frp: 65.0,
      intensity: 'LOW (65.0 MW)',
      thermal_intensity: '65.0 MW',
      persistence: '2.0 hours',
      facility: 'Tuticorin Port Thermal Channel',
      facility_name: 'Tuticorin Port Thermal Channel',
      facilityType: 'Harbor / Cooling Discharge',
      facilityOperator: 'V.O. Chidambaranar Port',
      facilityDistance: 2.2,
      landcover: 'Coastal Salt Flat',
      land_cover: 'Coastal Salt Flat',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS SNPP (Demo Reference)',
      detected: '2026-02-14 12:00',
      detected_at: '2026-02-14T12:00:00',
      evidence: 'Solar heating reflection and permitted low-temperature warm water cooling outlet.',
      explanation: 'Non-combustive coastal thermal anomaly with low hazard metric.',
      factors: [
        { label: 'Non-combustive Heat Balance', pct: 60 },
        { label: 'Coastal Saline Reflection', pct: 25 },
        { label: 'Low Gradient', pct: 15 }
      ]
    },
    // 9. Middle East - Gas Flare (Kuwait)
    {
      id: 'DEMO-ME-009',
      event_id: 'DEMO-ME-009',
      lat: 29.0769,
      latitude: 29.0769,
      lng: 48.1328,
      longitude: 48.1328,
      city: 'Ahmadi',
      country: 'Kuwait',
      state: 'Al Ahmadi',
      classification: 'GAS_FLARE',
      eventType: 'Gas Flare',
      event_type: 'GAS_FLARE',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 75,
      riskScore: 75,
      risk_score: 75,
      confidence: 93,
      frp: 480.0,
      intensity: 'MEDIUM (480.0 MW)',
      thermal_intensity: '480.0 MW',
      persistence: '9.0 hours',
      facility: 'Mina Al-Ahmadi Refinery Complex',
      facility_name: 'Mina Al-Ahmadi Refinery Complex',
      facilityType: 'Refinery & Hydrocarbon Hub',
      facilityOperator: 'Kuwait National Petroleum Co.',
      facilityDistance: 0.8,
      landcover: 'Refinery Infrastructure',
      land_cover: 'Refinery Infrastructure',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 08:50',
      detected_at: '2026-02-14T08:50:00',
      evidence: 'High radiance flare pit combustion verified via satellite SWIR channels.',
      explanation: 'Associated petroleum gas combustion during processing stabilization.',
      factors: [
        { label: 'Flare Pit Proximity', pct: 50 },
        { label: 'SWIR Radiance Channel', pct: 30 },
        { label: 'Continuous Emission Profile', pct: 20 }
      ]
    },
    // 10. Middle East - Gas Flare (Qatar)
    {
      id: 'DEMO-ME-010',
      event_id: 'DEMO-ME-010',
      lat: 25.9036,
      latitude: 25.9036,
      lng: 51.5283,
      longitude: 51.5283,
      city: 'Ras Laffan',
      country: 'Qatar',
      state: 'Al Khor',
      classification: 'GAS_FLARE',
      eventType: 'Gas Flare',
      event_type: 'GAS_FLARE',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 71,
      riskScore: 71,
      risk_score: 71,
      confidence: 90,
      frp: 395.0,
      intensity: 'MEDIUM (395.0 MW)',
      thermal_intensity: '395.0 MW',
      persistence: '7.8 hours',
      facility: 'Ras Laffan LNG Liquefaction Hub',
      facility_name: 'Ras Laffan LNG Liquefaction Hub',
      facilityType: 'LNG Export Terminal',
      facilityOperator: 'QatarEnergy LNG',
      facilityDistance: 1.2,
      landcover: 'LNG Industrial City',
      land_cover: 'LNG Industrial City',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-21 (Demo Reference)',
      detected: '2026-02-14 07:45',
      detected_at: '2026-02-14T07:45:00',
      evidence: 'Elevated industrial ground flare signature with steady radiant flux.',
      explanation: 'Regulated boil-off gas burning at mega-LNG export terminal.',
      factors: [
        { label: 'LNG Terminal Alignment', pct: 45 },
        { label: 'Constant Flux Profile', pct: 35 },
        { label: 'Regulated Flare Safety Zone', pct: 20 }
      ]
    },
    // 11. Middle East - Industrial Fire (Iraq)
    {
      id: 'DEMO-ME-011',
      event_id: 'DEMO-ME-011',
      lat: 30.5081,
      latitude: 30.5081,
      lng: 47.7835,
      longitude: 47.7835,
      city: 'Basra',
      country: 'Iraq',
      state: 'Basra Governorate',
      classification: 'INDUSTRIAL_FIRE',
      eventType: 'Industrial Fire',
      event_type: 'INDUSTRIAL_FIRE',
      industrial_natural_group: 'Industrial',
      risk: 'CRITICAL',
      riskPriority: 'CRITICAL',
      risk_priority: 'CRITICAL',
      score: 94,
      riskScore: 94,
      risk_score: 94,
      confidence: 95,
      frp: 790.0,
      intensity: 'CRITICAL (790.0 MW)',
      thermal_intensity: '790.0 MW',
      persistence: '5.6 hours',
      facility: 'Rumaila Oilfield Degassing Station',
      facility_name: 'Rumaila Oilfield Degassing Station',
      facilityType: 'Crude Oil Processing',
      facilityOperator: 'Basra Oil Company',
      facilityDistance: 1.5,
      landcover: 'Desert Industrial Oil Concession',
      land_cover: 'Desert Industrial Oil Concession',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Aqua (Demo Reference)',
      detected: '2026-02-14 09:10',
      detected_at: '2026-02-14T09:10:00',
      evidence: 'Anomalous uncontained thermal plume with intense Black Body radiant spectrum.',
      explanation: 'Emergency manifold fire detected outside designated flare combustion pits.',
      factors: [
        { label: 'Radiance Intensity (790 MW)', pct: 40 },
        { label: 'Off-stack Anomaly Location', pct: 35 },
        { label: 'Rapid Thermal Escalation', pct: 25 }
      ]
    },
    // 12. Southeast Asia - Persistent Industrial Thermal Source (Thailand)
    {
      id: 'DEMO-SEA-012',
      event_id: 'DEMO-SEA-012',
      lat: 12.6814,
      latitude: 12.6814,
      lng: 101.1648,
      longitude: 101.1648,
      city: 'Rayong',
      country: 'Thailand',
      state: 'Rayong Province',
      classification: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      eventType: 'Persistent Thermal Source',
      event_type: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      industrial_natural_group: 'Industrial',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 83,
      riskScore: 83,
      risk_score: 83,
      confidence: 92,
      frp: 460.0,
      intensity: 'HIGH (460.0 MW)',
      thermal_intensity: '460.0 MW',
      persistence: '16.5 hours',
      facility: 'Map Ta Phut Petrochemical Hub',
      facility_name: 'Map Ta Phut Petrochemical Hub',
      facilityType: 'Olefin Cracking & Plastics',
      facilityOperator: 'PTT Global Chemical',
      facilityDistance: 0.9,
      landcover: 'Heavy Industrial Estate',
      land_cover: 'Heavy Industrial Estate',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 04:30',
      detected_at: '2026-02-14T04:30:00',
      evidence: 'Persistent multi-day hotspot at cracker furnace battery with zero spatial drift.',
      explanation: 'Stable ethylene cracker high-temperature process emissions.',
      factors: [
        { label: 'Multi-orbit Persistence', pct: 50 },
        { label: 'Facility Blueprint Match', pct: 30 },
        { label: 'Controlled Heat Dissipation', pct: 20 }
      ]
    },
    // 13. Southeast Asia - Agricultural Burning (Indonesia)
    {
      id: 'DEMO-SEA-013',
      event_id: 'DEMO-SEA-013',
      lat: 0.5071,
      latitude: 0.5071,
      lng: 101.4478,
      longitude: 101.4478,
      city: 'Pekanbaru',
      country: 'Indonesia',
      state: 'Riau Province',
      classification: 'AGRICULTURAL_BURNING',
      eventType: 'Agricultural Burning',
      event_type: 'AGRICULTURAL_BURNING',
      industrial_natural_group: 'Natural / Rural',
      risk: 'LOW',
      riskPriority: 'LOW',
      risk_priority: 'LOW',
      score: 48,
      riskScore: 48,
      risk_score: 48,
      confidence: 78,
      frp: 110.0,
      intensity: 'LOW (110.0 MW)',
      thermal_intensity: '110.0 MW',
      persistence: '2.1 hours',
      facility: 'Riau Plantation Zone',
      facility_name: 'Riau Plantation Zone',
      facilityType: 'Oil Palm Plantation',
      facilityOperator: 'Regional Agriculture Group',
      facilityDistance: 14.0,
      landcover: 'Plantation Clearing Border',
      land_cover: 'Plantation Clearing Border',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS SNPP (Demo Reference)',
      detected: '2026-02-14 10:40',
      detected_at: '2026-02-14T10:40:00',
      evidence: 'Scattered thermal pixels over cleared plantation acreage with smoke aerosol signature.',
      explanation: 'Managed agricultural biomass burning during dry replanting cycle.',
      factors: [
        { label: 'Agricultural Concession', pct: 55 },
        { label: 'Transient Moderate Radiance', pct: 30 },
        { label: 'Regional Air Quality Impact', pct: 15 }
      ]
    },
    // 14. Southeast Asia - Forest / Wildfire (Indonesia)
    {
      id: 'DEMO-SEA-014',
      event_id: 'DEMO-SEA-014',
      lat: -2.2136,
      latitude: -2.2136,
      lng: 113.9108,
      longitude: 113.9108,
      city: 'Palangkaraya',
      country: 'Indonesia',
      state: 'Central Kalimantan',
      classification: 'FOREST_OR_WILDFIRE',
      eventType: 'Wildfire',
      event_type: 'FOREST_OR_WILDFIRE',
      industrial_natural_group: 'Natural / Rural',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 87,
      riskScore: 87,
      risk_score: 87,
      confidence: 93,
      frp: 680.0,
      intensity: 'HIGH (680.0 MW)',
      thermal_intensity: '680.0 MW',
      persistence: '7.4 hours',
      facility: 'Sebangau National Peatland Reserve',
      facility_name: 'Sebangau National Peatland Reserve',
      facilityType: 'Tropical Peat Swamp Forest',
      facilityOperator: 'Ministry of Environment & Forestry',
      facilityDistance: 18.0,
      landcover: 'Peatland Rain Forest',
      land_cover: 'Peatland Rain Forest',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Terra (Demo Reference)',
      detected: '2026-02-14 06:15',
      detected_at: '2026-02-14T06:15:00',
      evidence: 'Deep smoldering peat combustion front with extensive CO/PM2.5 plume detection.',
      explanation: 'Sub-surface peat fire spreading along drained peat swamp boundaries.',
      factors: [
        { label: 'High-density Peat Fuel Bed', pct: 50 },
        { label: 'Deep Combustion Persistence', pct: 30 },
        { label: 'Transboundary Haze Threat', pct: 20 }
      ]
    },
    // 15. Europe - Persistent Industrial Thermal Source (Netherlands)
    {
      id: 'DEMO-EU-015',
      event_id: 'DEMO-EU-015',
      lat: 51.9540,
      latitude: 51.9540,
      lng: 4.1350,
      longitude: 4.1350,
      city: 'Rotterdam',
      country: 'Netherlands',
      state: 'South Holland',
      classification: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      eventType: 'Persistent Thermal Source',
      event_type: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 68,
      riskScore: 68,
      risk_score: 68,
      confidence: 96,
      frp: 290.0,
      intensity: 'MEDIUM (290.0 MW)',
      thermal_intensity: '290.0 MW',
      persistence: '24.0 hours',
      facility: 'Port of Rotterdam Petrochemical Hub',
      facility_name: 'Port of Rotterdam Petrochemical Hub',
      facilityType: 'Refining & Chemical Logistics',
      facilityOperator: 'Shell Nederland',
      facilityDistance: 0.5,
      landcover: 'Deepwater Industrial Port',
      land_cover: 'Deepwater Industrial Port',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 03:20',
      detected_at: '2026-02-14T03:20:00',
      evidence: 'Stationary baseline heat flux correlating with European PRTR refinery registries.',
      explanation: 'Continuous thermal activity at European energy transition and refining facility.',
      factors: [
        { label: 'Registry Blueprint Alignment', pct: 55 },
        { label: 'Consistent Thermal Baseline', pct: 30 },
        { label: 'Port Industrial Perimeter', pct: 15 }
      ]
    },
    // 16. Europe - Gas Flare (France)
    {
      id: 'DEMO-EU-016',
      event_id: 'DEMO-EU-016',
      lat: 43.4378,
      latitude: 43.4378,
      lng: 4.8872,
      longitude: 4.8872,
      city: 'Fos-sur-Mer',
      country: 'France',
      state: 'Bouches-du-Rhône',
      classification: 'GAS_FLARE',
      eventType: 'Gas Flare',
      event_type: 'GAS_FLARE',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 66,
      riskScore: 66,
      risk_score: 66,
      confidence: 88,
      frp: 275.0,
      intensity: 'MEDIUM (275.0 MW)',
      thermal_intensity: '275.0 MW',
      persistence: '4.2 hours',
      facility: 'Fos Petrochemical Complex',
      facility_name: 'Fos Petrochemical Complex',
      facilityType: 'Ethylene & Petrochemical Works',
      facilityOperator: 'TotalEnergies / Kem One',
      facilityDistance: 1.0,
      landcover: 'Mediterranean Industrial Estuary',
      land_cover: 'Mediterranean Industrial Estuary',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-21 (Demo Reference)',
      detected: '2026-02-14 08:05',
      detected_at: '2026-02-14T08:05:00',
      evidence: 'Localized SWIR temperature peak consistent with safety flare relief valves.',
      explanation: 'Controlled flare discharge during unit maintenance cycle.',
      factors: [
        { label: 'Relief Flare Coordinates', pct: 50 },
        { label: 'Thermal Intensity Bounds', pct: 30 },
        { label: 'Coastal Dispersion Conditions', pct: 20 }
      ]
    },
    // 17. Europe - Forest Fire (Greece)
    {
      id: 'DEMO-EU-017',
      event_id: 'DEMO-EU-017',
      lat: 37.6393,
      latitude: 37.6393,
      lng: 21.6263,
      longitude: 21.6263,
      city: 'Olympia',
      country: 'Greece',
      state: 'Peloponnese',
      classification: 'FOREST_OR_WILDFIRE',
      eventType: 'Forest Fire',
      event_type: 'FOREST_OR_WILDFIRE',
      industrial_natural_group: 'Natural / Rural',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 85,
      riskScore: 85,
      risk_score: 85,
      confidence: 94,
      frp: 610.0,
      intensity: 'HIGH (610.0 MW)',
      thermal_intensity: '610.0 MW',
      persistence: '6.0 hours',
      facility: 'Peloponnese Pine Forest Reserve',
      facility_name: 'Peloponnese Pine Forest Reserve',
      facilityType: 'Mediterranean Pine Woodland',
      facilityOperator: 'Hellenic Fire Corps',
      facilityDistance: 9.0,
      landcover: 'Mediterranean Shrub & Pine',
      land_cover: 'Mediterranean Shrub & Pine',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Aqua (Demo Reference)',
      detected: '2026-02-14 11:50',
      detected_at: '2026-02-14T11:50:00',
      evidence: 'Multiple contiguous thermal fire detections advancing up ridgeline terrain.',
      explanation: 'High-intensity wildfire burning in rugged Mediterranean topography.',
      factors: [
        { label: 'Dry Conifer Fuel Combustibility', pct: 45 },
        { label: 'Steep Topographic Slope Winds', pct: 35 },
        { label: 'Heritage Zone Protection', pct: 20 }
      ]
    },
    // 18. Africa - Persistent Industrial Thermal Source (South Africa)
    {
      id: 'DEMO-AF-018',
      event_id: 'DEMO-AF-018',
      lat: -26.5503,
      latitude: -26.5503,
      lng: 29.1785,
      longitude: 29.1785,
      city: 'Secunda',
      country: 'South Africa',
      state: 'Mpumalanga',
      classification: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      eventType: 'Persistent Thermal Source',
      event_type: 'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE',
      industrial_natural_group: 'Industrial',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 86,
      riskScore: 86,
      risk_score: 86,
      confidence: 97,
      frp: 720.0,
      intensity: 'HIGH (720.0 MW)',
      thermal_intensity: '720.0 MW',
      persistence: '36.0 hours',
      facility: 'Sasol Secunda Synthetic Fuels Complex',
      facility_name: 'Sasol Secunda Synthetic Fuels Complex',
      facilityType: 'Coal Gasification & Liquids',
      facilityOperator: 'Sasol South Africa',
      facilityDistance: 0.7,
      landcover: 'Massive Industrial Synthetic Complex',
      land_cover: 'Massive Industrial Synthetic Complex',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 02:40',
      detected_at: '2026-02-14T02:40:00',
      evidence: 'World-scale continuous high radiant energy output from gasification synthesis units.',
      explanation: 'Known major global industrial thermal emission hotspot with ongoing operational monitoring.',
      factors: [
        { label: 'Global Landmark Hotspot Catalog', pct: 50 },
        { label: 'Thermal Intensity (720 MW)', pct: 30 },
        { label: 'Synthetic Gasifier Signature', pct: 20 }
      ]
    },
    // 19. Africa - Gas Flare (Nigeria)
    {
      id: 'DEMO-AF-019',
      event_id: 'DEMO-AF-019',
      lat: 4.4262,
      latitude: 4.4262,
      lng: 7.1648,
      longitude: 7.1648,
      city: 'Bonny Island',
      country: 'Nigeria',
      state: 'Rivers State',
      classification: 'GAS_FLARE',
      eventType: 'Gas Flare',
      event_type: 'GAS_FLARE',
      industrial_natural_group: 'Industrial',
      risk: 'HIGH',
      riskPriority: 'HIGH',
      risk_priority: 'HIGH',
      score: 79,
      riskScore: 79,
      risk_score: 79,
      confidence: 91,
      frp: 510.0,
      intensity: 'HIGH (510.0 MW)',
      thermal_intensity: '510.0 MW',
      persistence: '18.0 hours',
      facility: 'Bonny Island LNG Terminal',
      facility_name: 'Bonny Island LNG Terminal',
      facilityType: 'Gas Liquefaction & Crude Export',
      facilityOperator: 'Nigeria LNG (NLNG)',
      facilityDistance: 1.3,
      landcover: 'Mangrove Coastal Terminal',
      land_cover: 'Mangrove Coastal Terminal',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS SNPP (Demo Reference)',
      detected: '2026-02-14 07:30',
      detected_at: '2026-02-14T07:30:00',
      evidence: 'High radiance continuous gas flare emission over coastal delta terminal.',
      explanation: 'Offshore and onshore associated gas relief system operational monitoring.',
      factors: [
        { label: 'Flare Stack Geo-location', pct: 45 },
        { label: 'Radiative Heat Dissipation', pct: 35 },
        { label: 'Atmospheric Dispersion Factor', pct: 20 }
      ]
    },
    // 20. North America - Industrial Fire (USA)
    {
      id: 'DEMO-NA-020',
      event_id: 'DEMO-NA-020',
      lat: 29.7355,
      latitude: 29.7355,
      lng: -95.0135,
      longitude: -95.0135,
      city: 'Baytown / Houston',
      country: 'USA',
      state: 'Texas',
      classification: 'INDUSTRIAL_FIRE',
      eventType: 'Industrial Fire',
      event_type: 'INDUSTRIAL_FIRE',
      industrial_natural_group: 'Industrial',
      risk: 'CRITICAL',
      riskPriority: 'CRITICAL',
      risk_priority: 'CRITICAL',
      score: 95,
      riskScore: 95,
      risk_score: 95,
      confidence: 95,
      frp: 810.0,
      intensity: 'CRITICAL (810.0 MW)',
      thermal_intensity: '810.0 MW',
      persistence: '3.9 hours',
      facility: 'Baytown Olefins & Refining Complex',
      facility_name: 'Baytown Olefins & Refining Complex',
      facilityType: 'Integrated Petrochemical Refinery',
      facilityOperator: 'ExxonMobil Baytown Complex',
      facilityDistance: 1.1,
      landcover: 'Houston Ship Channel Industrial Strip',
      land_cover: 'Houston Ship Channel Industrial Strip',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'VIIRS NOAA-20 (Demo Reference)',
      detected: '2026-02-14 10:05',
      detected_at: '2026-02-14T10:05:00',
      evidence: 'High-order thermal radiance spike adjacent to processing units with rapid spatial enlargement.',
      explanation: 'Critical industrial thermal hazard requiring immediate municipal & private hazmat intervention.',
      factors: [
        { label: 'Houston Ship Channel Density', pct: 40 },
        { label: 'Radiant Heat Elevation (810 MW)', pct: 30 },
        { label: 'Volatile Hydrocarbon Inventory', pct: 20 },
        { label: 'Emergency Tier-1 Response', pct: 10 }
      ]
    },
    // 21. North America - Mining Thermal Activity (Canada)
    {
      id: 'DEMO-NA-021',
      event_id: 'DEMO-NA-021',
      lat: 56.9950,
      latitude: 56.9950,
      lng: -111.4930,
      longitude: -111.4930,
      city: 'Fort McMurray',
      country: 'Canada',
      state: 'Alberta',
      classification: 'MINING_THERMAL_ACTIVITY',
      eventType: 'Mining Activity',
      event_type: 'MINING_THERMAL_ACTIVITY',
      industrial_natural_group: 'Industrial',
      risk: 'MEDIUM',
      riskPriority: 'MEDIUM',
      risk_priority: 'MEDIUM',
      score: 65,
      riskScore: 65,
      risk_score: 65,
      confidence: 85,
      frp: 320.0,
      intensity: 'MEDIUM (320.0 MW)',
      thermal_intensity: '320.0 MW',
      persistence: '11.0 hours',
      facility: 'Athabasca Oil Sands Surface Mine',
      facility_name: 'Athabasca Oil Sands Surface Mine',
      facilityType: 'Surface Mining & Bitumen Extraction',
      facilityOperator: 'Syncrude / Suncor Works',
      facilityDistance: 2.8,
      landcover: 'Open Pit Mine Bitumen Deposit',
      land_cover: 'Open Pit Mine Bitumen Deposit',
      source: 'DEMO',
      data_source: 'DEMO',
      is_demo: true,
      satellite: 'MODIS Aqua (Demo Reference)',
      detected: '2026-02-14 05:55',
      detected_at: '2026-02-14T05:55:00',
      evidence: 'Large-scale thermal signature matching extraction machinery and bitumen extraction upgrading steam.',
      explanation: 'Surface bitumen thermal extraction process in Athabasca oil sands basin.',
      factors: [
        { label: 'Active Mine Footprint Concession', pct: 50 },
        { label: 'High Thermal Heat Recovery Units', pct: 30 },
        { label: 'Arctic Ambient Temperature Gradient', pct: 20 }
      ]
    }
  ];

  const DEMO_EVENTS_RAW = BUILTIN_DEMO_EVENTS;

  const DEMO_FACILITIES_RAW = [
    { id:'FAC-001', dbId:1, name:'Visakhapatnam Petrochemical Complex', lat:17.6800, latitude:17.6800, lng:83.2100, longitude:83.2100, type:'Petrochemical Plant', industry_type:'Petrochemical Plant', capacity:'High', risk_level:'High', operator:'HPCL (DEMO)', address:'Industrial Area, Visakhapatnam, Andhra Pradesh' },
    { id:'FAC-002', dbId:2, name:'Mumbai Refinery', lat:19.0700, latitude:19.0700, lng:72.8700, longitude:72.8700, type:'Oil Refinery', industry_type:'Oil Refinery', capacity:'Very High', risk_level:'Very High', operator:'BPCL (DEMO)', address:'Mahul, Chembur, Mumbai, Maharashtra' },
    { id:'FAC-003', dbId:3, name:'Vadodara Chemical Works', lat:22.3100, latitude:22.3100, lng:73.1800, longitude:73.1800, type:'Chemical Plant', industry_type:'Chemical Plant', capacity:'High', risk_level:'High', operator:'GSFC (DEMO)', address:'Fertilizernagar, Vadodara, Gujarat' },
    { id:'FAC-004', dbId:4, name:'Chennai Thermal Power Station', lat:13.0800, latitude:13.0800, lng:80.2700, longitude:80.2700, type:'Thermal Power Plant', industry_type:'Thermal Power Plant', capacity:'High', risk_level:'High', operator:'TANGEDCO (DEMO)', address:'Ennore Express Rd, Chennai, Tamil Nadu' },
    { id:'FAC-005', dbId:5, name:'Jamnagar Petrochemical Complex', lat:22.3039, latitude:22.3039, lng:70.8022, longitude:70.8022, type:'Refinery & Petrochemicals', industry_type:'Refinery & Petrochemicals', capacity:'Critical', risk_level:'Critical', operator:'Reliance Petroleum Ltd. (DEMO)', address:'Sector 4, Refinery Corridor, Jamnagar, Gujarat' },
    { id:'FAC-006', dbId:6, name:'Dahej Petrochemical SEZ Hub', lat:21.7100, latitude:21.7100, lng:72.5800, longitude:72.5800, type:'Chemical & LNG Processing', industry_type:'Chemical & LNG Processing', capacity:'High', risk_level:'High', operator:'Petronet LNG / OPAL (DEMO)', address:'Dahej SEZ, Bharuch, Gujarat' },
    { id:'FAC-007', dbId:7, name:'Mina Al-Ahmadi Refinery Complex', lat:29.0750, latitude:29.0750, lng:48.1300, longitude:48.1300, type:'Refinery & Hydrocarbon Hub', industry_type:'Refinery & Hydrocarbon Hub', capacity:'Critical', risk_level:'Critical', operator:'Kuwait National Petroleum Co. (DEMO)', address:'Ahmadi, Kuwait' },
    { id:'FAC-008', dbId:8, name:'Ras Laffan LNG Liquefaction Hub', lat:25.9000, latitude:25.9000, lng:51.5200, longitude:51.5200, type:'LNG Export Terminal', industry_type:'LNG Export Terminal', capacity:'Critical', risk_level:'Critical', operator:'QatarEnergy LNG (DEMO)', address:'Ras Laffan Industrial City, Qatar' },
    { id:'FAC-009', dbId:9, name:'Map Ta Phut Petrochemical Hub', lat:12.6800, latitude:12.6800, lng:101.1600, longitude:101.1600, type:'Olefin Cracking & Plastics', industry_type:'Olefin Cracking & Plastics', capacity:'High', risk_level:'High', operator:'PTT Global Chemical (DEMO)', address:'Map Ta Phut, Rayong, Thailand' },
    { id:'FAC-010', dbId:10, name:'Port of Rotterdam Petrochemical Hub', lat:51.9500, latitude:51.9500, lng:4.1300, longitude:4.1300, type:'Refining & Chemical Logistics', industry_type:'Refining & Chemical Logistics', capacity:'High', risk_level:'High', operator:'Shell Nederland (DEMO)', address:'Europoort, Rotterdam, Netherlands' },
    { id:'FAC-011', dbId:11, name:'Sasol Secunda Synthetic Fuels Complex', lat:-26.5500, latitude:-26.5500, lng:29.1700, longitude:29.1700, type:'Coal Gasification & Liquids', industry_type:'Coal Gasification & Liquids', capacity:'Critical', risk_level:'Critical', operator:'Sasol South Africa (DEMO)', address:'Secunda, Mpumalanga, South Africa' },
    { id:'FAC-012', dbId:12, name:'Baytown Olefins & Refining Complex', lat:29.7300, latitude:29.7300, lng:-95.0100, longitude:-95.0100, type:'Integrated Petrochemical Refinery', industry_type:'Integrated Petrochemical Refinery', capacity:'Critical', risk_level:'Critical', operator:'ExxonMobil Baytown Complex (DEMO)', address:'Baytown, Texas, USA' }
  ];

  const DEMO_NOTIFICATIONS_RAW = [
    { id:'NT-001', alert_id:'NT-001', level:'critical', severity:'Critical', riskPriority:'CRITICAL', title:'Critical Industrial Fire Detected', msg:'Industrial Fire detected near Visakhapatnam Industrial Zone. Risk: CRITICAL. AI Confidence: 93%.', message:'Industrial Fire detected near Visakhapatnam Industrial Zone. Risk: CRITICAL. AI Confidence: 93%.', eventId:'TH-2026-00421', event_id:'TH-2026-00421', latitude:17.6868, lat:17.6868, longitude:83.2185, lng:83.2185, riskScore:92, risk_score:92, eventType:'Industrial Fire', event_type:'Industrial Fire', time:'10:42 AM', unread:true, is_read:false, isAcknowledged:false, is_acknowledged:false, ts: Date.now() - 5*60*1000 },
    { id:'NT-002', alert_id:'NT-002', level:'high', severity:'High', riskPriority:'HIGH', title:'High-Risk Thermal Event Detected', msg:'Industrial Fire near Vadodara Chemical Plant. Risk: HIGH. AI Confidence: 96%.', message:'Industrial Fire near Vadodara Chemical Plant. Risk: HIGH. AI Confidence: 96%.', eventId:'TH-2026-00423', event_id:'TH-2026-00423', latitude:22.3072, lat:22.3072, longitude:73.1812, lng:73.1812, riskScore:95, risk_score:95, eventType:'Industrial Fire', event_type:'Industrial Fire', time:'08:47 AM', unread:true, is_read:false, isAcknowledged:false, is_acknowledged:false, ts: Date.now() - 12*60*1000 },
    { id:'NT-003', alert_id:'NT-003', level:'persistent', severity:'Moderate', riskPriority:'MEDIUM', title:'Persistent Thermal Source Identified', msg:'Persistent thermal activity detected near Surat LNG Terminal for 6.0 hours.', message:'Persistent thermal activity detected near Surat LNG Terminal for 6.0 hours.', eventId:'TH-2026-00422', event_id:'TH-2026-00422', latitude:19.0760, lat:19.0760, longitude:72.8777, lng:72.8777, riskScore:78, risk_score:78, eventType:'Gas Flare', event_type:'Gas Flare', time:'05:30 AM', unread:true, is_read:false, isAcknowledged:false, is_acknowledged:false, ts: Date.now() - 25*60*1000 },
    { id:'NT-004', alert_id:'NT-004', level:'gas', severity:'Moderate', riskPriority:'MEDIUM', title:'Gas Flare Detected', msg:'Gas flare detected near Mumbai Refinery. Risk: HIGH.', message:'Gas flare detected near Mumbai Refinery. Risk: HIGH.', eventId:'TH-2026-00422', event_id:'TH-2026-00422', latitude:19.0760, lat:19.0760, longitude:72.8777, lng:72.8777, riskScore:78, risk_score:78, eventType:'Gas Flare', event_type:'Gas Flare', time:'09:15 AM', unread:false, is_read:true, isAcknowledged:false, is_acknowledged:false, ts: Date.now() - 60*60*1000 }
  ];

  /* Backwards-compatibility aliases */
  const THERMAL_EVENTS = DEMO_EVENTS_RAW;
  const FACILITIES = DEMO_FACILITIES_RAW;
  const INITIAL_NOTIFICATIONS = DEMO_NOTIFICATIONS_RAW;

  /* Separated stores to prevent live/demo cross-contamination */
  const DEMO_DATA = {
    events: JSON.parse(JSON.stringify(DEMO_EVENTS_RAW)),
    facilities: JSON.parse(JSON.stringify(DEMO_FACILITIES_RAW)),
    notifications: JSON.parse(JSON.stringify(DEMO_NOTIFICATIONS_RAW)),
    analytics: null,
    reports: []
  };

  const LIVE_DATA = {
    events: [],
    facilities: [],
    notifications: [],
    analytics: null,
    reports: []
  };

  const LIVE_FEED = [
    { time:'10:42:31', text:'Critical thermal anomaly detected — Jamnagar Complex' },
    { time:'10:40:18', text:'AI classified Industrial Fire — Confidence 98%' },
    { time:'10:37:12', text:'Persistent hotspot detected — Dahej SEZ Zone' },
    { time:'10:35:44', text:'Risk assessment calculated — Score 96.5' },
    { time:'10:32:09', text:'Satellite telemetry synchronized — 5 active events' },
    { time:'10:28:51', text:'Emergency alert generated — Jamnagar Petrochemical' }
  ];

  /* ========== DYNAMIC WORKING ARRAYS ========== */
  let currentEvents = LIVE_DATA.events;
  let currentFacilities = LIVE_DATA.facilities;

  /* ========== STATE ========== */
  const state = {
    currentPage: 'initializing',
    authStatus: 'initializing', // 'initializing' | 'authenticated' | 'unauthenticated'
    selectedEvent: null,
    map: null,
    thermalLayer: null,
    facilityLayer: null,
    heatLayer: null,
    markers: {},
    simCounter: 500,
    dataState: 'CONNECTING', // 'CONNECTING' | 'LIVE' | 'DEMO_FALLBACK' | 'ERROR'
    dataSource: 'live', // Step 3: explicit data-source state ('live' | 'demo'), default 'live'
    isLiveBackend: true,
    backendConnected: false,
    firmsState: 'INITIALIZING', // Canonical LIVE state: 'LIVE_CONNECTED' | 'LIVE_STALE' | 'LIVE_UNAVAILABLE' | 'CONFIGURATION_REQUIRED' | 'INITIALIZING'
    lastSuccessfulFirmsFetch: null,
    lastSuccessfulFirmsEventCount: 0,
    lastFirmsError: null,
    lastFirmsFetchAttempt: null,
    liveFreshnessWindowMs: 30 * 60 * 1000, // 30-minute freshness threshold before considering live data stale
    livePollingActive: false,
    dashboardMountCount: 0,
    liveFetchRequestId: 0,
    lastSuccessfulFetch: null,
    lastApiError: null,
    notifications: JSON.parse(JSON.stringify(DEMO_DATA.notifications)),
    browserNotifPermission: 'default',
    showHeatmap: false,
    showFacilities: true,
    heatmapData: [],
    currentUser: null, // Initialized via getStoredLocalOperator() below
    authToken: localStorage.getItem('thermo_jwt_token') || null,
    authStatus: localStorage.getItem('thermo_jwt_token') ? 'authenticated' : 'local',
    backendAnalytics: null,
    backendReports: [],
    pendingPage: null,
    operatorTeams: [],
    fcmStatus: null,
    registeredDevices: []
  };

    /* ========== AUTHORITATIVE DATA STATE HELPERS ========== */
  function getSourceLabelText() {
    if (state.dataSource === 'demo' || state.dataState === 'DEMO_FALLBACK' || state.dataState === 'OFFLINE_FALLBACK') {
      return 'DEMO DATA';
    }
    if (state.dataState === 'CONNECTING') {
      return 'CONNECTING TO NASA FIRMS...';
    }
    return 'NASA FIRMS LIVE';
  }

  function getSourceLabelColor() {
    if (state.dataSource === 'demo' || state.dataState === 'DEMO_FALLBACK' || state.dataState === 'OFFLINE_FALLBACK') return '#CA8A04';
    if (state.dataState === 'CONNECTING') return '#D97706';
    return '#16A34A';
  }

  function getLiveStatusBadgeInfo() {
    if (state.dataSource === 'demo' || state.dataState === 'DEMO_FALLBACK' || state.dataState === 'OFFLINE_FALLBACK') {
      const isBackendDown = state.dataState === 'OFFLINE_FALLBACK' || !state.backendConnected;
      return {
        text: isBackendDown
          ? 'Live backend temporarily unavailable — displaying demonstration data.'
          : 'NASA FIRMS feed pending — displaying demonstration data.',
        badge: 'DEMO DATA',
        bg: '#FEF3C7',
        color: '#92400E',
        subtext: isBackendDown
          ? 'Live backend temporarily unavailable — displaying demonstration data.'
          : 'NASA FIRMS feed pending — displaying demonstration data.'
      };
    }
    if (state.dataState === 'CONNECTING') {
      return {
        text: 'Connecting to NASA FIRMS...',
        badge: 'CONNECTING...',
        bg: '#EFF6FF',
        color: '#1D4ED8',
        subtext: ''
      };
    }
    if (state.firmsState === 'LIVE_STALE') {
      const timeStr = state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : 'RECENT';
      return {
        text: `● NASA FIRMS LIVE — CACHED (${timeStr})`,
        badge: 'NASA FIRMS LIVE',
        bg: '#FEF3C7',
        color: '#92400E',
        subtext: `Satellite telemetry cached (${timeStr}).`
      };
    }
    return {
      text: '● NASA FIRMS LIVE',
      badge: 'NASA FIRMS LIVE',
      bg: '#DCFCE7',
      color: '#166534',
      subtext: ''
    };
  }

  function applyDemoFallbackState(reason = 'Live backend temporarily unavailable — displaying demonstration data.', isBackendOffline = false) {
    console.warn(`[ThermoSafe Fallback] Activating demo fallback mode: ${reason}`);
    state.dataSource = 'demo';
    state.dataState = isBackendOffline ? 'OFFLINE_FALLBACK' : 'DEMO_FALLBACK';
    state.firmsState = 'DEMO';
    state.backendConnected = !isBackendOffline;
    state.isLiveBackend = !isBackendOffline;
    state.lastApiError = reason;
    state.lastFirmsError = reason;
    state.liveStatusMessage = reason;
    currentEvents = (DEMO_DATA.events && DEMO_DATA.events.length > 0) ? DEMO_DATA.events : BUILTIN_DEMO_EVENTS;
    currentFacilities = DEMO_DATA.facilities;
    state.notifications = DEMO_DATA.notifications;
    LIVE_DATA.events = [];

    if (state.currentPage === 'dashboard') {
      updateDashboardLiveView();
    } else {
      renderMarkers();
      if (state.showFacilities) renderFacilities();
      if (state.currentPage === 'incidents') renderIncidentsPage();
      if (state.currentPage === 'alerts') renderAlertsPage();
    }
    updateDataSourceUI();
    updateDebugDiagnostics();
  }

  function activateFirmsUnavailable(reason = 'Live backend temporarily unavailable — displaying demonstration data.') {
    applyDemoFallbackState(reason, false);
  }

  function activateDemoFallback(reason = 'Live backend temporarily unavailable — displaying demonstration data.', isBackendOffline = false) {
    applyDemoFallbackState(reason, isBackendOffline);
  }

  /* ========== LOCAL OPERATOR SESSION (PHASE 28) ========== */
  const DEFAULT_LOCAL_OPERATOR = {
    id: "local-operator",
    name: "ThermoSafe Operator",
    full_name: "ThermoSafe Operator",
    role: "Analyst",
    email: "local@thermosafe.ai",
    operator_team_id: null,
    operator_team_name: "Operations Watch Desk"
  };

  function getStoredLocalOperator() {
    try {
      const stored = localStorage.getItem('thermo_operator_user');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && typeof parsed === 'object') {
          return { ...DEFAULT_LOCAL_OPERATOR, ...parsed };
        }
      }
    } catch (_) {}
    return { ...DEFAULT_LOCAL_OPERATOR };
  }

  // Set authoritative local user immediately
  state.currentUser = getStoredLocalOperator();

  function resolveApiBaseUrl() {
    if (typeof window !== 'undefined') {
      if (window.__THERMOSAFE_API_URL__ && String(window.__THERMOSAFE_API_URL__).trim()) {
        return String(window.__THERMOSAFE_API_URL__).trim().replace(/\/+$/, '');
      }
      if (window.VITE_API_BASE_URL && String(window.VITE_API_BASE_URL).trim()) {
        return String(window.VITE_API_BASE_URL).trim().replace(/\/+$/, '');
      }
      try {
        const savedUrl = localStorage.getItem('thermosafe_api_url');
        if (savedUrl && savedUrl.trim()) {
          return savedUrl.trim().replace(/\/+$/, '');
        }
      } catch (_) {}
    }
    if (typeof process !== 'undefined' && process.env?.VITE_API_BASE_URL) {
      return String(process.env.VITE_API_BASE_URL).trim().replace(/\/+$/, '');
    }
    if (typeof window !== 'undefined' && window.location) {
      const host = window.location.hostname;
      const proto = window.location.protocol;
      if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0' || !host || proto === 'file:') {
        if (window.location.port === '8000') {
          return window.location.origin.replace(/\/+$/, '');
        }
        return 'http://127.0.0.1:8000';
      }
      return 'https://thermosafe-ai.onrender.com';
    }
    return 'https://thermosafe-ai.onrender.com';
  }

  const API_BASE_URL = resolveApiBaseUrl();

  const apiClient = {
    async request(endpoint, options = {}, retries = 1) {
      const url = `${API_BASE_URL}${endpoint}`;
      const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
      const token = localStorage.getItem('thermo_jwt_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const controller = new AbortController();
      const timeoutMs = options.timeout || 15000;
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

      let resp;
      try {
        resp = await fetch(url, { ...options, headers, signal: controller.signal });
      } catch (netErr) {
        clearTimeout(timeoutId);
        if (netErr.name === 'AbortError') {
          throw new Error('Backend service temporarily unavailable (request timeout).');
        }
        if (retries > 0) {
          await new Promise(r => setTimeout(r, 1000));
          return await this.request(endpoint, options, retries - 1);
        }
        throw new Error('Backend service temporarily unavailable. Please try again.');
      } finally {
        clearTimeout(timeoutId);
      }
      if (!resp.ok) {
        // Only invalidate stored token on genuine auth-check failure (/api/auth/me)
        if (resp.status === 401 && endpoint === '/api/auth/me') {
          console.warn('[ThermoSafe Debug] Stored token rejected on /api/auth/me. Resetting to local mode.');
          localStorage.removeItem('thermo_jwt_token');
          state.authToken = null;
          state.authStatus = 'local';
          updateAuthUI();
          // Never redirect to login on 401
        } else if (resp.status === 401) {
          console.warn(`[ThermoSafe Debug] Secondary endpoint returned 401: ${endpoint}. Suppressing session logout.`);
        }
        if (resp.status >= 500) {
          throw new Error('Backend service temporarily unavailable. Please try again.');
        }
        let errMsg = `Request failed: ${resp.status}`;
        try {
          const errData = await resp.json();
          if (Array.isArray(errData.detail)) {
            errMsg = errData.detail.map(d => d.msg || JSON.stringify(d)).join('; ');
          } else if (typeof errData.detail === 'string') {
            errMsg = errData.detail;
          } else if (errData.message) {
            errMsg = errData.message;
          }
        } catch (_) {}
        throw new Error(errMsg);
      }
      const cType = resp.headers.get('content-type') || '';
      if (cType.includes('application/json')) {
        return await resp.json();
      }
      return await resp.text();
    },

    async checkHealth(timeoutMs = 6000) {
      try {
        const data = await this.request('/health', { timeout: timeoutMs }, 0);
        return !!data && (data.status === 'ok' || data.status === 'healthy');
      } catch (e) {
        try {
          const apiData = await this.request('/api/health', { timeout: Math.min(timeoutMs, 4000) }, 0);
          return !!apiData && (apiData.status === 'ok' || apiData.status === 'healthy');
        } catch (_) {
          return false;
        }
      }
    },

    async login(email, password) {
      return await this.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
    },

    async signup(fullName, email, password, confirmPassword = null, role = 'analyst', operatorTeamId = null) {
      return await this.request('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword || password,
          role,
          operator_team_id: operatorTeamId
        })
      });
    },

    async getCurrentUser() {
      return await this.request('/api/auth/me');
    },

    async getOperatorTeams() {
      return await this.request('/api/operator-teams');
    },

    async getOperatorTeam(teamId) {
      return await this.request(`/api/operator-teams/${teamId}`);
    },

    async createOperatorTeam(data) {
      return await this.request('/api/operator-teams', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    },

    async updateOperatorTeam(teamId, data) {
      return await this.request(`/api/operator-teams/${teamId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    },

    async deleteOperatorTeam(teamId) {
      return await this.request(`/api/operator-teams/${teamId}`, {
        method: 'DELETE'
      });
    },

    async registerDevice(deviceData) {
      return await this.request('/api/devices/register', {
        method: 'POST',
        body: JSON.stringify(deviceData)
      });
    },

    async getDevices() {
      return await this.request('/api/devices');
    },

    async deleteDevice(deviceId) {
      return await this.request(`/api/devices/${deviceId}`, {
        method: 'DELETE'
      });
    },

    async getFcmStatus() {
      return await this.request('/api/alerts/fcm/status');
    },

    async sendFcmTest(payload = {}) {
      return await this.request('/api/alerts/fcm/test', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    },

    async getThermalEvents(pageSize = 100, isDemo = null) {
      let url = `/api/thermal-events?page_size=${pageSize}`;
      if (isDemo !== null) url += `&is_demo=${isDemo}`;
      return await this.request(url);
    },

    async simulateThermalEvent(eventType = 'Industrial Fire') {
      return await this.request('/api/thermal-events/simulate', {
        method: 'POST',
        body: JSON.stringify({ event_type: eventType })
      });
    },

    async getFacilities(pageSize = 100) {
      return await this.request(`/api/facilities?page_size=${pageSize}`);
    },

    async getAlerts(pageSize = 50) {
      return await this.request(`/api/alerts?page_size=${pageSize}`);
    },

    async getUnreadAlerts() {
      return await this.request('/api/alerts/unread');
    },

    async markAlertRead(alertId) {
      return await this.request(`/api/alerts/${alertId}/read`, { method: 'PUT' });
    },

    async acknowledgeAlert(alertId, operatorName = null) {
      return await this.request(`/api/alerts/${alertId}/acknowledge`, {
        method: 'PUT',
        body: JSON.stringify({ operator_name: operatorName })
      });
    },

    async escalateAlert(alertId) {
      return await this.request(`/api/alerts/${alertId}/escalate`, {
        method: 'POST'
      });
    },

    async getFirmsLive(days = 1) {
      return await this.request(`/api/firms/live?days=${days}`);
    },

    async getFirmsHealth() {
      return await this.request('/api/firms/health');
    },

    async getSatelliteThermalEvents(mode = 'live', country = 'IND', days = 1) {
      try {
        return await this.request(`/api/firms/live?days=${days}`);
      } catch (err) {
        return await this.request(`/api/satellite/thermal-events?mode=${mode}&country=${country}&days=${days}`);
      }
    },

    async getNearbyTeams(lat, lng, radiusKm = 100) {
      return await this.request(`/api/operator-teams/nearby?latitude=${lat}&longitude=${lng}&radius_km=${radiusKm}`);
    },

    async getAnalyticsSummary(isDemo = null) {
      let url = '/api/analytics/summary';
      if (isDemo !== null) url += `?is_demo=${isDemo}`;
      return await this.request(url);
    },

    async getRiskDistribution(isDemo = null) {
      let url = '/api/analytics/risk-distribution';
      if (isDemo !== null) url += `?is_demo=${isDemo}`;
      return await this.request(url);
    },

    async getEventTypes(isDemo = null) {
      let url = '/api/analytics/event-types';
      if (isDemo !== null) url += `?is_demo=${isDemo}`;
      return await this.request(url);
    },

    async getTimeSeries(isDemo = null) {
      let url = '/api/analytics/time-series';
      if (isDemo !== null) url += `?is_demo=${isDemo}`;
      return await this.request(url);
    },

    async getReports(pageSize = 20) {
      return await this.request(`/api/reports?page_size=${pageSize}`);
    },

    async createReport(payload) {
      return await this.request('/api/reports', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    },

    async exportReportCsv(reportId) {
      return await this.request(`/api/reports/${reportId}/export?format=csv`);
    },

    async classifyThermal(payload) {
      return await this.request('/api/ai/classify', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    },

    async analyzeRisk(payload) {
      return await this.request('/api/risk/analyze', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    }
  };

  /* ========== BACKEND TO FRONTEND DATA MAPPERS ========== */
  function mapBackendEvent(e) {
    const pUpper = (e.risk_priority || 'LOW').toUpperCase();
    const eventType = e.event_type || 'Industrial Fire';
    const classification = (e.ai_classification && e.ai_classification.classification) ||
                           (e.classifications && e.classifications[0]?.classification) ||
                           e.event_type || 'Industrial Fire';

    let city = 'Industrial Corridor';
    let stateName = 'India';
    if (e.facility && e.facility.address) {
      const parts = e.facility.address.split(',').map(p => p.trim());
      if (parts.length >= 3) {
        city = parts[parts.length - 3] || parts[0];
        stateName = parts[parts.length - 2] || 'India';
      } else {
        city = parts[0];
        stateName = parts[1] || 'India';
      }
    }

    const detectedStr = e.detected_at ? new Date(e.detected_at).toLocaleString() : 'Recent';
    const explanation = (e.classifications && e.classifications[0]?.explanation) ||
                        (e.ai_classification && e.ai_classification.explanation) ||
                        (e.risk_assessments && e.risk_assessments[0]?.explanation) ||
                        'Prototype multi-factor thermal telemetry risk analysis.';

    let factors = [
      { label:'Industrial proximity', pct:35 },
      { label:'Thermal signature', pct:30 },
      { label:'Persistence', pct:20 },
      { label:'Historical pattern', pct:10 },
      { label:'Land cover', pct:5 }
    ];

    if (e.risk_assessments && e.risk_assessments[0]) {
      const ra = e.risk_assessments[0];
      factors = [
        { label:'Thermal intensity factor', pct: Math.round((ra.thermal_factor || 0.35) * 100) },
        { label:'Persistence factor', pct: Math.round((ra.persistence_factor || 0.25) * 100) },
        { label:'Industrial proximity', pct: Math.round((ra.industrial_proximity_factor || 0.25) * 100) },
        { label:'Historical factor', pct: Math.round((ra.historical_factor || 0.1) * 100) },
        { label:'Population proximity', pct: Math.round((ra.population_proximity_factor || 0.05) * 100) }
      ];
    }

    const numConf = Number(
      (e.ai_classification && e.ai_classification.confidence !== undefined) ? e.ai_classification.confidence :
      (e.classifications && e.classifications[0]?.confidence !== undefined) ? e.classifications[0].confidence :
      (e.confidence !== undefined ? e.confidence : 0.9)
    );
    const confPct = Math.round(numConf <= 1 ? numConf * 100 : numConf);

    return {
      id: e.event_id || (e.id ? `TH-${e.id}` : 'TH-001'),
      event_id: e.event_id || (e.id ? `TH-${e.id}` : 'TH-001'),
      dbId: e.id,
      lat: Number(e.latitude),
      latitude: Number(e.latitude),
      lng: Number(e.longitude),
      longitude: Number(e.longitude),
      city: city,
      state: stateName,
      classification: classification,
      eventType: eventType,
      event_type: eventType,
      risk: pUpper,
      riskPriority: pUpper,
      risk_priority: pUpper,
      score: Math.round(Number(e.risk_score || 0)),
      riskScore: Math.round(Number(e.risk_score || 0)),
      risk_score: Number(e.risk_score || 0),
      confidence: confPct,
      intensity: e.thermal_intensity || 'HIGH',
      thermal_intensity: e.thermal_intensity || 'HIGH',
      persistence: e.persistence || 'Active',
      facility: e.facility ? e.facility.name : (e.facility_name || null),
      facility_name: e.facility ? e.facility.name : (e.facility_name || null),
      facilityOperator: e.facility ? e.facility.operator : null,
      landcover: e.land_cover || 'Industrial Area',
      land_cover: e.land_cover || 'Industrial Area',
      source: e.data_source || 'NASA FIRMS',
      data_source: e.data_source || 'NASA FIRMS',
      detected: detectedStr,
      detected_at: e.detected_at,
      explanation: explanation,
      factors: factors,
      raw: e
    };
  }

  function mapBackendFacility(f) {
    return {
      id: `FAC-${String(f.id).padStart(3, '0')}`,
      dbId: f.id,
      name: f.name,
      lat: Number(f.latitude),
      latitude: Number(f.latitude),
      lng: Number(f.longitude),
      longitude: Number(f.longitude),
      type: f.industry_type || 'Industrial Processing',
      industry_type: f.industry_type || 'Industrial Processing',
      capacity: f.risk_level || 'Medium',
      risk_level: f.risk_level || 'Medium',
      operator: f.operator || 'National Consortium',
      address: f.address || '',
      raw: f
    };
  }

  function mapBackendAlert(a) {
    const rawSev = (a.severity || a.risk_priority || 'low').toLowerCase();
    const level = rawSev.includes('crit') ? 'critical' : rawSev.includes('high') ? 'high' : 'low';
    let evId = a.event ? a.event.event_id : a.event_id;
    if (!evId && a.thermal_event_id) {
      evId = `TH-${a.thermal_event_id}`;
    }
    if (!evId) evId = 'TH-2026-00421';

    const numScore = a.risk_score !== undefined ? Math.round(Number(a.risk_score)) : 50;

    return {
      id: `ALT-${a.id || a.alert_id}`,
      alert_id: `ALT-${a.id || a.alert_id}`,
      dbId: a.id,
      level: level,
      severity: a.severity || a.risk_priority || 'High',
      riskPriority: a.risk_priority || a.severity || 'High',
      risk_priority: a.risk_priority || a.severity || 'High',
      title: a.title || 'Thermal Alert',
      msg: a.message || 'Thermal risk detected near monitored industrial zone.',
      message: a.message || 'Thermal risk detected near monitored industrial zone.',
      eventId: evId,
      event_id: evId,
      thermalEventId: a.thermal_event_id,
      thermal_event_id: a.thermal_event_id,
      time: a.created_at ? new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent',
      unread: !a.is_read,
      is_read: !!a.is_read,
      isAcknowledged: !!a.is_acknowledged,
      is_acknowledged: !!a.is_acknowledged,
      acknowledgedAt: a.acknowledged_at,
      acknowledged_at: a.acknowledged_at,
      acknowledgedBy: a.acknowledged_by,
      acknowledged_by: a.acknowledged_by,
      latitude: a.latitude !== undefined && a.latitude !== null ? Number(a.latitude) : null,
      lat: a.latitude !== undefined && a.latitude !== null ? Number(a.latitude) : null,
      longitude: a.longitude !== undefined && a.longitude !== null ? Number(a.longitude) : null,
      lng: a.longitude !== undefined && a.longitude !== null ? Number(a.longitude) : null,
      riskScore: numScore,
      risk_score: numScore,
      eventType: a.event_type || 'Industrial Fire',
      event_type: a.event_type || 'Industrial Fire',
      ts: a.created_at ? new Date(a.created_at).getTime() : Date.now(),
      raw: a
    };
  }

  /* ========== UTILS ========== */
  function getEventById(id) {
    if (!id) return null;
    const strId = String(id).trim().toLowerCase();
    return currentEvents.find(e => {
      if (String(e.id).toLowerCase() === strId) return true;
      if (e.dbId && String(e.dbId) === strId) return true;
      if (e.id && String(e.id).toLowerCase().replace('demo-evt-', '') === strId.replace('demo-evt-', '')) return true;
      if (strId.startsWith('th-') && e.dbId && `th-${e.dbId}` === strId) return true;
      return false;
    });
  }

  function timeAgo(ts) {
    const s = Math.floor((Date.now() - ts) / 1000);
    if (s < 60) return s + 's ago';
    if (s < 3600) return Math.floor(s/60) + 'm ago';
    if (s < 86400) return Math.floor(s/3600) + 'h ago';
    return Math.floor(s/86400) + 'd ago';
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }

  /* ========== TOASTS ========== */
  function showToast(title, msg, level, eventId) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast ' + (level || '').toLowerCase();
    toast.innerHTML = `
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-msg">${escapeHtml(msg)}</div>
      <div class="toast-actions">
        ${eventId ? `<button class="btn btn-primary btn-sm" onclick="window.__thermosafe.selectEvent('${eventId}')">View Event</button>` : ''}
        <button class="btn btn-outline btn-sm" onclick="this.closest('.toast').remove()">Dismiss</button>
      </div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      if (!toast.parentNode) return;
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(40px)';
      toast.style.transition = 'all 0.35s';
      setTimeout(() => toast.remove(), 350);
    }, 6500);
  }

  /* ========== NOTIFICATIONS & DRAWER ========== */
  function updateNotifBadge() {
    const unread = state.notifications.filter(n => n.unread).length;
    const badge = document.getElementById('notifCount');
    if (badge) {
      badge.textContent = unread;
      badge.style.display = unread > 0 ? 'flex' : 'none';
    }
  }

  function renderDrawer() {
    const body = document.getElementById('drawerBody');
    if (!body) return;

    const unread = state.notifications.filter(n => n.unread);
    const read = state.notifications.filter(n => !n.unread);

    function notifHtml(n) {
      const btnLabel = n.level === 'critical' ? 'View Event' : 'View on Map';
      const sev = (n.raw?.severity || n.level || 'High').toUpperCase();
      const evType = n.eventType || (n.raw?.event_type) || 'Industrial Anomaly';
      const rPriority = n.riskPriority || n.level?.toUpperCase() || 'HIGH';
      const rScore = n.riskScore ? `${n.riskScore}/100` : (n.raw?.risk_score ? `${n.raw.risk_score}/100` : '—');
      const locStr = (n.latitude && n.longitude) ? `${Number(n.latitude).toFixed(3)}°N, ${Number(n.longitude).toFixed(3)}°E` : 'Industrial Zone';
      const statusText = n.isAcknowledged ? `✓ Acknowledged` : (n.unread ? `● Unread` : `✓ Read`);
      const statusColor = n.isAcknowledged ? '#16A34A' : (n.unread ? '#DC2626' : '#7A8699');

      return `
        <div class="notif-item ${n.level} ${n.unread ? 'unread' : ''}" style="padding:12px;margin-bottom:8px;border-radius:8px;background:var(--bg-card);border:1px solid var(--border);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span class="risk-badge ${n.level === 'critical' ? 'risk-critical' : (n.level === 'high' ? 'risk-high' : 'risk-low')}" style="font-size:10px;padding:2px 6px;">
              ${escapeHtml(sev)}
            </span>
            <span style="font-size:11px;font-weight:700;color:${statusColor};">${escapeHtml(statusText)}</span>
          </div>
          <div class="notif-title" style="font-size:13px;font-weight:800;color:var(--navy);margin-bottom:4px;">${escapeHtml(n.title)}</div>
          <div class="notif-msg" style="font-size:12px;color:var(--text-secondary);margin-bottom:6px;line-height:1.4;">${escapeHtml(n.msg)}</div>
          
          <div style="font-size:11px;color:var(--text-muted);display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px;background:var(--bg-section);padding:6px 8px;border-radius:6px;border:1px solid var(--border);">
            <div>Ref: <b style="font-family:monospace;color:var(--navy);">${escapeHtml(n.eventId)}</b></div>
            <div>Type: <b style="color:var(--navy);">${escapeHtml(evType)}</b></div>
            <div>Loc: <span style="font-family:monospace;">${escapeHtml(locStr)}</span></div>
            <div>Risk: <b style="color:${n.level === 'critical' ? '#DC2626' : '#EA580C'};">${escapeHtml(rPriority)}</b> (${escapeHtml(rScore)})</div>
          </div>

          <div class="notif-meta" style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:8px;">
            <span>🕒 ${escapeHtml(n.time)}</span>
            <span>${timeAgo(n.ts)}</span>
          </div>

          <div class="notif-actions" style="display:flex;gap:6px;flex-wrap:wrap;">
            <button class="btn btn-primary btn-sm" style="flex:1;" onclick="window.__thermosafe.viewAlertOnMap('${n.id}');">${btnLabel}</button>
            ${!n.isAcknowledged ? `<button class="btn btn-success btn-sm" style="flex:1;" onclick="window.__thermosafe.acknowledge('${n.id}')">Acknowledge</button>` : `<span style="font-size:11px;color:#16A34A;font-weight:700;display:inline-flex;align-items:center;padding:0 6px;">✓ Ack</span>`}
            ${n.unread ? `<button class="btn btn-outline btn-sm" onclick="window.__thermosafe.markRead('${n.id}')">Mark Read</button>` : ''}
          </div>
        </div>
      `;
    }

    let html = '';
    if (unread.length) {
      html += `<div class="nav-section-label" style="padding:6px 4px 8px;display:flex;justify-content:space-between;align-items:center;"><span>Unread Alerts</span><span class="risk-badge risk-critical" style="font-size:10px;">${unread.length} new</span></div>`;
      html += unread.map(notifHtml).join('');
    }
    if (read.length) {
      html += `<div class="nav-section-label" style="padding:14px 4px 8px;">History (${read.length})</div>`;
      html += read.map(notifHtml).join('');
    }
    if (!unread.length && !read.length) {
      html = `<div style="text-align:center;padding:40px 10px;color:var(--text-muted);font-size:13px;">No notifications recorded</div>`;
    }

    body.innerHTML = html;
    updateNotifBadge();
  }

  function markRead(id) {
    const n = state.notifications.find(x => x.id === id);
    if (n) {
      n.unread = false;
      if (n.dbId) {
        apiClient.markAlertRead(n.dbId).catch(console.error);
      }
    }
    renderDrawer();
  }

  function markAllRead() {
    state.notifications.forEach(n => {
      n.unread = false;
      if (n.dbId) {
        apiClient.markAlertRead(n.dbId).catch(console.error);
      }
    });
    renderDrawer();
    showToast('Notifications', 'All notifications marked as read.', 'low');
  }

  function clearNotifications() {
    state.notifications = [];
    renderDrawer();
  }

  function addNotification(level, title, msg, eventId, extraData = {}) {
    // Prevent duplicate alert entries
    if (eventId && state.notifications.some(x => x.eventId === eventId && x.title === title)) {
      return;
    }
    const latVal = extraData.latitude !== undefined ? extraData.latitude : (extraData.lat !== undefined ? extraData.lat : null);
    const lngVal = extraData.longitude !== undefined ? extraData.longitude : (extraData.lng !== undefined ? extraData.lng : null);
    const rPriority = extraData.risk_priority || extraData.riskPriority || (level === 'critical' ? 'CRITICAL' : 'HIGH');
    const rScore = extraData.risk_score || extraData.riskScore || (level === 'critical' ? 92 : 78);
    const evType = extraData.event_type || extraData.eventType || 'Industrial Fire';

    const n = {
      id: 'NT-' + (++state.simCounter),
      level,
      title,
      msg,
      eventId: eventId || 'TH-2026-00421',
      eventType: evType,
      event_type: evType,
      time: new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }),
      unread: true,
      isAcknowledged: false,
      latitude: latVal,
      lat: latVal,
      longitude: lngVal,
      lng: lngVal,
      riskPriority: rPriority,
      risk_priority: rPriority,
      riskScore: rScore,
      risk_score: rScore,
      ts: Date.now()
    };
    state.notifications.unshift(n);
    if (state.dataSource === 'demo') {
      if (!DEMO_DATA.notifications.some(x => x.id === n.id)) {
        DEMO_DATA.notifications.unshift(n);
      }
    }
    renderDrawer();
    updateNotifBadge();
    showToast(title, msg, level, eventId);
  }

  function openDrawer() {
    renderDrawer();
    document.getElementById('notificationDrawer')?.classList.add('open');
    const b = document.getElementById('drawerBackdrop');
    if (b) b.style.display = 'block';
  }

  function closeDrawer() {
    document.getElementById('notificationDrawer')?.classList.remove('open');
    const b = document.getElementById('drawerBackdrop');
    if (b) b.style.display = 'none';
  }

  /* ========== BROWSER PUSH NOTIFICATIONS & DEVICE REGISTRATION ========== */
  async function registerCurrentDevice(pushToken = null) {
    let deviceId = localStorage.getItem('thermo_device_id');
    if (!deviceId) {
      deviceId = 'dev_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
      localStorage.setItem('thermo_device_id', deviceId);
    }
    const navUserAgent = navigator.userAgent || '';
    let browser = 'Chrome';
    if (navUserAgent.includes('Firefox')) browser = 'Firefox';
    else if (navUserAgent.includes('Safari') && !navUserAgent.includes('Chrome')) browser = 'Safari';
    else if (navUserAgent.includes('Edge')) browser = 'Edge';

    const platform = (navigator.userAgentData?.platform) || (navigator.platform) || (navUserAgent.includes('Android') ? 'Android' : 'Web');
    const perm = ('Notification' in window) ? Notification.permission : 'default';

    // Deduplicate registrations within the current session
    const regKey = `${deviceId}_${pushToken || 'default'}_${perm}_${state.currentUser ? state.currentUser.operator_team_id : 'none'}`;
    if (sessionStorage.getItem('thermo_last_reg') === regKey) {
      return null;
    }

    try {
      const res = await apiClient.registerDevice({
        device_identifier: deviceId,
        push_token: pushToken || `push_tok_${deviceId}`,
        platform: platform.toLowerCase().includes('android') ? 'android' : 'web',
        browser: browser,
        notification_permission: perm,
        operator_team_id: state.currentUser ? state.currentUser.operator_team_id : null
      });
      sessionStorage.setItem('thermo_last_reg', regKey);
      return res;
    } catch (e) {
      console.warn('Device push registration note:', e);
      return null;
    }
  }

  async function requestNotifPermission() {
    if (!('Notification' in window)) {
      showToast('Notifications Unavailable', 'This browser does not support Web Notifications.', 'low');
      return;
    }
    try {
      const perm = await Notification.requestPermission();
      state.browserNotifPermission = perm;
      if (perm === 'granted') {
        if ('serviceWorker' in navigator) {
          try {
            await navigator.serviceWorker.register('/firebase-messaging-sw.js');
          } catch (_) {}
        }
        await registerCurrentDevice('push_fcm_' + Date.now());
        showToast('Notifications Enabled', 'Browser push notifications active. Registered with command center.', 'low');
      } else {
        await registerCurrentDevice(null);
        showToast('Notifications Denied', 'Browser notification permission was not granted.', 'low');
      }
      if (state.currentPage === 'settings') renderSettingsPage();
    } catch (e) {
      console.warn('Notification permission error:', e);
    }
  }

  async function sendTestPushNotification() {
    showToast('Dispatching Push', 'Triggering FCM notification test...', 'low');
    try {
      const res = await apiClient.sendFcmTest({
        title: 'EMERGENCY TEST ALERT: Industrial Heat Signature',
        body: 'FCM push delivery test verified by ThermoSafe AI Command Center.'
      });
      if (res) {
        showToast('Push Dispatched', `Status: ${res.status || 'OK'} (${res.mode || 'simulated'}).`, 'low');
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('EMERGENCY TEST ALERT: Industrial Heat Signature', {
            body: 'ThermoSafe AI push delivery test active.',
            icon: '/vite.svg'
          });
        }
      }
    } catch (err) {
      showToast('Push Dispatch Note', err.message || 'Push test executed.', 'low');
    }
  }

  /* ========== LEAFLET MAP & MARKERS ========== */
  function initMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    if (state.map) {
      try {
        state.map.off();
        state.map.remove();
      } catch (e) {
        console.warn('[ThermoSafe Debug] map cleanup error', e);
      }
      state.map = null;
    }

    if (mapEl._leaflet_id) {
      delete mapEl._leaflet_id;
    }

    state.map = L.map('map', {
      center: [22.0, 77.0],
      zoom: 5,
      minZoom: 4,
        maxBounds: [
            [6.5, 68.0],
            [37.5, 97.5]
        ],
        maxBoundsViscosity: 1.0,
      zoomControl: true,
      attributionControl: true
    });

    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors | THERMOSAFE AI'
    });

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 18,
      attribution: 'Tiles &copy; Esri &mdash; Contextual Satellite Imagery (Does not independently prove fire)'
    });

    osmLayer.addTo(state.map);

    const baseMaps = {
      "OSM (Standard)": osmLayer,
      "Satellite (Contextual)": satelliteLayer
    };
    L.control.layers(baseMaps, null, { position: 'topright' }).addTo(state.map);

    state.thermalLayer = L.layerGroup().addTo(state.map);
    state.facilityLayer = L.layerGroup().addTo(state.map);

    renderMarkers();
    if (state.showFacilities) renderFacilities();
  }

  function makeThermalIcon(event, isHighlighted = false) {
    const colorObj = getEventColor(event);
    const color = colorObj.hex;
    const isCritical = (event.risk || event.risk_priority) === 'CRITICAL';
    const isHigh = (event.risk || event.risk_priority) === 'HIGH';
    const isDemo = event.data_source === 'DEMO' || event.is_demo;
    let size = isCritical ? 24 : isHigh ? 20 : 16;
    if (isHighlighted) size = Math.max(size + 8, 28);

    const pulseCls = isHighlighted ? 'pulse-critical' : (isCritical ? 'pulse-critical' : isHigh ? 'pulse-high' : '');
    const borderStyle = isHighlighted
      ? '3px solid #F59E0B'
      : (isDemo ? '2.5px dashed #A855F7' : '2.5px solid #FFFFFF');
    const boxShadow = isHighlighted
      ? '0 0 0 4px rgba(245, 158, 11, 0.6), 0 0 20px rgba(220, 38, 38, 0.7)'
      : (isDemo ? '0 0 0 2px rgba(168, 85, 247, 0.4), 0 2px 6px rgba(0,0,0,0.25)' : '0 0 0 1px rgba(11,37,69,0.35), 0 2px 6px rgba(0,0,0,0.25)');

    return L.divIcon({
      className: isHighlighted ? 'marker-highlight-active' : (isDemo ? 'marker-demo' : 'marker-live'),
      html: `<div class="${pulseCls}" style="
        width:${size}px;height:${size}px;border-radius:50%;
        background:${color};
        border:${borderStyle};
        box-shadow:${boxShadow};
        display:flex;align-items:center;justify-content:center;
        transition:all 0.3s ease;
        "><div style="width:4px;height:4px;border-radius:50%;background:#FFFFFF;"></div></div>`,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
      popupAnchor: [0, -size/2]
    });
  }

  function makeFacilityIcon() {
    return L.divIcon({
      className: '',
      html: `<div style="
        width:16px;height:16px;background:#2563EB;
        border:2.5px solid #FFFFFF;
        box-shadow:0 0 0 1px rgba(11,37,69,0.35), 0 2px 6px rgba(0,0,0,0.25);
        display:flex;align-items:center;justify-content:center;
        border-radius:3px;
        "><svg width="8" height="8" fill="white" viewBox="0 0 24 24"><path d="M3 21h18V8l-8-5-8 5v13zm10-11h-2v2H9v-2H7v4h2v-2h2v2h2v-4z"/></svg></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
      popupAnchor: [0, -8]
    });
  }

  function renderMarkers() {
    if (!state.thermalLayer) return;
    state.thermalLayer.clearLayers();
    state.markers = {};
    state.heatmapData = [];

    currentEvents.forEach(ev => {
      const isSelected = state.selectedEvent && (state.selectedEvent.id === ev.id || state.selectedEvent.dbId === ev.dbId);
      const marker = L.marker([ev.lat, ev.lng], {
        icon: makeThermalIcon(ev, isSelected),
        title: ev.id
      });

      const latFmt = (ev.lat || ev.latitude || 0).toFixed(4);
      const lngFmt = (ev.lng || ev.longitude || 0).toFixed(4);
      const evtType = ev.eventType || ev.event_type || ev.classification || 'Industrial Fire';
      const riskVal = (ev.risk || ev.risk_priority || 'HIGH').toUpperCase();
      const scoreVal = ev.score !== undefined ? ev.score : (ev.risk_score !== undefined ? ev.risk_score : 85);
      const confVal = ev.confidence !== undefined ? ev.confidence : 95;
      const intensityVal = ev.intensity || ev.thermal_intensity || 'High (850 MW)';
      const detectVal = ev.detected || ev.detected_at || 'Just now';
      const locStr = `${ev.city || 'Industrial Zone'}, ${ev.state || 'India'}`;

      const isDemo = ev.data_source === 'DEMO' || ev.is_demo;
      const srcBadge = isDemo
        ? '<span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#F3E8FF;color:#6B21A8;font-weight:700;">DEMO</span>'
        : '<span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#DCFCE7;color:#166534;font-weight:700;">NASA LIVE</span>';

      marker.bindPopup(`
        <div style="min-width:260px;font-family:'Source Serif 4',Georgia,serif;padding:2px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;border-bottom:1px solid #E2E8F0;padding-bottom:4px;">
            <span style="font-weight:800;font-size:14px;color:#0B2545;">${escapeHtml(ev.id)}</span>
            <div style="display:flex;gap:4px;align-items:center;">
              ${srcBadge}
              ${riskBadge(riskVal)}
            </div>
          </div>
          <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px; border-radius:8px; min-width:210px; font-size:12px; line-height:1.6;">
  <div><b>Event ID:</b> <span style="font-family:monospace;">${escapeHtml(String(ev.id || 'N/A'))}</span></div>
  <div><b>Data Source:</b> ${isDemo ? '<span style="color:#7C3AED;font-weight:600;">DEMO</span>' : '<span style="color:#059669;font-weight:600;">NASA FIRMS LIVE</span>'}</div>
  <div><b>Location:</b> ${escapeHtml(String(ev.city || ev.location || (ev.lat != null ? ev.lat.toFixed(3) + ', ' + ev.lng.toFixed(3) : 'Perimeter')))}</div>
  <div><b>Latitude:</b> <span style="font-family:monospace;">${ev.lat != null ? ev.lat.toFixed(4) : 'N/A'}</span></div>
  <div><b>Longitude:</b> <span style="font-family:monospace;">${ev.lng != null ? ev.lng.toFixed(4) : 'N/A'}</span></div>
  <div><b>Event Type:</b> ${escapeHtml(String(ev.event_type || ev.type || 'Thermal Anomaly'))}</div>
  <div><b>AI Classification:</b> <span style="font-weight:600; color:#0284C7;">${escapeHtml(String(ev.classification || ev.ai_classification || (isDemo ? 'Unclassified' : 'Active Hotspot')))}</span></div>
  <div><b>AI Confidence:</b> <b>${ev.confidence != null ? ev.confidence : 85}%</b></div>
  <div><b>Risk Priority:</b> ${typeof riskBadge === 'function' ? riskBadge(ev.risk || ev.risk_priority || 'HIGH') : (ev.risk || 'HIGH')}</div>
  <div><b>Thermal Intensity:</b> ${escapeHtml(String(ev.frp != null ? ev.frp : (ev.brightness != null ? ev.brightness : (ev.intensity || 'N/A'))))} MW</div>
</div>
<button onclick="window.__thermosafe ? window.__thermosafe.viewFullAnalysis('${ev.id}') : viewFullAnalysis('${ev.id}')"
  style="margin-top:8px; width:100%; background:#1E5AA8; color:white; border:none; padding:7px 12px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer; font-family:inherit; box-shadow:0 1px 3px rgba(0,0,0,0.15);">
  View Full Analysis
</button>
      `);

      marker.on('click', () => {
        if (window.innerWidth <= 900) {
          openBottomSheet(ev.id);
        } else {
          selectEvent(ev.id);
        }
      });

      marker.addTo(state.thermalLayer);
      state.markers[ev.id] = marker;
      state.heatmapData.push([ev.lat, ev.lng, Math.min(1, ev.score / 100)]);
    });
  }

  function renderFacilities() {
    if (!state.facilityLayer) return;
    state.facilityLayer.clearLayers();
    currentFacilities.forEach(f => {
      const m = L.marker([f.lat, f.lng], { icon: makeFacilityIcon(), title: f.name });
      m.bindPopup(`
        <div style="min-width:200px;font-family:'Source Serif 4',Georgia,serif;">
          <div style="font-weight:800;font-size:13px;color:#0B2545;margin-bottom:4px;">${escapeHtml(f.name)}</div>
          <div style="font-size:11px;color:#4A5568;margin-bottom:4px;">Facility ID: ${f.id}</div>
          <div style="font-size:12px;color:#0B2545;"><b>Type:</b> ${escapeHtml(f.type)}</div>
          <div style="font-size:12px;color:#0B2545;"><b>Operator:</b> ${escapeHtml(f.operator || 'Industrial')}</div>
          <div style="font-size:12px;color:#0B2545;"><b>Risk Level:</b> ${escapeHtml(f.capacity)}</div>
        </div>
      `);
      m.addTo(state.facilityLayer);
    });
  }

  function toggleHeatmap() {
    state.showHeatmap = !state.showHeatmap;
    if (state.showHeatmap) {
      showToast('Heatmap Enabled', 'Displaying composite thermal risk density.', 'low');
    } else {
      showToast('Heatmap Disabled', 'Default pin marker mode active.', 'low');
    }
  }

  /* ========== EVENT SELECTION & AI PANEL ========== */
  function selectEvent(id) {
    const ev = getEventById(id);
    if (!ev) return;
    state.selectedEvent = ev;

    if (state.map) {
      state.map.setView([ev.lat, ev.lng], 8, { animate: true });
    }

    const panel = document.getElementById('ai-panel-content');
    if (window.innerWidth <= 900 || !panel) {
      openBottomSheet(id);
    } else {
      renderAIPanel(ev);
    }

    const color = getEventColor(ev);
    showToast(
      `Selected: ${ev.classification}`,
      `${ev.id} · ${ev.city} · Risk ${ev.risk} · Confidence ${ev.confidence}%`,
      color.clsShort,
      ev.id
    );
  }

  function openBottomSheet(id) {
    const ev = getEventById(id);
    if (!ev) return;
    state.selectedEvent = ev;
    const sheet = document.getElementById('bottomSheet');
    const content = document.getElementById('sheetContent');
    if (!sheet || !content) return;

    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div style="font-weight:800;font-size:15px;color:#0B2545;">${escapeHtml(ev.id)}</div>
        ${riskBadge(ev.risk)}
      </div>
      <div style="font-size:12px;color:#4A5568;margin-bottom:10px;">${escapeHtml(ev.city)}, ${escapeHtml(ev.state)}</div>
      <div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;">
        ${classBadge(ev.classification)}
      </div>
      <div class="detail-row"><span class="detail-label">Event Type</span><span class="detail-value">${escapeHtml(ev.eventType || ev.classification)}</span></div>
      <div class="detail-row"><span class="detail-label">AI Classification</span><span class="detail-value">${escapeHtml(ev.classification)}</span></div>
      <div class="detail-row"><span class="detail-label">Risk Priority</span><span class="detail-value">${riskBadge(ev.risk)}</span></div>
      <div class="detail-row"><span class="detail-label">Risk Score</span><span class="detail-value">${ev.score}/100</span></div>
      <div class="detail-row"><span class="detail-label">AI Confidence</span><span class="detail-value">${ev.confidence}%</span></div>
      <div class="detail-row"><span class="detail-label">Coordinates</span><span class="detail-value font-mono">${ev.lat.toFixed(4)}° N, ${ev.lng.toFixed(4)}° E</span></div>
      <div class="detail-row"><span class="detail-label">Thermal Intensity</span><span class="detail-value">${ev.intensity}</span></div>
      <div class="detail-row"><span class="detail-label">Persistence</span><span class="detail-value">${ev.persistence}</span></div>
      <div class="detail-row"><span class="detail-label">Nearby Facility</span><span class="detail-value">${escapeHtml(ev.facility || '—')}</span></div>
      <div class="detail-row"><span class="detail-label">Detection Time</span><span class="detail-value font-mono">${ev.detected}</span></div>
      <div style="margin-top:10px;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;">AI Explanation</div>
      <div style="margin-top:4px;font-size:12px;color:var(--text-secondary);line-height:1.5;background:var(--bg-section);padding:8px;border-radius:6px;border:1px solid var(--border);">${escapeHtml(ev.explanation)}</div>

      <button class="btn btn-primary btn-block mt-3" onclick="window.__thermosafe.closeBottomSheet(); window.__thermosafe.viewFullAnalysis('${ev.id}');">
        View Full Analysis
      </button>
    `;
    sheet.classList.add('open');
  }

  function closeBottomSheet() {
    document.getElementById('bottomSheet')?.classList.remove('open');
  }

  function closeAnalysisModal() {
    const modal = document.getElementById('analysisModal');
    const backdrop = document.getElementById('analysisBackdrop');
    if (modal) modal.style.display = 'none';
    if (backdrop) backdrop.style.display = 'none';
  }

  function openAnalysisModal(id) {
    const ev = getEventById(id);
    if (!ev) return;
    state.selectedEvent = ev;
    const modal = document.getElementById('analysisModal');
    const backdrop = document.getElementById('analysisBackdrop');
    const body = document.getElementById('analysisModalBody');
    if (!modal || !backdrop || !body) return;

    const color = getEventColor(ev);
    const isDemo = ev.data_source === 'DEMO' || ev.is_demo;
    const factors = ev.factors || [
      { label:'Proximity to Facility', pct:35 },
      { label:'Thermal Intensity', pct:25 },
      { label:'Persistence', pct:20 },
      { label:'Historical Frequency', pct:10 },
      { label:'Environmental Vulnerability', pct:10 }
    ];

    const notif = state.notifications.find(n => n.eventId === ev.id || n.id === ev.id);
    const isAck = notif ? !!notif.isAcknowledged : false;
    const ackStatusStr = isAck ? '✓ Acknowledged' : 'Pending Acknowledgement';
    const ackStatusColor = isAck ? '#16A34A' : '#DC2626';

    const deliveryStatusStr = isAck ? 'DELIVERED' : (state.fcmStatus && state.fcmStatus.mode === 'live' ? 'SENT' : 'CONFIGURATION_REQUIRED');
    const assignedTeamName = ev.facilityOperator || 'Jamnagar Industrial Fire & Hazmat Battalion';

    let protocolStr = 'Standard Incident Response: Verify sensor telemetry, dispatch automated alerts, standby for confirmation.';
    const rPriority = (ev.risk || ev.risk_priority || 'MEDIUM').toUpperCase();
    if (rPriority === 'CRITICAL') {
      protocolStr = 'CRITICAL TIER-1 PROTOCOL: Immediate facility shutdown alert, emergency containment dispatch, activate perimeter sensors, notify district disaster control.';
    } else if (rPriority === 'HIGH') {
      protocolStr = 'HIGH PRIORITY TIER-2 PROTOCOL: Deploy nearest hazardous material response unit, inspect flare knockout drums, cross-check gas emissions telemetry.';
    } else if ((ev.classification || '').includes('Gas') || (ev.classification || '') === 'GAS_FLARE') {
      protocolStr = 'GAS FLARE PROTOCOL: Monitor combustion efficiency, verify flare stack temperature thresholds, log continuous emission monitoring system (CEMS).';
    }

    const frpVal = ev.frp ? `${ev.frp} MW` : (ev.thermal_intensity || ev.intensity || '420.0 MW');
    const satVal = ev.satellite || (isDemo ? 'VIIRS NOAA-20 (Demo Reference)' : 'NASA FIRMS VIIRS / MODIS');
    const groupVal = ev.industrial_natural_group || ((ev.classification || '').includes('Forest') || (ev.classification || '').includes('Agricultural') ? 'Natural / Rural' : 'Industrial');
    const distVal = ev.facilityDistance !== undefined ? `${Number(ev.facilityDistance).toFixed(1)} km` : (ev.facility_distance ? `${Number(ev.facility_distance).toFixed(1)} km` : '1.2 km');
    const facVal = ev.facility || ev.facility_name || 'Jamnagar Integrated Refinery Complex';
    const evidVal = ev.evidence || ev.explanation || 'Thermal radiance pattern and multi-spectral signature analyzed.';

    body.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;flex-wrap:wrap;gap:8px;border-bottom:1px solid var(--border);padding-bottom:10px;">
        <div>
          <div style="font-weight:800;font-size:18px;color:#0B2545;">${escapeHtml(ev.id)}</div>
          <div style="font-size:12px;color:#4A5568;margin-top:2px;">${escapeHtml(ev.city || 'Industrial Complex')}, ${escapeHtml(ev.country || ev.state || 'India')}</div>
        </div>
        <div style="display:flex;gap:6px;align-items:center;">
          <span style="font-size:11px;padding:3px 8px;border-radius:12px;background:${isDemo ? '#F3E8FF' : '#DCFCE7'};color:${isDemo ? '#6B21A8' : '#166534'};font-weight:700;">
            ${isDemo ? '● DEMO DATA' : '● NASA FIRMS LIVE'}
          </span>
          ${classBadge(ev.classification)}
          ${riskBadge(rPriority)}
        </div>
      </div>

      <!-- SECTION 1: EVENT INFORMATION -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>📋</span> 1. EVENT INFORMATION
        </div>
        <div style="background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);font-size:12px;">
          <div class="detail-row"><span class="detail-label">Event ID</span><span class="detail-value font-mono font-bold">${escapeHtml(ev.id)}</span></div>
          <div class="detail-row"><span class="detail-label">Data Source</span><span class="detail-value font-bold" style="color:${isDemo ? '#6B21A8' : '#166534'};">${isDemo ? 'DEMO (Simulated Reference)' : 'NASA FIRMS (Live Satellite Telemetry)'}</span></div>
          <div class="detail-row"><span class="detail-label">Location</span><span class="detail-value font-mono">${(ev.lat || 0).toFixed(4)}° N, ${(ev.lng || 0).toFixed(4)}° E (${escapeHtml(ev.city || 'Zone')}, ${escapeHtml(ev.state || ev.country || 'India')})</span></div>
          <div class="detail-row"><span class="detail-label">Latitude</span><span class="detail-value font-mono">${(ev.lat || ev.latitude || 0).toFixed(4)}° N</span></div>
          <div class="detail-row"><span class="detail-label">Longitude</span><span class="detail-value font-mono">${(ev.lng || ev.longitude || 0).toFixed(4)}° E</span></div>
          <div class="detail-row"><span class="detail-label">Acquisition Date/Time</span><span class="detail-value font-mono">${escapeHtml(ev.detected || ev.detected_at || 'Real-time')}</span></div>
          <div class="detail-row"><span class="detail-label">Detection Time</span><span class="detail-value font-mono">${escapeHtml(ev.detected || ev.detected_at || 'Real-time')}</span></div>
          <div class="detail-row"><span class="detail-label">Satellite</span><span class="detail-value">${escapeHtml(satVal)}</span></div>
          <div class="detail-row"><span class="detail-label">FRP (Fire Radiative Power)</span><span class="detail-value font-mono font-bold" style="color:#DC2626;">${escapeHtml(frpVal)}</span></div>
        </div>
      </div>

      <!-- SECTION 2: AI ANALYSIS -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>🤖</span> 2. AI ANALYSIS
        </div>
        <div style="background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);font-size:12px;">
          <div class="detail-row"><span class="detail-label">Classification</span><span class="detail-value" style="color:${color.hex};font-weight:800;">${escapeHtml(ev.classification)}</span></div>
          <div class="detail-row"><span class="detail-label">Industrial/Natural Group</span><span class="detail-value font-bold">${escapeHtml(groupVal)}</span></div>
          <div class="detail-row"><span class="detail-label">Confidence</span><span class="detail-value" style="color:#1E5AA8;font-weight:800;">${ev.confidence || 90}%</span></div>
          <div class="detail-row"><span class="detail-label">Model</span><span class="detail-value font-mono" style="font-weight:700;">ThermalEnsemble-v2</span></div>
          <div class="detail-row"><span class="detail-label">Evidence</span><span class="detail-value">${escapeHtml(evidVal)}</span></div>
          <div style="margin-top:6px;padding-top:6px;border-top:1px dashed var(--border);font-size:11px;color:var(--text-secondary);line-height:1.5;">
            <b>Explanation:</b> ${escapeHtml(ev.explanation || 'Thermal signature evaluated using multi-spectral radiance thresholds.')}
          </div>
        </div>
      </div>

      <!-- SECTION 3: RISK ANALYSIS -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>⚠️</span> 3. RISK ANALYSIS
        </div>
        <div style="background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);font-size:12px;">
          <div class="detail-row"><span class="detail-label">Risk Score</span><span class="detail-value" style="color:#DC2626;font-weight:800;font-size:14px;">${ev.score || ev.risk_score || 85}/100</span></div>
          <div class="detail-row"><span class="detail-label">Risk Level</span><span class="detail-value">${riskBadge(rPriority)}</span></div>
          <div class="detail-row"><span class="detail-label">Risk Priority</span><span class="detail-value">${riskBadge(rPriority)}</span></div>
          <div class="detail-row"><span class="detail-label">Persistence</span><span class="detail-value font-mono">${escapeHtml(ev.persistence || '3.5 hours')}</span></div>
          
          <div style="margin-top:8px;margin-bottom:6px;">
            <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px;">Multi-Factor Breakdown (5 Factors)</div>
            <div style="display:flex;flex-direction:column;gap:5px;">
              ${factors.map(f => `
                <div style="font-size:11px;">
                  <div style="display:flex;justify-content:space-between;color:#4A5568;margin-bottom:2px;font-weight:600;">
                    <span>${f.label}</span>
                    <span style="font-weight:800;color:#0B2545;">${f.pct}%</span>
                  </div>
                  <div class="progress-track" style="height:5px;">
                    <div class="progress-fill" style="width:${f.pct}%;background:#1E5AA8;"></div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
          <div style="margin-top:6px;padding-top:6px;border-top:1px dashed var(--border);font-size:11px;color:var(--text-secondary);line-height:1.5;">
            <b>Risk Explanation:</b> ${escapeHtml(ev.riskExplanation || ev.explanation || 'Composite multi-factor calculation based on industrial proximity, radiance, persistence, and frequency.')}
          </div>
        </div>
      </div>

      <!-- SECTION 4: FACILITY -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>🏭</span> 4. FACILITY
        </div>
        <div style="background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);font-size:12px;">
          <div class="detail-row"><span class="detail-label">Closest Facility Name</span><span class="detail-value font-bold">${escapeHtml(facVal)}</span></div>
          <div class="detail-row"><span class="detail-label">Nearest Facility</span><span class="detail-value font-bold">${escapeHtml(facVal)}</span></div>
          <div class="detail-row"><span class="detail-label">Facility Type</span><span class="detail-value">${escapeHtml(ev.facilityType || 'Petrochemical / Refining')}</span></div>
          <div class="detail-row"><span class="detail-label">Operator</span><span class="detail-value">${escapeHtml(ev.facilityOperator || 'Reliance Industries / Petrochemical Division')}</span></div>
          <div class="detail-row"><span class="detail-label">Distance</span><span class="detail-value font-mono">${escapeHtml(distVal)}</span></div>
          <div class="detail-row"><span class="detail-label">Distance to Facility</span><span class="detail-value font-mono">${escapeHtml(distVal)}</span></div>
          <div class="detail-row"><span class="detail-label">Facility Risk Level</span><span class="detail-value"><span class="risk-badge risk-high" style="font-size:10px;">HIGH VULNERABILITY</span></span></div>
        </div>
      </div>

      <!-- SECTION 5: RESPONSE -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:#166534;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>🚒</span> 5. RESPONSE
        </div>
        <div id="modalOperatorTeamCard" style="background:#F0FDF4;padding:10px 12px;border-radius:6px;border:1px solid #BBF7D0;font-size:12px;">
          <div class="detail-row"><span class="detail-label">Assigned Operator Team</span><span class="detail-value font-bold" id="respTeamName">${escapeHtml(assignedTeamName)}</span></div>
          <div class="detail-row"><span class="detail-label">Notification Status</span><span class="detail-value font-mono font-bold" id="respNotifStatus" style="color:#15803D;">${escapeHtml(deliveryStatusStr)}</span></div>
          <div class="detail-row"><span class="detail-label">Acknowledgement Status</span><span class="detail-value font-bold" id="respAckStatus" style="color:${ackStatusColor};">${escapeHtml(ackStatusStr)}</span></div>
          <div style="margin-top:6px;padding-top:6px;border-top:1px dashed #BBF7D0;font-size:11px;color:#166534;line-height:1.5;">
            <b>Recommended Response Protocol:</b><br>${escapeHtml(protocolStr)}
          </div>
        </div>
      </div>

      <div style="display:flex;gap:8px;margin-top:16px;">
        <button class="btn btn-primary btn-block" onclick="window.__thermosafe.closeAnalysisModal(); window.__thermosafe.viewAlertOnMap('${ev.id}');">View on Live Map</button>
        <button class="btn btn-outline btn-block" onclick="window.__thermosafe.closeAnalysisModal();">Close</button>
      </div>
    `;

    // Query nearby emergency team asynchronously
    apiClient.getNearbyTeams(ev.lat, ev.lng, 100).then(res => {
      const items = (res && (res.items || res.nearby_teams)) || [];
      if (items.length > 0) {
        const match = items[0];
        const topTeam = match.team || match;
        const distStr = match.distance_km !== undefined ? `${match.distance_km.toFixed(1)} km` : 'Proximity Dispatch';
        const teamEl = document.getElementById('respTeamName');
        if (teamEl) {
          teamEl.textContent = `${topTeam.name} (${distStr})`;
        }
      }
    }).catch(()=>{});

    modal.style.display = 'block';
    backdrop.style.display = 'block';
  }

  function viewFullAnalysis(id) {
        let ev = (typeof getEventById === 'function') ? getEventById(id) : null;

        // If clicked on a facility (starts with FAC- or found in facilities list), construct incident analysis data
        if (!ev && window.state && Array.isArray(state.currentFacilities)) {
            const fac = state.currentFacilities.find(f => f.id === id);
            if (fac) {
                ev = {
                    id: fac.id,
                    name: fac.name,
                    city: fac.name,
                    location: `${fac.lat.toFixed(4)}, ${fac.lng.toFixed(4)} (${fac.name})`,
                    lat: fac.lat,
                    lng: fac.lng,
                    classification: "INDUSTRIAL_FIRE",
                    event_type: "INDUSTRIAL_FIRE",
                    risk: fac.risk || "HIGH",
                    risk_score: 92,
                    confidence: 94,
                    frp: 620,
                    intensity: 620,
                    satellite: "MODIS/VIIRS Active Monitoring",
                    explanation: `High thermal intensity and continuous monitoring registered at ${fac.name}. Baseline industrial thermal levels active.`
                };
            }
        }

        if (!ev) return;
        state.selectedEvent = ev;

        if (state.map && ev.lat != null && ev.lng != null) {
            state.map.setView([ev.lat, ev.lng], 9, { animate: true });
        }

        if (typeof renderAIPanel === 'function') {
            renderAIPanel(ev);
        }
        if (typeof openAnalysisModal === 'function') {
            openAnalysisModal(ev.id);
        }
    }

  function renderAIPanel(ev) {
    const panel = document.getElementById('ai-panel-content');
    if (!panel) return;

    if (!ev) {
      panel.innerHTML = `
        <div style="text-align:center;padding:24px 0;color:#7A8699;font-size:13px;line-height:1.6;">
          <div style="font-size:36px;margin-bottom:10px;opacity:0.5;">🛰️</div>
          Select a thermal marker on the map<br>to view AI classification.
        </div>
      `;
      return;
    }

    const color = getEventColor(ev);
    const factors = ev.factors || [
      { label:'Industrial proximity', pct:35 },
      { label:'Thermal signature', pct:30 },
      { label:'Persistence', pct:20 },
      { label:'Historical pattern', pct:10 },
      { label:'Land cover', pct:5 }
    ];

    panel.innerHTML = `
      <div style="animation:fadeIn 0.3s ease;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <div style="font-weight:800;font-size:14px;color:#0B2545;">${escapeHtml(ev.id)}</div>
          ${riskBadge(ev.risk)}
        </div>
        <div style="font-size:11px;color:#4A5568;margin-bottom:12px;">${escapeHtml(ev.city)}, ${escapeHtml(ev.state)} · ${ev.detected}</div>

        <div style="font-size:10px;color:#7A8699;text-transform:uppercase;letter-spacing:0.8px;font-weight:700;margin-bottom:4px;">Event Type</div>
        <div style="margin-bottom:12px;">${classBadge(ev.eventType || ev.classification)}</div>

        <div style="font-size:10px;color:#7A8699;text-transform:uppercase;letter-spacing:0.8px;font-weight:700;margin-bottom:4px;">AI Classification</div>
        <div style="font-weight:700;font-size:14px;color:${color.hex};margin-bottom:12px;">${escapeHtml(ev.classification)}</div>

        <div style="display:flex;justify-content:space-between;font-size:11px;color:#4A5568;margin-bottom:4px;font-weight:600;">
          <span>AI Confidence</span><span style="color:#0B2545;font-weight:800;">${ev.confidence}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${ev.confidence}%;background:linear-gradient(90deg,#0891B2,#1E5AA8);"></div>
        </div>

        <div style="display:flex;justify-content:space-between;font-size:11px;color:#4A5568;margin:10px 0 4px;font-weight:600;">
          <span>Risk Score</span><span style="color:#0B2545;font-weight:800;">${ev.score}/100</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${ev.score}%;background:${getRiskColor(ev.risk)};"></div>
        </div>

        <div style="margin-top:16px;font-size:10px;color:#7A8699;text-transform:uppercase;letter-spacing:0.8px;font-weight:700;margin-bottom:8px;">AI Explanation</div>
        <div style="font-size:12px;color:var(--text-secondary);line-height:1.5;margin-bottom:10px;background:var(--bg-section);padding:8px 10px;border-radius:6px;border:1px solid var(--border);">
          ${escapeHtml(ev.explanation)}
        </div>

        ${factors.map(f => `
          <div style="font-size:11px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:3px;color:#4A5568;font-weight:600;">
              <span>${f.label}</span>
              <span style="color:#0B2545;font-weight:800;">${f.pct}%</span>
            </div>
            <div class="progress-track" style="height:5px;">
              <div class="progress-fill" style="width:${f.pct}%;background:#1E5AA8;"></div>
            </div>
          </div>
        `).join('')}

        <div style="margin-top:16px;padding-top:12px;border-top:1px solid #D6E2EF;">
          <div class="detail-row"><span class="detail-label">Thermal Intensity</span><span class="detail-value">${ev.intensity}</span></div>
          <div class="detail-row"><span class="detail-label">Persistence</span><span class="detail-value">${ev.persistence}</span></div>
          <div class="detail-row"><span class="detail-label">Coordinates</span><span class="detail-value font-mono" style="font-size:11px;">${ev.lat.toFixed(4)}° N, ${ev.lng.toFixed(4)}° E</span></div>
          <div class="detail-row"><span class="detail-label">Nearby Facility</span><span class="detail-value">${escapeHtml(ev.facility || '—')}</span></div>
          <div class="detail-row"><span class="detail-label">Detection Time</span><span class="detail-value font-mono">${ev.detected}</span></div>
          <div class="detail-row"><span class="detail-label">Land Cover</span><span class="detail-value">${ev.landcover}</span></div>
          <div class="detail-row"><span class="detail-label">Source</span><span class="detail-value">${ev.source}</span></div>
        </div>

        <div class="btn-grid" style="margin-top:14px;">
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.navigateTo('reports')">Generate Report</button>
          <button class="btn btn-danger btn-sm" onclick="window.__thermosafe.createAlertFromEvent('${ev.id}')">Create Alert</button>
        </div>
        <button class="btn btn-primary btn-block btn-sm" style="margin-top:8px;" onclick="window.__thermosafe.trackEvent('${ev.id}')">Track Event</button>

        <div style="margin-top:14px;font-size:10px;color:#7A8699;text-align:center;line-height:1.5;">
          ${state.dataSource === 'live' ? (state.backendConnected ? '🟢 Live Data — Connected to Live AI Backend & FIRMS Telemetry' : '🟡 Live Data — Reconnecting to Backend...') : '🟡 DEMO MODE — Local simulated events & scenario controls'}
        </div>
      </div>
    `;
  }

  function createAlertFromEvent(id) {
    const ev = getEventById(id);
    if (!ev) return;
    addNotification(
      (ev.risk || ev.riskPriority) === 'CRITICAL' ? 'critical' : 'high',
      `${ev.classification || ev.eventType} — Alert Created`,
      `Alert generated for ${ev.city}. Risk: ${ev.risk || ev.riskPriority}. AI Confidence: ${ev.confidence}%.`,
      ev.id
    );
  }

  function trackEvent(id) {
    const ev = getEventById(id);
    if (!ev) return;
    showToast('Tracking Event', `Now tracking ${ev.id}. Updates will appear in the live feed.`, 'low', ev.id);
  }

  /* ========== PAGE RENDERERS ========== */
  function renderDashboard() {
    const content = document.getElementById('content');
    if (!content) return;

    state.dashboardMountCount++;
    console.log(`[ThermoSafe Debug] Full Dashboard Mounted (count: ${state.dashboardMountCount}, source: ${state.dataSource})`);

    const s = (state.dataSource === 'live' && state.backendAnalytics) ? state.backendAnalytics.summary : null;
    const totalEvents = s ? s.total_thermal_events : currentEvents.length;
    const critEvents = s ? s.critical_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'CRITICAL').length;
    const highEvents = s ? s.high_risk_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'HIGH').length;
    const modEvents = s ? s.moderate_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'MEDIUM' || (e.classification || '').includes('Gas')).length;
    const lowEvents = s ? s.low_risk_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'LOW').length;
    const facCount = s ? s.industrial_facilities : currentFacilities.length;

    content.innerHTML = `
      <div class="dashboard-header-banner" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;padding:10px 16px;background:#FFFFFF;border:1px solid #D6E2EF;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.05);flex-wrap:wrap;gap:8px;">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
          <span style="font-weight:800;font-size:13px;color:#0B2545;letter-spacing:0.5px;">
            DATA SOURCE: <span id="dashSourceLabel" style="color:${getSourceLabelColor()};">${getSourceLabelText()}</span>
          </span>
          <span id="dashLiveStatus" style="font-size:11px;padding:2px 8px;border-radius:12px;background:${getLiveStatusBadgeInfo().bg};color:${getLiveStatusBadgeInfo().color};font-weight:700;">
            ${getLiveStatusBadgeInfo().badge || getLiveStatusBadgeInfo().text}
          </span>
          <span id="dashLiveSubtext" style="font-size:11px;color:#92400E;font-style:italic;${getLiveStatusBadgeInfo().subtext ? '' : 'display:none;'}">
            ${getLiveStatusBadgeInfo().subtext || ''}
          </span>
          <span id="dashHotspotsCount" style="font-size:11px;padding:2px 8px;border-radius:12px;background:#EFF6FF;color:#1D4ED8;font-weight:700;">
            Hotspots: ${currentEvents.length}
          </span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;font-size:12px;color:#7A8699;">
          <div>
            LAST UPDATED: <span id="dashLastUpdated" style="font-weight:700;color:#0B2545;font-family:monospace;">${state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : (state.lastSuccessfulFetch ? state.lastSuccessfulFetch.toLocaleTimeString() : (state.dataSource === 'demo' ? 'DEMO DATASET' : 'CONNECTING...'))}</span>
          </div>
          <button id="btnManualRefresh" class="btn btn-sm btn-outline" style="padding:3px 10px;font-size:11px;font-weight:700;height:26px;display:inline-flex;align-items:center;gap:4px;" onclick="window.__thermosafe.manualRefreshFirms()">
            ↻ Refresh
          </button>
        </div>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card info">
          <div class="kpi-label">Active Thermal Anomalies</div>
          <div class="kpi-value" id="kpi-val-total">${totalEvents}</div>
          <div class="kpi-sub" id="kpi-sub-total">${state.dataSource === 'live' ? 'Live telemetry synchronized' : 'Simulated observations'}</div>
        </div>
        <div class="kpi-card critical">
          <div class="kpi-label">Critical Industrial Fires</div>
          <div class="kpi-value" id="kpi-val-critical">${critEvents}</div>
          <div class="kpi-sub" id="kpi-sub-critical">Immediate response required</div>
        </div>
        <div class="kpi-card high">
          <div class="kpi-label">High-Risk Events</div>
          <div class="kpi-value" id="kpi-val-high">${highEvents}</div>
          <div class="kpi-sub" id="kpi-sub-high">Active industrial hotspots</div>
        </div>
        <div class="kpi-card medium">
          <div class="kpi-label">Gas Flares & Moderate</div>
          <div class="kpi-value" id="kpi-val-moderate">${modEvents}</div>
          <div class="kpi-sub" id="kpi-sub-moderate">Continuous monitoring</div>
        </div>
        <div class="kpi-card persistent">
          <div class="kpi-label">Monitored Facilities</div>
          <div class="kpi-value" id="kpi-val-facilities">${facCount}</div>
          <div class="kpi-sub" id="kpi-sub-facilities">Industrial perimeter registry</div>
        </div>
        <div class="kpi-card low">
          <div class="kpi-label">Normal / Low Activity</div>
          <div class="kpi-value" id="kpi-val-low">${lowEvents}</div>
          <div class="kpi-sub" id="kpi-sub-low">Baseline thermal levels</div>
        </div>
      </div>

      <div class="dashboard-grid" style="height:calc(100vh - 260px);min-height:520px;">
        <div class="map-container">
          <div id="map"></div>
          <div class="legend">
            <div class="legend-title">Thermal Event Legend</div>
            <div class="legend-item"><div class="legend-dot" style="background:#DC2626;"></div>Critical Industrial Fire</div>
            <div class="legend-item"><div class="legend-dot" style="background:#EA580C;"></div>High-Risk Thermal Event</div>
            <div class="legend-item"><div class="legend-dot" style="background:#CA8A04;"></div>Gas Flare / Moderate</div>
            <div class="legend-item"><div class="legend-dot" style="background:#7C3AED;"></div>Persistent Thermal Source</div>
            <div class="legend-item"><div class="legend-square" style="background:#2563EB;"></div>Industrial Facility</div>
            <div class="legend-item"><div class="legend-dot" style="background:#16A34A;"></div>Low-Risk / Normal</div>
          </div>
        </div>

        <div class="right-panel">
          <div class="card">
            <div class="card-title">
              <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><path d="M12 6v6l4 2"/></svg>
              AI Thermal Classification
            </div>
            <div id="ai-panel-content">
              <div style="text-align:center;padding:24px 0;color:#7A8699;font-size:13px;line-height:1.6;">
                <div style="font-size:36px;margin-bottom:10px;opacity:0.5;">🛰️</div>
                Select a thermal marker on the map<br>to view AI classification.
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-title">
              <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
              Live Event Feed
            </div>
            <div id="live-feed">
              ${LIVE_FEED.slice(0, 6).map(f => `
                <div class="feed-item">
                  <span class="feed-time">${f.time}</span>
                  <span class="feed-text">${escapeHtml(f.text)}</span>
                </div>
              `).join('')}
            </div>
          </div>

          <div class="card">
            <div class="card-title">
              <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              SIMULATION & CONTROLS
            </div>
            <div style="font-size:11px;color:#7A8699;margin-bottom:12px;line-height:1.5;">
              Trigger simulated incident alerts for demonstration
            </div>
            <div class="btn-grid">
              <button class="btn btn-danger btn-sm" onclick="window.__thermosafe.simulate('Industrial Fire')">🔴 Critical Fire</button>
              <button class="btn btn-warning btn-sm" onclick="window.__thermosafe.simulate('High-Risk Thermal')">🟠 High-Risk</button>
            </div>
            <div class="btn-grid" style="margin-top:8px;">
              <button class="btn btn-warning btn-sm" style="background:#CA8A04;" onclick="window.__thermosafe.simulate('Gas Flare')">🟡 Gas Flare</button>
              <button class="btn btn-purple btn-sm" onclick="window.__thermosafe.simulate('Persistent Thermal Source')">🟣 Persistent</button>
            </div>
            <button class="btn btn-outline btn-block btn-sm" style="margin-top:8px;" onclick="window.__thermosafe.requestNotifPermission()">
              🔔 Enable Browser Notifications
            </button>
            <button class="btn btn-primary btn-block btn-sm" style="margin-top:8px;" onclick="window.__thermosafe.simulateCritical()">
              ⚡ SIMULATE CRITICAL ALERT
            </button>
          </div>
        </div>
      </div>
    `;

    setTimeout(initMap, 50);
    updateDebugDiagnostics();
  }

  function updateDashboardLiveView() {
    const totalEvents = currentEvents.length;
    const critEvents = currentEvents.filter(e => (e.risk || e.risk_priority) === 'CRITICAL').length;
    const highEvents = currentEvents.filter(e => (e.risk || e.risk_priority) === 'HIGH').length;
    const modEvents = currentEvents.filter(e => (e.risk || e.risk_priority) === 'MEDIUM' || (e.classification || '').includes('Gas') || (e.classification || '') === 'GAS_FLARE').length;
    const lowEvents = currentEvents.filter(e => (e.risk || e.risk_priority) === 'LOW').length;
    const facCount = currentFacilities.length;

    const elSourceLabel = document.getElementById('dashSourceLabel');
    if (elSourceLabel) {
      elSourceLabel.textContent = getSourceLabelText();
      elSourceLabel.style.color = getSourceLabelColor();
    }
    const elLiveStatus = document.getElementById('dashLiveStatus');
    const elLiveSubtext = document.getElementById('dashLiveSubtext');
    if (elLiveStatus) {
      const badge = getLiveStatusBadgeInfo();
      elLiveStatus.textContent = badge.badge || badge.text;
      elLiveStatus.style.background = badge.bg;
      elLiveStatus.style.color = badge.color;
      if (elLiveSubtext) {
        elLiveSubtext.textContent = badge.subtext || '';
        elLiveSubtext.style.display = badge.subtext ? 'inline' : 'none';
      }
    }
    const elHotspots = document.getElementById('dashHotspotsCount');
    if (elHotspots) {
      elHotspots.textContent = `Hotspots: ${totalEvents}`;
    }
    const elLastUpdated = document.getElementById('dashLastUpdated');
    if (elLastUpdated) {
      if (state.lastSuccessfulFirmsFetch) {
        elLastUpdated.textContent = state.lastSuccessfulFirmsFetch.toLocaleTimeString();
      } else if (state.lastSuccessfulFetch) {
        elLastUpdated.textContent = state.lastSuccessfulFetch.toLocaleTimeString();
      } else if (state.dataSource === 'demo') {
        elLastUpdated.textContent = 'DEMO DATASET';
      } else if (state.dataState === 'CONNECTING') {
        elLastUpdated.textContent = 'CONNECTING...';
      } else {
        elLastUpdated.textContent = new Date().toLocaleTimeString();
      }
    }

    if (state.dataState === 'CONNECTING') {
      const elValTotal = document.getElementById('kpi-val-total');
      if (elValTotal) elValTotal.innerHTML = '<span style="font-size:20px;color:#D97706;animation:pulse 1.5s infinite;">CONNECTING...</span>';
      const elSubTotal = document.getElementById('kpi-sub-total');
      if (elSubTotal) elSubTotal.textContent = 'Connecting to NASA FIRMS...';

      const elValCrit = document.getElementById('kpi-val-critical');
      if (elValCrit) elValCrit.textContent = '--';
      const elValHigh = document.getElementById('kpi-val-high');
      if (elValHigh) elValHigh.textContent = '--';
      const elValMod = document.getElementById('kpi-val-moderate');
      if (elValMod) elValMod.textContent = '--';
      const elValFac = document.getElementById('kpi-val-facilities');
      if (elValFac) elValFac.textContent = facCount;
      const elValLow = document.getElementById('kpi-val-low');
      if (elValLow) elValLow.textContent = '--';
    } else {
      const elValTotal = document.getElementById('kpi-val-total');
      if (elValTotal) elValTotal.textContent = totalEvents;
      const elSubTotal = document.getElementById('kpi-sub-total');
      if (elSubTotal) elSubTotal.textContent = state.dataSource === 'live' ? 'Live telemetry synchronized' : 'Simulated observations';

      const elValCrit = document.getElementById('kpi-val-critical');
      if (elValCrit) elValCrit.textContent = critEvents;

      const elValHigh = document.getElementById('kpi-val-high');
      if (elValHigh) elValHigh.textContent = highEvents;

      const elValMod = document.getElementById('kpi-val-moderate');
      if (elValMod) elValMod.textContent = modEvents;

      const elValFac = document.getElementById('kpi-val-facilities');
      if (elValFac) elValFac.textContent = facCount;

      const elValLow = document.getElementById('kpi-val-low');
      if (elValLow) elValLow.textContent = lowEvents;
    }

    const liveFeedEl = document.getElementById('live-feed');
    if (liveFeedEl && LIVE_FEED && LIVE_FEED.length > 0) {
      liveFeedEl.innerHTML = LIVE_FEED.slice(0, 6).map(f => `
        <div class="feed-item">
          <span class="feed-time">${f.time}</span>
          <span class="feed-text">${escapeHtml(f.text)}</span>
        </div>
      `).join('');
    }

    if (state.map && state.thermalLayer) {
      renderMarkers();
      if (state.showFacilities) renderFacilities();
    }

    updateDebugDiagnostics();
  }

  function updateDebugDiagnostics() {
    let panel = document.getElementById('devDiagnosticPanel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'devDiagnosticPanel';
      document.body.appendChild(panel);
    }
    const lastFetchStr = state.lastSuccessfulFetch ? state.lastSuccessfulFetch.toLocaleTimeString() : 'None';
    
    // Truthful status indicator (Step 8)
    let statusText = 'OK';
    if (state.dataSource === 'live') {
      if (state.lastApiError) {
        statusText = `Err: ${state.lastApiError}`;
      } else if (state.firmsState === 'CONFIGURATION_REQUIRED') {
        statusText = 'FIRMS UNCONFIGURED';
      } else if (state.firmsState === 'LIVE_UNAVAILABLE') {
        statusText = 'NASA FIRMS UNAVAILABLE';
      } else if (state.firmsState === 'LIVE_INGESTING') {
        statusText = 'LIVE INGESTING';
      } else if (state.firmsState === 'LIVE_INGESTION_ERROR') {
        statusText = 'LIVE INGESTION ERROR';
      } else if (state.firmsState === 'LIVE_CONNECTED') {
        const evCount = currentEvents.length;
        statusText = evCount > 0 ? 'LIVE CONNECTED' : 'LIVE CONNECTED — 0 EVENTS';
      } else if (state.firmsState === 'LIVE_STALE') {
        statusText = 'LIVE STALE';
      } else {
        statusText = state.isLiveBackend ? (currentEvents.length > 0 ? 'LIVE CONNECTED' : 'LIVE CONNECTED — 0 EVENTS') : 'BACKEND OFFLINE';
      }
    } else {
      statusText = state.lastApiError ? `Err: ${state.lastApiError}` : 'DEMO MODE';
    }

    panel.innerHTML = `
      <span class="diag-item"><span class="diag-label">Auth:</span> <span class="diag-val">${escapeHtml(state.authStatus)}</span></span>
      <span class="diag-item"><span class="diag-label">Source:</span> <span class="diag-val" style="color:${state.dataSource === 'live' ? '#22C55E' : '#EAB308'};">${state.dataSource.toUpperCase()}</span></span>
      <span class="diag-item"><span class="diag-label">Mounts:</span> <span class="diag-val">${state.dashboardMountCount}</span></span>
      <span class="diag-item"><span class="diag-label">Last Fetch:</span> <span class="diag-val">${lastFetchStr}</span></span>
      <span class="diag-item"><span class="diag-label">Status:</span> <span class="diag-val">${escapeHtml(statusText)}</span></span>
    `;
  }

  function renderMapPage() {
    const content = document.getElementById('content');
    if (!content) return;

    const critCount = currentEvents.filter(e => e.risk === 'CRITICAL').length;
    const highCount = currentEvents.filter(e => e.risk === 'HIGH').length;
    const gasCount = currentEvents.filter(e => e.risk === 'MEDIUM' || e.classification.includes('Gas')).length;
    const persistCount = currentEvents.filter(e => e.classification.includes('Persistent')).length;
    const lowCount = currentEvents.filter(e => e.risk === 'LOW').length;

    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-size:20px;font-weight:800;color:#0B2545;">Live Thermal Map</div>
          <div style="font-size:12px;color:#4A5568;margin-top:2px;">India Corridor · ${currentEvents.length} thermal anomalies · ${currentFacilities.length} facilities</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <div class="datasource-control" style="display:inline-flex;align-items:center;background:#F0F6FC;border:1px solid #D6E2EF;border-radius:20px;padding:2px;gap:2px;">
            <button type="button" class="source-toggle-btn ${state.dataSource === 'live' ? 'active-live' : ''}" id="btnMapSourceLive" onclick="window.__thermosafe.setDataSource('live')">● LIVE DATA</button>
            <button type="button" class="source-toggle-btn ${state.dataSource === 'demo' ? 'active-demo' : ''}" id="btnMapSourceDemo" onclick="window.__thermosafe.setDataSource('demo')">● DEMO DATA</button>
          </div>
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.toggleHeatmap()">
            ${state.showHeatmap ? '✓ Heatmap On' : 'Heatmap'}
          </button>
        </div>
      </div>

      <div class="kpi-grid" style="margin-bottom:14px;">
        <div class="kpi-card critical"><div class="kpi-label">Critical</div><div class="kpi-value">${critCount}</div></div>
        <div class="kpi-card high"><div class="kpi-label">High</div><div class="kpi-value">${highCount}</div></div>
        <div class="kpi-card medium"><div class="kpi-label">Gas Flare</div><div class="kpi-value">${gasCount}</div></div>
        <div class="kpi-card persistent"><div class="kpi-label">Persistent</div><div class="kpi-value">${persistCount}</div></div>
        <div class="kpi-card low"><div class="kpi-label">Low / Normal</div><div class="kpi-value">${lowCount}</div></div>
      </div>

      <div class="map-container" style="height:calc(100vh - 340px);min-height:480px;">
        <div id="map"></div>
        <div class="legend">
          <div class="legend-title">Thermal Event Legend</div>
          <div class="legend-item"><div class="legend-dot" style="background:#DC2626;"></div>Critical Industrial Fire</div>
          <div class="legend-item"><div class="legend-dot" style="background:#EA580C;"></div>High-Risk Thermal Event</div>
          <div class="legend-item"><div class="legend-dot" style="background:#CA8A04;"></div>Gas Flare / Moderate</div>
          <div class="legend-item"><div class="legend-dot" style="background:#7C3AED;"></div>Persistent Thermal Source</div>
          <div class="legend-item"><div class="legend-square" style="background:#2563EB;"></div>Industrial Facility</div>
          <div class="legend-item"><div class="legend-dot" style="background:#16A34A;"></div>Low-Risk / Normal</div>
        </div>
      </div>
    `;
    setTimeout(() => { initMap(); if (state.showHeatmap) toggleHeatmap(); }, 50);
  }

  function renderIncidentsPage() {
    const content = document.getElementById('content');
    if (!content) return;
    const sorted = [...currentEvents].sort((a, b) => b.score - a.score);
    content.innerHTML = `
      <div style="font-size:20px;font-weight:800;margin-bottom:4px;color:#0B2545;">Incidents Registry</div>
      <div style="font-size:12px;color:#4A5568;margin-bottom:16px;">Detected thermal anomalies ranked by evaluated risk score</div>

      <div style="background:#FFFFFF;border:1px solid #D6E2EF;border-radius:10px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#E8F1FB;color:#0B2545;">
              <th style="text-align:left;padding:12px;font-weight:800;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;border-bottom:2px solid #1E5AA8;">Event ID</th>
              <th style="text-align:left;padding:12px;font-weight:800;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;border-bottom:2px solid #1E5AA8;">Classification</th>
              <th style="text-align:left;padding:12px;font-weight:800;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;border-bottom:2px solid #1E5AA8;">Location</th>
              <th style="text-align:center;padding:12px;font-weight:800;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;border-bottom:2px solid #1E5AA8;">Risk</th>
              <th style="text-align:right;padding:12px;font-weight:800;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;border-bottom:2px solid #1E5AA8;">Score</th>
              <th style="text-align:right;padding:12px;font-weight:800;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;border-bottom:2px solid #1E5AA8;">Confidence</th>
            </tr>
          </thead>
          <tbody>
            ${sorted.length > 0 ? sorted.map(ev => `
              <tr style="border-bottom:1px solid #D6E2EF;cursor:pointer;transition:background 0.15s;" onmouseover="this.style.background='#F5F8FC'" onmouseout="this.style.background='#FFFFFF'" onclick="window.__thermosafe.selectEvent('${ev.id}')">
                <td style="padding:10px 12px;font-family:'Courier New',monospace;font-weight:700;color:#0B2545;">${ev.id}</td>
                <td style="padding:10px 12px;">${classBadge(ev.classification)}</td>
                <td style="padding:10px 12px;color:#4A5568;">${escapeHtml(ev.city || '')}${ev.state ? ', ' + escapeHtml(ev.state) : ''}</td>
                <td style="padding:10px 12px;text-align:center;">${riskBadge(ev.risk)}</td>
                <td style="padding:10px 12px;text-align:right;font-weight:800;color:#0B2545;">${ev.score}</td>
                <td style="padding:10px 12px;text-align:right;font-weight:600;color:#1E5AA8;">${ev.confidence}%</td>
              </tr>
            `).join('') : `
              <tr>
                <td colspan="6" style="padding:36px 16px;text-align:center;color:#7A8699;">
                  <div style="font-weight:700;font-size:14px;color:#0B2545;margin-bottom:6px;">No Live Thermal Incidents Detected</div>
                  <div style="font-size:12px;color:#4A5568;line-height:1.5;">
                    ${state.dataSource === 'live' 
                      ? (state.firmsState === 'LIVE_CONNECTED' 
                          ? 'NASA FIRMS live connection verified. Zero active thermal hotspots returned in current pass.' 
                          : (state.firmsState === 'CONFIGURATION_REQUIRED'
                              ? 'NASA FIRMS MAP KEY is not configured in backend/.env. Configure FIRMS_MAP_KEY to ingest real-time VIIRS telemetry.'
                              : state.liveStatusMessage || 'Awaiting live satellite telemetry feed.'))
                      : 'No demonstration incidents recorded.'}
                  </div>
                </td>
              </tr>
            `}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderAnalyticsPage() {
    const content = document.getElementById('content');
    if (!content) return;

    let classEntries = [];
    let riskCounts = { CRITICAL:0, HIGH:0, MEDIUM:0, LOW:0 };
    let timeSeriesPoints = [];

    if (state.backendAnalytics) {
      if (state.backendAnalytics.event_types?.items) {
        classEntries = state.backendAnalytics.event_types.items.map(i => [i.event_type, i.count]);
      }
      if (state.backendAnalytics.risk_distribution?.items) {
        state.backendAnalytics.risk_distribution.items.forEach(i => {
          const k = i.risk_priority.toUpperCase();
          if (riskCounts[k] !== undefined) riskCounts[k] = i.count;
          else if (k.includes('MOD') || k.includes('MED')) riskCounts.MEDIUM = i.count;
        });
      }
      if (state.backendAnalytics.time_series?.data_points) {
        timeSeriesPoints = state.backendAnalytics.time_series.data_points;
      }
    }

    const totalCount = currentEvents.length;
    if (!classEntries.length) {
      if (totalCount > 0) {
        const classCounts = {};
        currentEvents.forEach(e => { classCounts[e.classification] = (classCounts[e.classification] || 0) + 1; });
        classEntries = Object.entries(classCounts).sort((a, b) => b[1] - a[1]);
        currentEvents.forEach(e => {
          const r = e.risk in riskCounts ? e.risk : 'LOW';
          riskCounts[r] = (riskCounts[r] || 0) + 1;
        });
      }
    }

    const maxClass = Math.max(...classEntries.map(e => e[1]), 1);

    content.innerHTML = `
      <div style="font-size:20px;font-weight:800;margin-bottom:4px;color:#0B2545;">Analytics & Intelligence</div>
      <div style="font-size:12px;color:#4A5568;margin-bottom:16px;">
        ${state.dataSource === 'live' ? 'Real-time database aggregated thermal intelligence KPIs' : 'Local demonstration telemetry'}
      </div>

      <div class="kpi-grid" style="margin-bottom:16px;">
        <div class="kpi-card info"><div class="kpi-label">Total Events</div><div class="kpi-value">${totalCount}</div></div>
        <div class="kpi-card critical"><div class="kpi-label">Critical</div><div class="kpi-value">${riskCounts.CRITICAL || 0}</div></div>
        <div class="kpi-card high"><div class="kpi-label">High</div><div class="kpi-value">${riskCounts.HIGH || 0}</div></div>
        <div class="kpi-card medium"><div class="kpi-label">Medium / Gas</div><div class="kpi-value">${riskCounts.MEDIUM || 0}</div></div>
        <div class="kpi-card low"><div class="kpi-label">Low / Normal</div><div class="kpi-value">${riskCounts.LOW || 0}</div></div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;">
        <div class="card">
          <div class="card-title">Event Classification Breakdown</div>
          <div class="chart-container">
            ${classEntries.length > 0 ? classEntries.map(([name, count]) => {
              const c = EVENT_COLORS[name] || EVENT_COLORS['Unknown'];
              return `
                <div class="bar-row">
                  <div class="bar-label">${name.length > 16 ? name.slice(0,14) + '…' : name}</div>
                  <div class="bar-track">
                    <div class="bar-fill" style="width:${(count/maxClass)*100}%;background:${c.hex};">${count}</div>
                  </div>
                </div>
              `;
            }).join('') : `
              <div style="padding:24px;text-align:center;color:#7A8699;font-size:12px;">No active classified thermal events</div>
            `}
          </div>
        </div>

        <div class="card">
          <div class="card-title">Risk Priority Distribution</div>
          <div class="chart-container">
            ${Object.entries(riskCounts).map(([level, count]) => {
              const pct = totalCount > 0 ? (count / totalCount) * 100 : 0;
              return `
                <div class="bar-row">
                  <div class="bar-label">${level}</div>
                  <div class="bar-track">
                    <div class="bar-fill" style="width:${Math.max(pct, 5)}%;background:${getRiskColor(level)};">${count}</div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>

      <div class="card" style="margin-top:16px;">
        <div class="card-title">Thermal Events Over Time (${state.dataSource === 'live' ? 'Database Chronology' : 'Last 24h Trend'})</div>
        <div style="display:flex;align-items:flex-end;gap:8px;height:140px;padding-top:12px;">
          ${(timeSeriesPoints.length ? timeSeriesPoints : (totalCount === 0 ? [
            { label:'00h', count:0 }, { label:'04h', count:0 }, { label:'08h', count:0 }, { label:'12h', count:0 }, { label:'16h', count:0 }, { label:'20h', count:0 }
          ] : [
            { label:'00h', count:2 }, { label:'04h', count:5 }, { label:'08h', count:9 }, { label:'12h', count:14 }, { label:'16h', count:8 }, { label:'20h', count:4 }
          ])).map((p) => {
            const h = Math.min(100, Math.max(15, (p.count || p.total_events || 1) * 12));
            const lbl = p.timestamp ? new Date(p.timestamp).toLocaleTimeString([], {hour:'2-digit'}) : (p.label || 'T');
            const cnt = p.total_events !== undefined ? p.total_events : (p.count || 0);
            return `
              <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;">
                <div style="width:100%;height:${h}px;background:linear-gradient(180deg,#DC2626,#1E5AA8);border-radius:4px 4px 0 0;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:700;">
                  ${cnt}
                </div>
                <div style="font-size:10px;color:#7A8699;font-weight:600;">${lbl}</div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  function renderAlertsPage() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-size:20px;font-weight:800;color:#0B2545;">Alerts & Notifications</div>
          <div style="font-size:12px;color:#4A5568;margin-top:2px;">
            ${state.notifications.length} notifications · ${state.dataSource === 'live' ? 'Database Synchronized' : 'Demo Data'}
          </div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.openDrawer()">Open Notification Drawer</button>
      </div>

      <div style="display:flex;flex-direction:column;gap:12px;">
        ${state.notifications.map(a => {
          const ev = getEventById(a.eventId);
          const color = ev ? getEventColor(ev).hex : getRiskColor(a.level.toUpperCase());
          return `
            <div class="card" style="padding:16px;border-left:5px solid ${color};">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                <div style="flex:1;min-width:220px;">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;">
                    <span class="risk-badge ${a.level === 'critical' ? 'risk-critical' : a.level === 'high' ? 'risk-high' : 'risk-low'}">${a.level.toUpperCase()}</span>
                    <span style="font-size:11px;color:#7A8699;font-family:'Courier New',monospace;font-weight:600;">${a.time}</span>
                    <span style="font-size:11px;color:#7A8699;">${timeAgo(a.ts)}</span>
                  </div>
                  <div style="font-weight:800;font-size:15px;color:#0B2545;margin-bottom:6px;">${escapeHtml(a.title)}</div>
                  <div style="font-size:13px;color:#4A5568;line-height:1.6;">${escapeHtml(a.msg)}</div>
                  <div style="font-size:11px;color:#7A8699;margin-top:6px;">Event Reference: <span style="font-family:'Courier New',monospace;">${escapeHtml(a.eventId)}</span></div>
                  ${a.isAcknowledged ? `
                    <div style="font-size:11px;color:#16A34A;margin-top:4px;font-weight:700;display:flex;align-items:center;gap:4px;">
                      <span>✓</span> Acknowledged by ${escapeHtml(a.acknowledgedBy || 'Operator')} ${a.acknowledgedAt ? '· ' + new Date(a.acknowledgedAt).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : ''}
                    </div>
                  ` : ''}
                </div>
                <div style="display:flex;flex-direction:column;gap:6px;min-width:160px;">
                  <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.viewAlertOnMap('${a.id}')">View on Map</button>
                  ${a.isAcknowledged ? `
                    <button class="btn btn-outline btn-sm" style="color:#16A34A;border-color:#86EFAC;background:#F0FDF4;font-weight:700;" onclick="window.__thermosafe.showAckDetails('${a.id}')">
                      ✓ Acknowledged
                    </button>
                  ` : `
                    <button class="btn btn-success btn-sm" onclick="window.__thermosafe.acknowledge('${a.id}')">Acknowledge</button>
                  `}
                  <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.navigateTo('reports')">Generate Report</button>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderReportsPage() {
    const content = document.getElementById('content');
    if (!content) return;
    const ev = state.selectedEvent || currentEvents[0];
    const color = getEventColor(ev);

    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-size:20px;font-weight:800;color:#0B2545;">Incident & Compliance Report</div>
          <div style="font-size:12px;color:#4A5568;margin-top:2px;">
            ${state.isLiveBackend ? 'Connected to Backend Reporting Engine' : 'Local Demonstration Mode'}
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.previewReport()">Preview Report</button>
          <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.downloadReport()">Download CSV / Report</button>
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.shareReport()">Share</button>
        </div>
      </div>

      <div class="card" style="border-top:4px solid ${color.hex};">
        <div style="font-weight:800;font-size:18px;margin-bottom:16px;color:#0B2545;padding-bottom:10px;border-bottom:2px solid #D6E2EF;display:flex;justify-content:space-between;align-items:center;">
          <span>THERMOSAFE AI — Incident Intelligence Report</span>
          <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.generateBackendReport()">⚡ Save Report to Database</button>
        </div>
        <div class="detail-row"><span class="detail-label">Event ID</span><span class="detail-value font-mono">${ev.id}</span></div>
        <div class="detail-row"><span class="detail-label">Location</span><span class="detail-value">${escapeHtml(ev.city)}, ${escapeHtml(ev.state)}</span></div>
        <div class="detail-row"><span class="detail-label">Coordinates</span><span class="detail-value font-mono">${ev.lat.toFixed(4)}° N, ${ev.lng.toFixed(4)}° E</span></div>
        <div class="detail-row"><span class="detail-label">Classification</span><span class="detail-value">${classBadge(ev.classification)}</span></div>
        <div class="detail-row"><span class="detail-label">Risk Priority</span><span class="detail-value">${riskBadge(ev.risk)}</span></div>
        <div class="detail-row"><span class="detail-label">Risk Score</span><span class="detail-value">${ev.score}/100</span></div>
        <div class="detail-row"><span class="detail-label">AI Confidence</span><span class="detail-value">${ev.confidence}%</span></div>
        <div class="detail-row"><span class="detail-label">Thermal Intensity</span><span class="detail-value">${ev.intensity}</span></div>
        <div class="detail-row"><span class="detail-label">Persistence</span><span class="detail-value">${ev.persistence}</span></div>
        <div class="detail-row"><span class="detail-label">Nearby Facility</span><span class="detail-value">${escapeHtml(ev.facility || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">Satellite Source</span><span class="detail-value">${ev.source}</span></div>
        <div class="detail-row"><span class="detail-label">Detected Time</span><span class="detail-value font-mono">${ev.detected}</span></div>
      </div>

      <div class="card" style="margin-top:16px;">
        <div class="card-title">AI Analysis Context & Explanation</div>
        <div style="font-size:13px;color:#4A5568;line-height:1.7;">
          ${escapeHtml(ev.explanation)}
        </div>
      </div>

      <div class="card" style="margin-top:16px;border-left:4px solid ${color.hex};">
        <div class="card-title">Operational Protocol Recommendation</div>
        <div style="font-size:13px;color:#4A5568;line-height:1.7;">
          ${ev.risk === 'CRITICAL' ? '⚠ Immediate dispatch to facility safety response unit and district emergency management. Ground thermal verification team within 30 minutes. Secure combustible perimeter.' : ev.risk === 'HIGH' ? '⚠ Notify industrial safety officer and refinery operations control. Schedule ground inspection within 2 hours.' : '● Maintain routine automated satellite pass monitoring. Log incident for long-term historical recurrence modeling.'}
        </div>
      </div>

      ${state.backendReports && state.backendReports.length > 0 ? `
        <div class="card" style="margin-top:16px;">
          <div class="card-title">Previously Generated Database Reports</div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${state.backendReports.map(r => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--bg-section);border-radius:6px;border:1px solid var(--border);">
                <div>
                  <div style="font-weight:700;font-size:13px;color:var(--navy);">${escapeHtml(r.title)}</div>
                  <div style="font-size:11px;color:var(--text-muted);">Generated: ${new Date(r.generated_at).toLocaleString()} · Type: ${r.report_type}</div>
                </div>
                <a href="${API_BASE_URL}/api/reports/${r.id}/export?format=csv" target="_blank" class="btn btn-outline btn-sm">Download CSV</a>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}
    `;
  }

  function renderSettingsPage() {
    const content = document.getElementById('content');
    if (!content) return;

    const deviceId = localStorage.getItem('thermo_device_id') || 'Not registered';
    const notifPerm = ('Notification' in window) ? Notification.permission : 'Not supported';
    const fcmStatus = state.fcmStatus ? state.fcmStatus.status : 'CONFIGURATION_REQUIRED';
    const fcmMode = state.fcmStatus ? state.fcmStatus.mode : 'simulated';

    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-size:20px;font-weight:800;color:#0B2545;">System Settings & Operator Administration</div>
          <div style="font-size:12px;color:#4A5568;margin-top:2px;">Operator team mobilization, device push registration, and backend status</div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.openTeamModal()">+ Register Operator Team</button>
      </div>

      <!-- Current Session -->
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">Operator Profile & Local Session</div>
        <div class="detail-row"><span class="detail-label">Operator Name</span><span class="detail-value font-bold">${escapeHtml(state.currentUser ? (state.currentUser.full_name || state.currentUser.name) : 'ThermoSafe Operator')}</span></div>
        <div class="detail-row"><span class="detail-label">Email</span><span class="detail-value">${escapeHtml(state.currentUser ? state.currentUser.email : 'local@thermosafe.ai')}</span></div>
        <div class="detail-row"><span class="detail-label">Role</span><span class="detail-value"><span class="risk-badge risk-facility">${escapeHtml((state.currentUser ? (state.currentUser.role || 'Analyst') : 'Analyst').toUpperCase())}</span></span></div>
        <div class="detail-row"><span class="detail-label">Operator Team</span><span class="detail-value">${escapeHtml(state.currentUser && state.currentUser.operator_team_name ? state.currentUser.operator_team_name : 'Operations Watch Desk')}</span></div>
        <div class="detail-row"><span class="detail-label">Session Status</span><span class="detail-value" style="color:#16A34A;font-weight:700;">● Active Local Operator Session</span></div>
        <div style="margin-top:12px;display:flex;gap:8px;">
          <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.openEditProfileModal()">Edit Profile</button>
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.logout()">Reset Session</button>
        </div>
      </div>

      <!-- Operator Teams Management (Phase 30) -->
      <div class="card" style="margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
          <div class="card-title" style="margin:0;">🚒 Emergency Operator Teams & Hazmat Units</div>
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.openTeamModal()">+ New Team</button>
        </div>
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
          Units dispatched automatically during High and Critical thermal incidents within their response radius.
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${state.operatorTeams && state.operatorTeams.length > 0 ? state.operatorTeams.map(t => {
            const teamName = t.team_name || t.name;
            const orgName = t.organization_name || 'Industrial Emergency Response';
            const facName = t.facility_name || (t.facility_id ? `Facility #${t.facility_id}` : 'General Industrial Zone');
            const isActive = t.is_active !== false;
            const notifOn = t.notification_enabled !== false;
            const radius = t.response_radius_km || 50;
            const phone = t.phone || t.contact_phone || 'Emergency Dispatch';
            const email = t.email || '—';
            const contact = t.contact_person || 'Unit Commander';
            const indType = t.industry_type || t.team_type || 'Industrial Hazmat';
            const userCount = t.assigned_users ? t.assigned_users.length : (t.assigned_user_ids ? t.assigned_user_ids.length : 0);

            return `
              <div style="background:var(--bg-section);border:1px solid var(--border);border-radius:8px;padding:14px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
                  <div>
                    <div style="font-weight:800;font-size:15px;color:var(--navy);display:flex;align-items:center;gap:6px;">
                      <span>${escapeHtml(teamName)}</span>
                      <span class="risk-badge ${isActive ? 'risk-low' : 'risk-critical'}" style="font-size:10px;">
                        ${isActive ? 'Active' : 'Inactive'}
                      </span>
                      <span class="risk-badge ${notifOn ? 'risk-gas' : 'risk-low'}" style="font-size:10px;">
                        ${notifOn ? '🔔 Alerts ON' : '🔕 Alerts OFF'}
                      </span>
                    </div>
                    <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
                      <b>${escapeHtml(orgName)}</b> · Facility: ${escapeHtml(facName)} · Type: ${escapeHtml(indType)}
                    </div>
                  </div>
                  <div style="display:flex;gap:6px;">
                    <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.openTeamModal(${t.id})">Edit</button>
                    <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.toggleTeamActive(${t.id})">
                      ${isActive ? 'Deactivate' : 'Activate'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="window.__thermosafe.deleteTeam(${t.id})">Delete</button>
                  </div>
                </div>

                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:6px;font-size:11px;color:var(--text-muted);background:#fff;padding:8px 10px;border-radius:6px;border:1px solid var(--border);">
                  <div>Contact: <b style="color:var(--navy);">${escapeHtml(contact)}</b></div>
                  <div>Phone: <b style="color:var(--navy);">${escapeHtml(phone)}</b></div>
                  <div>Email: <span>${escapeHtml(email)}</span></div>
                  <div>Radius: <b>${radius} km</b></div>
                  <div>Coordinates: <span style="font-family:monospace;">${Number(t.latitude).toFixed(3)}°N, ${Number(t.longitude).toFixed(3)}°E</span></div>
                  <div>Assigned Personnel: <b>${userCount} operator(s)</b></div>
                </div>
              </div>
            `;
          }).join('') : `
            <div style="text-align:center;padding:24px;color:var(--text-muted);font-size:13px;background:var(--bg-section);border-radius:8px;">
              No operator teams currently registered. Click <b>+ New Team</b> to add an emergency response team.
            </div>
          `}
        </div>
      </div>

      <!-- Browser & Device Push Registration (Phase 31 & 32) -->
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">📱 Browser & Device Push Notifications (FCM)</div>
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
          Hardware device fingerprinting and real-time push alerting via Firebase Cloud Messaging.
        </div>
        <div class="detail-row"><span class="detail-label">Client Device Identifier</span><span class="detail-value font-mono" style="font-size:11px;">${escapeHtml(deviceId)}</span></div>
        <div class="detail-row"><span class="detail-label">Browser Platform</span><span class="detail-value">${escapeHtml(navigator.platform || 'Web')} (${escapeHtml(navigator.userAgent.includes('Chrome') ? 'Chrome' : 'Standard Web')})</span></div>
        <div class="detail-row"><span class="detail-label">Notification Permission</span><span class="detail-value"><span class="risk-badge ${notifPerm === 'granted' ? 'risk-low' : (notifPerm === 'denied' ? 'risk-critical' : 'risk-gas')}">${notifPerm.toUpperCase()}</span></span></div>
        <div class="detail-row"><span class="detail-label">FCM Integration Status</span><span class="detail-value"><span class="risk-badge ${fcmStatus === 'PASS' ? 'risk-low' : 'risk-gas'}">${fcmStatus} (${fcmMode.toUpperCase()})</span></span></div>
        <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn btn-primary btn-sm" onclick="window.__thermosafe.requestNotifPermission()">
            🔔 Enable / Update Browser Notifications
          </button>
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.sendTestPushNotification()">
            ⚡ Send Test Emergency Push Alert
          </button>
        </div>
      </div>

      <!-- Live Backend Services -->
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">Live Backend Services</div>
        <div class="detail-row"><span class="detail-label">API Gateway</span><span class="detail-value font-mono">${API_BASE_URL}</span></div>
        <div class="detail-row"><span class="detail-label">Backend Status</span><span class="detail-value" style="color:${state.isLiveBackend ? '#16A34A' : '#CA8A04'};font-weight:700;">${state.isLiveBackend ? '🟢 Connected (FastAPI)' : '⚠ Offline (Using Local Fallback)'}</span></div>
        <div class="detail-row"><span class="detail-label">NASA FIRMS Service</span><span class="detail-value" style="color:#16A34A;">Integrated (Server-side Protected)</span></div>
        <div class="detail-row"><span class="detail-label">AI Classification Engine</span><span class="detail-value" style="color:#16A34A;">Modular Service (Active)</span></div>
        <div class="detail-row"><span class="detail-label">Risk Assessment Engine</span><span class="detail-value" style="color:#16A34A;">0–100 Multi-factor Model (Active)</span></div>
        <div class="detail-row"><span class="detail-label">Operator Emergency Mobilization</span><span class="detail-value" style="color:#16A34A;">Proximity Haversine Dispatch (Active)</span></div>
        <div class="detail-row"><span class="detail-label">Database Persistence</span><span class="detail-value" style="color:#16A34A;">SQLite / SQLAlchemy (Active)</span></div>
        <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.configureApiGateway()">
            🌐 Configure API Gateway URL
          </button>
        </div>
      </div>

      <!-- About -->
      <div class="card">
        <div class="card-title">About THERMOSAFE AI</div>
        <div style="font-size:13px;color:#4A5568;line-height:1.7;">
          <b style="color:#0B2545;">SIH26162</b> — AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources<br>
          Theme: Disaster Management · Ministry / Org: NTRO
        </div>
      </div>
    `;
  }

  /* ========== OPERATOR TEAM MANAGEMENT (PHASE 29 & 30) ========== */
  function renderOperatorTeamsPage() {
    const content = document.getElementById('content');
    if (!content) return;
    state.currentPage = 'operator-teams';

    const teams = state.operatorTeams || [];
    const activeCount = teams.filter(t => t.is_active !== false).length;
    const notifCount = teams.filter(t => t.notification_enabled !== false).length;
    const callCount = teams.filter(t => t.call_escalation_enabled !== false).length;

    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
        <div>
          <div style="font-size:22px;font-weight:800;color:var(--navy);letter-spacing:-0.3px;">Operator Teams & Response Units</div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
            Registry of emergency response teams, hazmat units, and industrial brigades for proximity alert routing and call escalation.
          </div>
        </div>
        <button class="btn btn-primary" onclick="window.__thermosafe.openTeamModal()">
          + Register Operator Team
        </button>
      </div>

      <div class="kpi-grid" style="margin-bottom:18px;">
        <div class="kpi-card info">
          <div class="kpi-label">Registered Teams</div>
          <div class="kpi-value">${teams.length}</div>
          <div class="kpi-sub">Total operational units</div>
        </div>
        <div class="kpi-card low">
          <div class="kpi-label">Active / Ready</div>
          <div class="kpi-value">${activeCount}</div>
          <div class="kpi-sub">Available for dispatch</div>
        </div>
        <div class="kpi-card medium">
          <div class="kpi-label">Push Alerts Active</div>
          <div class="kpi-value">${notifCount}</div>
          <div class="kpi-sub">Real-time alert routing</div>
        </div>
        <div class="kpi-card critical">
          <div class="kpi-label">Phone Escalation</div>
          <div class="kpi-value">${callCount}</div>
          <div class="kpi-sub">Unacknowledged escalation</div>
        </div>
      </div>

      <div class="card" style="padding:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">
          <div class="card-title" style="margin:0;">Configured Response Units</div>
          <div style="font-size:12px;color:var(--text-muted);">
            Proximity Haversine routing connects incidents to the nearest capable unit.
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px;">
          ${teams.length > 0 ? teams.map(t => {
            const teamName = t.team_name || t.name;
            const orgName = t.organization_name || 'Industrial Command';
            const facName = t.facility_name || (t.facility ? t.facility.name : (t.facility_id ? `Facility #${t.facility_id}` : 'General Sector (No Direct Facility)'));
            const facType = t.facility_type || t.industry_type || (t.facility ? t.facility.type : 'Industrial Perimeter');
            const spec = t.specialization || t.team_type || 'Industrial Fire Brigade';
            const isActive = t.is_active !== false;
            const notifOn = t.notification_enabled !== false;
            const callOn = t.call_escalation_enabled !== false;
            const radius = t.response_radius_km || t.coverage_radius_km || 50;
            const phone = t.team_phone || t.phone || t.contact_phone || 'Unconfigured';
            const email = t.team_email || t.email || t.contact_email || 'Unconfigured';
            const contact = t.contact_person || 'Commanding Officer';
            const members = Array.isArray(t.team_members) && t.team_members.length > 0
              ? t.team_members.join(', ')
              : (t.assigned_users && t.assigned_users.length > 0
                  ? t.assigned_users.map(u => u.full_name || u.email).join(', ')
                  : 'Duty Watch Crew');

            return `
              <div style="background:var(--bg-section);border:1px solid var(--border);border-radius:8px;padding:16px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:10px;">
                  <div>
                    <div style="font-weight:800;font-size:16px;color:var(--navy);display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                      <span>${escapeHtml(teamName)}</span>
                      <span class="risk-badge ${isActive ? 'risk-low' : 'risk-critical'}" style="font-size:10px;">
                        ${isActive ? 'Active' : 'Inactive'}
                      </span>
                      <span class="risk-badge ${notifOn ? 'risk-gas' : 'risk-low'}" style="font-size:10px;">
                        ${notifOn ? '🔔 Alerts ON' : '🔕 Alerts OFF'}
                      </span>
                      <span class="risk-badge ${callOn ? 'risk-high' : 'risk-low'}" style="font-size:10px;">
                        ${callOn ? '📞 Call Escalation ON' : '📵 Call Escalation OFF'}
                      </span>
                    </div>
                    <div style="font-size:12px;color:var(--text-secondary);margin-top:3px;">
                      <b>${escapeHtml(orgName)}</b> · Specialization: <span style="font-weight:700;color:var(--blue);">${escapeHtml(spec)}</span>
                    </div>
                  </div>
                  <div style="display:flex;gap:6px;">
                    <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.openTeamModal(${t.id})">Edit</button>
                    <button class="btn btn-outline btn-sm" onclick="window.__thermosafe.toggleTeamActive(${t.id})">
                      ${isActive ? 'Deactivate' : 'Activate'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="window.__thermosafe.deleteTeam(${t.id})">Delete</button>
                  </div>
                </div>

                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:8px;font-size:12px;background:#fff;padding:10px 14px;border-radius:6px;border:1px solid var(--border);">
                  <div><b>Associated Facility:</b> <span style="color:var(--navy);">${escapeHtml(facName)}</span></div>
                  <div><b>Facility Type:</b> <span style="color:var(--navy);">${escapeHtml(facType)}</span></div>
                  <div><b>Official Phone:</b> <span style="font-family:monospace;font-weight:700;color:var(--navy);">${escapeHtml(phone)}</span></div>
                  <div><b>Official Email:</b> <span>${escapeHtml(email)}</span></div>
                  <div><b>Duty Officer:</b> <span>${escapeHtml(contact)}</span></div>
                  <div><b>Coverage Radius:</b> <span>${radius} km</span></div>
                  <div><b>Coordinates:</b> <span style="font-family:monospace;">${Number(t.latitude).toFixed(4)}°N, ${Number(t.longitude).toFixed(4)}°E</span></div>
                  <div><b>Team Members:</b> <span>${escapeHtml(members)}</span></div>
                </div>
              </div>
            `;
          }).join('') : `
            <div style="text-align:center;padding:36px 20px;color:var(--text-muted);font-size:13px;background:var(--bg-section);border-radius:8px;">
              <div style="font-size:32px;margin-bottom:8px;">🚒</div>
              No emergency operator teams currently configured.<br>
              Click <b>+ Register Operator Team</b> to establish local response units for emergency alert routing.
            </div>
          `}
        </div>
      </div>
    `;
    updateDebugDiagnostics();
  }

  function openTeamModal(teamId = null) {
    const modal = document.getElementById('teamModal');
    const backdrop = document.getElementById('teamBackdrop');
    const body = document.getElementById('teamModalBody');
    const title = document.getElementById('teamModalTitle');
    if (!modal || !backdrop || !body) return;

    let team = null;
    if (teamId && state.operatorTeams) {
      team = state.operatorTeams.find(t => t.id === teamId);
    }

    if (title) {
      title.textContent = team ? `Edit Operator Team: ${team.team_name || team.name}` : 'Register New Operator Team';
    }

    const tName = team ? (team.team_name || team.name || '') : '';
    const tOrg = team ? (team.organization_name || '') : '';
    const tFacId = team ? (team.facility_id || '') : '';
    const tFacType = team ? (team.facility_type || team.industry_type || '') : '';
    const tSpec = team ? (team.specialization || team.team_type || 'Industrial Fire Brigade') : 'Industrial Fire Brigade';
    const tContact = team ? (team.contact_person || '') : '';
    const tEmail = team ? (team.team_email || team.email || team.contact_email || '') : '';
    const tPhone = team ? (team.team_phone || team.phone || team.contact_phone || '') : '';
    const tLat = team ? team.latitude : 22.3039;
    const tLng = team ? team.longitude : 70.8022;
    const tRadius = team ? (team.response_radius_km || team.coverage_radius_km || 50) : 50;
    const tMembers = team && Array.isArray(team.team_members) ? team.team_members.join(', ') : '';
    const tNotif = team ? (team.notification_enabled !== false) : true;
    const tCallEscalation = team ? (team.call_escalation_enabled !== false) : true;
    const tActive = team ? (team.is_active !== false) : true;

    body.innerHTML = `
      <form id="teamForm" onsubmit="window.__thermosafe.handleTeamSubmit(event, ${team ? team.id : 'null'})" style="display:flex;flex-direction:column;gap:12px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Team Name *</label>
            <input type="text" id="tName" required value="${escapeHtml(tName)}" placeholder="e.g. Jamnagar Hazmat Quick Reaction Unit" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Organization *</label>
            <input type="text" id="tOrg" required value="${escapeHtml(tOrg)}" placeholder="e.g. Gujarat State Disaster Response" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Associated Facility</label>
            <select id="tFacId" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 8px;font-family:inherit;font-size:13px;outline:none;background:#fff;">
              <option value="">-- No Direct Facility (District Unit) --</option>
              ${currentFacilities.map(f => `
                <option value="${f.dbId || f.id}" ${String(f.dbId) === String(tFacId) ? 'selected' : ''}>
                  ${escapeHtml(f.name)} (${escapeHtml(f.type)})
                </option>
              `).join('')}
            </select>
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Facility Type</label>
            <input type="text" id="tFacType" value="${escapeHtml(tFacType)}" placeholder="e.g. Refinery / Chemical SEZ / Power Station" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Specialization *</label>
            <select id="tSpecialization" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 8px;font-family:inherit;font-size:13px;outline:none;background:#fff;">
              <option value="Industrial Fire Brigade" ${tSpec === 'Industrial Fire Brigade' ? 'selected' : ''}>Industrial Fire Brigade</option>
              <option value="Hazmat Response Unit" ${tSpec === 'Hazmat Response Unit' ? 'selected' : ''}>Hazmat Response Unit</option>
              <option value="Petrochemical Fire & Hazmat" ${tSpec === 'Petrochemical Fire & Hazmat' ? 'selected' : ''}>Petrochemical Fire & Hazmat</option>
              <option value="Medical Emergency Squad" ${tSpec === 'Medical Emergency Squad' ? 'selected' : ''}>Medical Emergency Squad</option>
              <option value="Disaster Containment Unit" ${tSpec === 'Disaster Containment Unit' ? 'selected' : ''}>Disaster Containment Unit</option>
              <option value="Rapid Tactical Response" ${tSpec === 'Rapid Tactical Response' ? 'selected' : ''}>Rapid Tactical Response</option>
            </select>
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Duty Officer / Contact Person</label>
            <input type="text" id="tContact" value="${escapeHtml(tContact)}" placeholder="Commanding Officer" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Official Team Phone *</label>
            <input type="tel" id="tPhone" required value="${escapeHtml(tPhone)}" placeholder="+91-288-2234-911" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Official Team Email *</label>
            <input type="email" id="tEmail" required value="${escapeHtml(tEmail)}" placeholder="unit@ops.gov.in" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Latitude *</label>
            <input type="number" step="any" id="tLat" required value="${tLat}" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Longitude *</label>
            <input type="number" step="any" id="tLng" required value="${tLng}" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Radius (km) *</label>
            <input type="number" id="tRadius" required value="${tRadius}" min="1" max="500" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
        </div>

        <div>
          <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Team Members (Names / Call-signs)</label>
          <input type="text" id="tMembers" value="${escapeHtml(tMembers)}" placeholder="e.g. Insp. Sharma, Sub-Insp. Patel, Hazmat Tech Rao" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
        </div>

        <div style="display:flex;flex-direction:column;gap:8px;margin-top:6px;background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);">
          <label style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--navy);cursor:pointer;">
            <input type="checkbox" id="tActive" ${tActive ? 'checked' : ''} />
            Operational / Active Status (Ready for automatic dispatch)
          </label>
          <label style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--navy);cursor:pointer;">
            <input type="checkbox" id="tNotif" ${tNotif ? 'checked' : ''} />
            Emergency Alerts & Push Notifications Enabled
          </label>
          <label style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--navy);cursor:pointer;">
            <input type="checkbox" id="tCallEscalation" ${tCallEscalation ? 'checked' : ''} />
            Phone Call Escalation Enabled (Trigger call simulation if critical alert remains unacknowledged)
          </label>
        </div>

        <div id="teamError" style="display:none;background:#FEE2E2;color:#DC2626;border:1px solid #FCA5A5;padding:8px 12px;border-radius:6px;font-size:12px;font-weight:600;line-height:1.4;"></div>

        <div style="display:flex;gap:8px;margin-top:8px;">
          <button type="submit" id="teamSubmitBtn" class="btn btn-primary" style="flex:1;height:40px;">
            ${team ? 'Save Team Changes' : 'Create Operator Team'}
          </button>
          <button type="button" class="btn btn-outline" style="height:40px;" onclick="window.__thermosafe.closeTeamModal()">Cancel</button>
        </div>
      </form>
    `;

    modal.style.display = 'block';
    backdrop.style.display = 'block';
  }

  function closeTeamModal() {
    const modal = document.getElementById('teamModal');
    const backdrop = document.getElementById('teamBackdrop');
    if (modal) modal.style.display = 'none';
    if (backdrop) backdrop.style.display = 'none';
  }

  async function handleTeamSubmit(event, teamId) {
    event.preventDefault();
    const btn = document.getElementById('teamSubmitBtn');
    const errBox = document.getElementById('teamError');
    if (errBox) errBox.style.display = 'none';

    try {
      const emailVal = document.getElementById('tEmail').value.trim();
      if (emailVal && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
        throw new Error('Please provide a valid official email address.');
      }

      const phoneVal = document.getElementById('tPhone').value.trim();
      const digits = phoneVal.replace(/\D/g, '');
      if (digits.length < 7) {
        throw new Error('Please provide a valid official telephone number (minimum 7 digits).');
      }

      const latVal = parseFloat(document.getElementById('tLat').value);
      const lngVal = parseFloat(document.getElementById('tLng').value);
      if (isNaN(latVal) || latVal < -90 || latVal > 90) {
        throw new Error('Latitude must be between -90 and 90 degrees.');
      }
      if (isNaN(lngVal) || lngVal < -180 || lngVal > 180) {
        throw new Error('Longitude must be between -180 and 180 degrees.');
      }

      if (btn) { btn.disabled = true; btn.textContent = 'Saving...'; }

      const rawMembers = document.getElementById('tMembers').value;
      const memberList = rawMembers ? rawMembers.split(',').map(s => s.trim()).filter(Boolean) : [];

      const payload = {
        name: document.getElementById('tName').value.trim(),
        team_name: document.getElementById('tName').value.trim(),
        organization_name: document.getElementById('tOrg').value.trim() || 'Industrial Emergency Response',
        facility_id: document.getElementById('tFacId').value ? parseInt(document.getElementById('tFacId').value) : null,
        facility_type: document.getElementById('tFacType').value.trim() || null,
        industry_type: document.getElementById('tFacType').value.trim() || null,
        specialization: document.getElementById('tSpecialization').value.trim() || 'Industrial Fire Brigade',
        team_type: document.getElementById('tSpecialization').value.trim() || 'Industrial Fire Brigade',
        contact_person: document.getElementById('tContact').value.trim() || null,
        phone: phoneVal,
        team_phone: phoneVal,
        contact_phone: phoneVal,
        email: emailVal,
        team_email: emailVal,
        contact_email: emailVal,
        latitude: latVal,
        longitude: lngVal,
        response_radius_km: parseFloat(document.getElementById('tRadius').value) || 50,
        coverage_radius_km: parseFloat(document.getElementById('tRadius').value) || 50,
        team_members: memberList,
        notification_enabled: document.getElementById('tNotif').checked,
        call_escalation_enabled: document.getElementById('tCallEscalation').checked,
        is_active: document.getElementById('tActive').checked
      };

      if (teamId) {
        await apiClient.updateOperatorTeam(teamId, payload);
        showToast('Team Updated', `Operator team '${payload.team_name}' updated successfully.`, 'low');
      } else {
        await apiClient.createOperatorTeam(payload);
        showToast('Team Registered', `New operator team '${payload.team_name}' registered.`, 'low');
      }

      closeTeamModal();
      const updatedTeams = await apiClient.getOperatorTeams();
      if (updatedTeams) state.operatorTeams = updatedTeams;
      if (state.currentPage === 'operator-teams') renderOperatorTeamsPage();
      else if (state.currentPage === 'settings') renderSettingsPage();
    } catch (err) {
      if (errBox) {
        errBox.textContent = err.message || 'Error saving operator team.';
        errBox.style.display = 'block';
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = teamId ? 'Save Team Changes' : 'Create Operator Team';
      }
    }
  }

  async function toggleTeamActive(teamId) {
    const team = state.operatorTeams?.find(t => t.id === teamId);
    if (!team) return;
    try {
      const res = await apiClient.request(`/api/operator-teams/${teamId}/toggle-active`, { method: 'PATCH' });
      if (res) {
        team.is_active = res.is_active;
        showToast('Status Updated', `Team '${res.team_name || res.name}' is now ${res.is_active ? 'Active' : 'Inactive'}.`, 'low');
      }
      if (state.currentPage === 'operator-teams') renderOperatorTeamsPage();
      else if (state.currentPage === 'settings') renderSettingsPage();
    } catch (err) {
      showToast('Error', err.message || 'Could not update team status.', 'high');
    }
  }

  async function deleteTeam(teamId) {
    if (!confirm('Are you sure you want to delete this operator team?')) return;
    try {
      await apiClient.deleteOperatorTeam(teamId);
      state.operatorTeams = state.operatorTeams.filter(t => t.id !== teamId);
      showToast('Team Deleted', 'Operator team removed from registry.', 'low');
      if (state.currentPage === 'operator-teams') renderOperatorTeamsPage();
      else if (state.currentPage === 'settings') renderSettingsPage();
    } catch (err) {
      showToast('Error', err.message || 'Could not delete team.', 'high');
    }
  }

  /* ========== LOGIN & REGISTRATION PAGE (PHASE 27) ========== */
  function renderLoginPage(mode = 'login') {
    const content = document.getElementById('content');
    if (!content) return;
    state.currentPage = 'login';
    const isLogin = mode === 'login';

    content.innerHTML = `
      <div style="min-height: calc(100vh - 120px); display: flex; align-items: center; justify-content: center; padding: 24px 16px; background: linear-gradient(180deg, #F5F8FC 0%, #FFFFFF 100%);">
        <div class="card" style="width: 100%; max-width: 440px; box-shadow: var(--shadow-lg); border-top: 4px solid var(--blue); padding: 28px 24px;">
          <div style="text-align: center; margin-bottom: 22px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; background: linear-gradient(135deg, var(--c-critical), var(--c-high)); border-radius: 12px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(220,38,38,0.25);">
              <span style="font-size: 24px;">🔥</span>
            </div>
            <div style="font-size: 20px; font-weight: 800; color: var(--navy); letter-spacing: -0.3px;">THERMOSAFE AI</div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px; font-weight: 600;">
              Industrial Thermal Intelligence · Ministry / Org: NTRO
            </div>
            <div style="display: inline-block; margin-top: 8px; font-size: 11px; font-weight: 700; color: var(--blue); background: var(--blue-light); padding: 3px 10px; border-radius: 12px; border: 1px solid var(--border);">
              🔒 Protected Command Access
            </div>
          </div>

          <div style="display:flex;gap:8px;margin-bottom:20px;background:var(--bg-section);padding:4px;border-radius:8px;border:1px solid var(--border);">
            <button type="button" style="flex:1;padding:9px;border:none;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;background:${isLogin ? 'var(--blue)' : 'transparent'};color:${isLogin ? '#fff' : 'var(--navy)'};transition:all 0.2s;" onclick="window.__thermosafe.renderLoginPage('login')">Sign In</button>
            <button type="button" style="flex:1;padding:9px;border:none;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;background:${!isLogin ? 'var(--blue)' : 'transparent'};color:${!isLogin ? '#fff' : 'var(--navy)'};transition:all 0.2s;" onclick="window.__thermosafe.renderLoginPage('signup')">Create Account</button>
          </div>

          <form id="authForm" onsubmit="window.__thermosafe.handleAuthSubmit(event, '${mode}')" style="display:flex;flex-direction:column;gap:13px;">
            ${!isLogin ? `
              <div>
                <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Full Name *</label>
                <input type="text" id="authFullName" required placeholder="e.g. Commander Rajesh V." style="width:100%;height:40px;border:1px solid var(--border);border-radius:6px;padding:0 12px;font-family:inherit;font-size:13px;outline:none;" />
              </div>
              <div>
                <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Operational Role *</label>
                <select id="authRole" style="width:100%;height:40px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;background:#fff;">
                  <option value="admin">Admin (Platform Administrator)</option>
                  <option value="operator">Operator (Emergency Responder)</option>
                  <option value="analyst" selected>Analyst (Thermal Intelligence Analyst)</option>
                  <option value="viewer">Viewer (Facility Observer)</option>
                </select>
              </div>
            ` : ''}
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Email Address *</label>
              <input type="email" id="authEmail" required placeholder="analyst@domain.gov.in" style="width:100%;height:40px;border:1px solid var(--border);border-radius:6px;padding:0 12px;font-family:inherit;font-size:13px;outline:none;" />
            </div>
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Password *</label>
              <input type="password" id="authPassword" required minlength="6" placeholder="••••••••••••" style="width:100%;height:40px;border:1px solid var(--border);border-radius:6px;padding:0 12px;font-family:inherit;font-size:13px;outline:none;" />
            </div>
            ${!isLogin ? `
              <div>
                <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Confirm Password *</label>
                <input type="password" id="authConfirmPassword" required minlength="6" placeholder="••••••••••••" style="width:100%;height:40px;border:1px solid var(--border);border-radius:6px;padding:0 12px;font-family:inherit;font-size:13px;outline:none;" />
              </div>
            ` : ''}
            <div id="authError" style="display:none;background:#FEE2E2;color:#DC2626;border:1px solid #FCA5A5;padding:10px 12px;border-radius:6px;font-size:12px;font-weight:600;line-height:1.4;"></div>
            <button type="submit" id="authSubmitBtn" class="btn btn-primary btn-block" style="margin-top:4px;height:42px;font-size:14px;font-weight:700;">
              ${isLogin ? 'Sign In to Platform' : 'Create Account'}
            </button>
            <div style="text-align:center;font-size:12px;color:var(--text-secondary);margin-top:6px;">
              ${isLogin ? 
                `Don't have an account? <a href="javascript:void(0)" onclick="window.__thermosafe.renderLoginPage('signup')" style="color:var(--blue);font-weight:700;text-decoration:none;">Create an account</a>` : 
                `Already have an account? <a href="javascript:void(0)" onclick="window.__thermosafe.renderLoginPage('login')" style="color:var(--blue);font-weight:700;text-decoration:none;">Sign In</a>`}
            </div>
          </form>
        </div>
      </div>
    `;
    updateDebugDiagnostics();
  }

  /* ========== NAVIGATION ========== */
  function navigateTo(page) {
    state.currentPage = page;
    document.querySelectorAll('.sidebar .nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-page') === page);
    });
    document.querySelectorAll('.mobile-nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-page') === page);
    });

    if (page === 'login') renderLoginPage('login');
    else if (page === 'dashboard') renderDashboard();
    else if (page === 'map') renderMapPage();
    else if (page === 'incidents') renderIncidentsPage();
    else if (page === 'analytics') renderAnalyticsPage();
    else if (page === 'alerts') renderAlertsPage();
    else if (page === 'reports') renderReportsPage();
    else if (page === 'operator-teams') renderOperatorTeamsPage();
    else if (page === 'settings') renderSettingsPage();

    updateDebugDiagnostics();
  }

  /* ========== SIMULATION ========== */
  async function simulate(type) {
    // If backend is connected or in live mode, trigger the real intelligence pipeline
    if (state.backendConnected || state.isLiveBackend) {
      try {
        showToast('Processing Pipeline...', `Dispatching ${type} to AI & routing engine...`, 'low');
        const res = await apiClient.simulateThermalEvent(type);
        if (res && res.event) {
          const te = res.event;
          const pipe = res.pipeline || {};
          const al = pipe.alert || null;
          const assigned = pipe.assigned_team || {};

          const newEv = {
            id: te.event_id || te.id,
            dbId: te.id,
            lat: te.latitude,
            latitude: te.latitude,
            lng: te.longitude,
            longitude: te.longitude,
            city: te.city || 'Jamnagar',
            state: te.state || 'Gujarat',
            classification: te.classification || te.event_type || type,
            eventType: te.event_type || te.classification || type,
            event_type: te.event_type || te.classification || type,
            risk: te.risk_priority || 'CRITICAL',
            riskPriority: te.risk_priority || 'CRITICAL',
            risk_priority: te.risk_priority || 'CRITICAL',
            score: Math.round(te.risk_score || 85),
            riskScore: Math.round(te.risk_score || 85),
            risk_score: Math.round(te.risk_score || 85),
            confidence: Math.round(te.confidence || 95),
            intensity: te.thermal_intensity || 'High',
            persistence: te.persistence || 'Sustained',
            facility: te.facility_name || 'Petrochemical Complex',
            facilityOperator: assigned.team_name || 'Jamnagar Industrial Fire & Hazmat Battalion',
            landcover: te.land_cover || 'Industrial Perimeter',
            source: te.data_source || 'NASA FIRMS (Simulation)',
            detected: new Date(te.detected_at || Date.now()).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }),
            explanation: te.ai_explanation || 'Thermal anomaly processed via automated risk and operator routing pipeline.',
            factors: [
              { label:'Proximity to Facility', pct:35 },
              { label:'Thermal Intensity', pct:25 },
              { label:'Persistence', pct:20 },
              { label:'Historical Frequency', pct:10 },
              { label:'Environmental Vulnerability', pct:10 }
            ]
          };

          currentEvents.unshift(newEvent);
          renderMarkers();

          if (al) {
            addNotification(
              al.severity ? al.severity.toLowerCase() : 'critical',
              al.title || `${type} Alert`,
              al.message || `Automated alert for event ${newEvent.id}`,
              newEvent.id,
              {
                dbId: al.id,
                latitude: newEvent.lat,
                longitude: newEvent.lng,
                event_type: newEvent.classification,
                risk_priority: al.severity || 'CRITICAL',
                risk_score: newEvent.score
              }
            );
          }

          selectEvent(newEvent.id);
          viewAlertOnMap(newEvent.id);
          showToast('Pipeline Event Generated', `Event ${newEvent.id} created & routed to ${assigned.team_name || 'Operator Team'}.`, 'high', newEvent.id);
          return;
        }
      } catch (err) {
        console.warn('Backend simulate pipeline failed, falling back to local simulation:', err);
      }
    }

    if (state.dataSource !== 'demo') {
      setDataSource('demo', true);
    }

    state.simCounter++;
    const id = 'TH-2026-00' + state.simCounter;
    const templates = {
      'Industrial Fire':           { classif:'Industrial Fire', risk:'CRITICAL', score:88 + Math.floor(Math.random()*10), conf:90 + Math.floor(Math.random()*8), facility:'Chemical Plant' },
      'High-Risk Thermal':         { classif:'Industrial Fire', risk:'HIGH', score:74 + Math.floor(Math.random()*12), conf:82 + Math.floor(Math.random()*10), facility:'Steel Plant' },
      'Gas Flare':                 { classif:'Gas Flare', risk:'MEDIUM', score:58 + Math.floor(Math.random()*12), conf:76 + Math.floor(Math.random()*10), facility:'Oil Refinery' },
      'Persistent Thermal Source': { classif:'Persistent Thermal Source', risk:'HIGH', score:75 + Math.floor(Math.random()*15), conf:85 + Math.floor(Math.random()*10), facility:'Thermal Power Plant' }
    };
    const t = templates[type] || templates['Industrial Fire'];
    const cities = [
      { city:'Jamnagar', state:'Gujarat', lat:22.3039, lng:70.8022 },
      { city:'Hazira', state:'Gujarat', lat:21.1167, lng:72.6500 },
      { city:'Visakhapatnam', state:'Andhra Pradesh', lat:17.6868, lng:83.2185 },
      { city:'Mumbai', state:'Maharashtra', lat:19.0760, lng:72.8777 }
    ];
    const loc = cities[Math.floor(Math.random() * cities.length)];
    const jitter = () => (Math.random() - 0.5) * 0.4;
    const finalLat = loc.lat + jitter();
    const finalLng = loc.lng + jitter();

    const newEvent = {
      id,
      lat: finalLat,
      latitude: finalLat,
      lng: finalLng,
      longitude: finalLng,
      city: loc.city,
      state: loc.state,
      classification: t.classif,
      eventType: t.classif,
      event_type: t.classif,
      risk: t.risk,
      riskPriority: t.risk,
      risk_priority: t.risk,
      score: t.score,
      riskScore: t.score,
      risk_score: t.score,
      confidence: t.conf,
      intensity:'HIGH',
      persistence:'2.4 hours',
      facility: t.facility,
      landcover:'Industrial',
      source:'NASA FIRMS (Simulation)',
      detected: new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }),
      explanation: 'Simulated high-radiance thermal anomaly for presentation validation.',
      factors: [
        { label:'Thermal intensity', pct:35 },
        { label:'Industrial proximity', pct:35 },
        { label:'Persistence', pct:20 },
        { label:'Historical pattern', pct:10 }
      ]
    };

    DEMO_DATA.events.unshift(newEvent);
    currentEvents = DEMO_DATA.events;
    renderMarkers();
    addNotification(t.risk === 'CRITICAL' ? 'critical' : 'high',
      `${t.classif} Detected — ${loc.city}`,
      `Thermal activity detected near ${t.facility}. Risk Score: ${t.score}/100.`,
      id,
      {
        latitude: finalLat,
        longitude: finalLng,
        event_type: t.classif,
        risk_priority: t.risk,
        risk_score: t.score
      }
    );
    selectEvent(id);
    if (state.currentPage === 'dashboard') {
      const mapEl = document.getElementById('map');
      if (mapEl && state.map) {
        updateDashboardLiveView();
      } else {
        renderDashboard();
      }
    }
    else if (state.currentPage === 'map') renderMapPage();
    else if (state.currentPage === 'incidents') renderIncidentsPage();
  }

  function simulateCritical() {
    simulate('Industrial Fire');
  }

  function closeAckModal() {
    const modal = document.getElementById('ackModal');
    const backdrop = document.getElementById('ackBackdrop');
    if (modal) modal.style.display = 'none';
    if (backdrop) backdrop.style.display = 'none';
  }

  function openAcknowledgementModal(details) {
    const modal = document.getElementById('ackModal');
    const backdrop = document.getElementById('ackBackdrop');
    const body = document.getElementById('ackModalBody');
    if (!modal || !backdrop || !body) return;

    body.innerHTML = `
      <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:12px;margin-bottom:14px;">
        <div style="font-weight:800;color:#166534;font-size:14px;margin-bottom:2px;">Emergency Alert Successfully Acknowledged</div>
        <div style="font-size:12px;color:#15803D;">Incident logged in duty watch records. Operations & operator response synchronized.</div>
      </div>

      <div style="background:var(--bg-section);padding:14px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;">
        <div class="detail-row"><span class="detail-label">Acknowledged By</span><span class="detail-value" style="color:#0B2545;">${escapeHtml(details.acknowledgedBy)}</span></div>
        <div class="detail-row"><span class="detail-label">Acknowledged At</span><span class="detail-value font-mono">${escapeHtml(details.acknowledgedAt)}</span></div>
        <div class="detail-row"><span class="detail-label">Alert Severity</span><span class="detail-value">${riskBadge(details.severity)}</span></div>
        <div class="detail-row"><span class="detail-label">Event ID</span><span class="detail-value font-mono">${escapeHtml(details.eventId)}</span></div>
        <div class="detail-row"><span class="detail-label">Event Type</span><span class="detail-value">${escapeHtml(details.eventType)}</span></div>
        <div class="detail-row"><span class="detail-label">Risk Priority</span><span class="detail-value">${riskBadge(details.riskPriority)}</span></div>
        <div class="detail-row"><span class="detail-label">Risk Score</span><span class="detail-value" style="color:#DC2626;font-weight:800;">${details.riskScore}</span></div>
        <div class="detail-row"><span class="detail-label">Location</span><span class="detail-value">${escapeHtml(details.location)}</span></div>
        <div class="detail-row"><span class="detail-label">Emergency Unit</span><span class="detail-value">${escapeHtml(details.operatorTeam)}</span></div>
      </div>

      <div style="display:flex;gap:8px;">
        <button class="btn btn-primary btn-block" onclick="window.__thermosafe.closeAckModal(); window.__thermosafe.viewAlertOnMap('${details.alertId || details.eventId}');">
          View Incident on Map
        </button>
        <button class="btn btn-outline btn-block" onclick="window.__thermosafe.closeAckModal();">
          Close Confirmation
        </button>
      </div>
    `;

    modal.style.display = 'block';
    backdrop.style.display = 'block';
  }

  function showAckDetails(id) {
    const n = state.notifications.find(x => x.id === id || String(x.dbId) === String(id));
    if (!n) return;
    const ev = getEventById(n.eventId) || (n.thermalEventId ? getEventById(n.thermalEventId) : null);
    const locStr = ev ? `${ev.city}, ${ev.state} (${ev.lat.toFixed(4)}° N, ${ev.lng.toFixed(4)}° E)` : (n.latitude && n.longitude ? `${n.latitude.toFixed(4)}° N, ${n.longitude.toFixed(4)}° E` : 'Industrial Zone');
    const sevStr = n.level ? n.level.toUpperCase() : (n.raw?.severity || 'HIGH');
    const evtType = ev ? (ev.eventType || ev.classification) : (n.eventType || 'Thermal Incident');
    const riskPri = ev ? ev.risk : (n.riskPriority || sevStr);
    const rScore = ev ? `${ev.score}/100` : (n.riskScore ? `${n.riskScore}/100` : '—');
    const ackTime = new Date(n.acknowledgedAt || n.ts).toLocaleString();
    const opTeam = ev?.facilityOperator || ev?.facility || 'Jamnagar Petrochemical Hazmat & Fire Battalion';

    openAcknowledgementModal({
      acknowledgedBy: n.acknowledgedBy || 'Command Center Operator',
      acknowledgedAt: ackTime,
      severity: sevStr,
      eventId: n.eventId || (ev ? ev.id : 'TH-ALERT'),
      eventType: evtType,
      riskPriority: riskPri,
      riskScore: rScore,
      location: locStr,
      operatorTeam: opTeam,
      alertId: n.id
    });
  }

  async function acknowledge(id) {
    const n = state.notifications.find(x => x.id === id || String(x.dbId) === String(id));
    if (!n) return;

    if (n.isAcknowledged) {
      showToast('Already Acknowledged', `Alert ${n.id} has already been acknowledged.`, 'low');
      return;
    }

    const opName = state.currentUser ? (state.currentUser.full_name || state.currentUser.email) : 'Duty Watch Officer';
    const nowIso = new Date().toISOString();

    n.unread = false;
    n.isAcknowledged = true;
    n.acknowledgedBy = opName;
    n.acknowledgedAt = nowIso;

    if (n.dbId && (state.isLiveBackend || state.backendConnected)) {
      try {
        const resp = await apiClient.acknowledgeAlert(n.dbId, opName);
        if (resp) {
          n.isAcknowledged = true;
          n.acknowledgedBy = resp.acknowledged_by || opName;
          n.acknowledgedAt = resp.acknowledged_at || nowIso;
        }
      } catch (err) {
        console.warn('Backend acknowledgement error:', err);
        if (err.message && err.message.toLowerCase().includes('already')) {
          showToast('Already Acknowledged', 'This alert has already been acknowledged in the system.', 'low');
        }
      }
    }

    const ev = getEventById(n.eventId) || (n.thermalEventId ? getEventById(n.thermalEventId) : null);
    const locStr = ev ? `${ev.city}, ${ev.state} (${ev.lat.toFixed(4)}° N, ${ev.lng.toFixed(4)}° E)` : (n.latitude && n.longitude ? `${n.latitude.toFixed(4)}° N, ${n.longitude.toFixed(4)}° E` : 'Industrial Zone');
    const sevStr = n.level ? n.level.toUpperCase() : (n.raw?.severity || 'HIGH');
    const evtType = ev ? (ev.eventType || ev.classification) : (n.eventType || 'Thermal Incident');
    const riskPri = ev ? ev.risk : (n.riskPriority || sevStr);
    const rScore = ev ? `${ev.score}/100` : (n.riskScore ? `${n.riskScore}/100` : '—');
    const ackTime = new Date(n.acknowledgedAt || nowIso).toLocaleString();
    const opTeam = ev?.facilityOperator || ev?.facility || 'Jamnagar Industrial Fire & Hazmat Battalion';

    openAcknowledgementModal({
      acknowledgedBy: n.acknowledgedBy || opName,
      acknowledgedAt: ackTime,
      severity: sevStr,
      eventId: n.eventId || (ev ? ev.id : 'TH-ALERT'),
      eventType: evtType,
      riskPriority: riskPri,
      riskScore: rScore,
      location: locStr,
      operatorTeam: opTeam,
      alertId: n.id
    });

    renderDrawer();
    updateNotifBadge();
    if (state.currentPage === 'alerts') renderAlertsPage();
    showToast('Alert Acknowledged', `${n.id} acknowledged by ${opName}.`, 'low');
  }

  function viewAlertOnMap(id) {
    let ev = null;
    const notif = state.notifications.find(n => n.id === id || String(n.dbId) === String(id) || n.eventId === id);
    if (notif) {
      ev = getEventById(notif.eventId) || (notif.thermalEventId ? getEventById(notif.thermalEventId) : null);
      if (!ev && notif.latitude && notif.longitude) {
        ev = currentEvents.find(e => Math.abs(e.lat - notif.latitude) < 0.1 && Math.abs(e.lng - notif.longitude) < 0.1);
      }
    }
    if (!ev) {
      ev = getEventById(id);
    }
    if (!ev && currentEvents.length > 0) {
      ev = currentEvents[0];
    }
    if (!ev) return;

    state.selectedEvent = ev;
    closeDrawer();
    closeAckModal();
    closeAnalysisModal();

    // Navigate to dashboard if not on a map view
    if (state.currentPage !== 'dashboard' && state.currentPage !== 'map') {
      navigateTo('dashboard');
    }

    setTimeout(() => {
      if (state.map) {
        // Reset previous highlighted icon if exists
        if (state.highlightedEventId && state.markers[state.highlightedEventId]) {
          const prevEv = getEventById(state.highlightedEventId);
          if (prevEv) state.markers[state.highlightedEventId].setIcon(makeThermalIcon(prevEv, false));
        }
        state.highlightedEventId = ev.id;
        state.map.setView([ev.lat, ev.lng], 14, { animate: true });
        const marker = state.markers[ev.id];
        if (marker) {
          marker.setIcon(makeThermalIcon(ev, true));
          marker.openPopup();
        }
      }
      renderAIPanel(ev);
      showToast(
        `Centered on Incident`,
        `${ev.id} · ${ev.city}, ${ev.state} · Risk ${ev.risk}`,
        ev.risk === 'CRITICAL' ? 'critical' : 'high',
        ev.id
      );
    }, 150);
  }


  /* ========== REPORT GENERATION & DOWNLOAD ========== */
  function previewReport() {
    showToast('Report Preview', 'Full compliance audit preview loaded below.', 'low');
  }

  async function generateBackendReport() {
    const ev = state.selectedEvent || currentEvents[0];
    showToast('Generating Report', 'Creating structured report in database...', 'low');
    try {
      const res = await apiClient.createReport({
        title: `Thermal Incident Intelligence Report - ${ev.id}`,
        report_type: 'incident_report',
        filters: {
          risk_priority: ev.risk,
          event_type: ev.classification
        }
      });
      if (res && res.id) {
        showToast('Report Generated', `Report #${res.id} persisted to database.`, 'low');
        const list = await apiClient.getReports(10);
        if (list && list.items) state.backendReports = list.items;
        renderReportsPage();
      }
    } catch (err) {
      showToast('Report Error', err.message || 'Could not save to database.', 'high');
    }
  }

  async function downloadReport() {
    const ev = state.selectedEvent || currentEvents[0];
    if (state.isLiveBackend) {
      try {
        showToast('Exporting Report', 'Generating CSV export from backend...', 'low');
        const res = await apiClient.createReport({
          title: `Thermal Incident Export - ${ev.id}`,
          report_type: 'incident_report',
          filters: {
            risk_priority: ev.risk
          }
        });
        if (res && res.id) {
          const csvData = await apiClient.exportReportCsv(res.id);
          const blob = new Blob([csvData], { type: 'text/csv' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `thermo_report_${res.id}.csv`;
          a.click();
          URL.revokeObjectURL(url);
          showToast('Downloaded', `thermo_report_${res.id}.csv saved.`, 'low');
          return;
        }
      } catch (err) {
        console.warn('Backend export failed, falling back to local file', err);
      }
    }

    // Local fallback text file
    const txt = `THERMOSAFE AI — INCIDENT REPORT
================================================
Event ID: ${ev.id}
Location: ${ev.city}, ${ev.state}
Coordinates: ${ev.lat.toFixed(4)}° N, ${ev.lng.toFixed(4)}° E
Classification: ${ev.classification}
Risk Priority: ${ev.risk}
Risk Score: ${ev.score}/100
AI Confidence: ${ev.confidence}%
Thermal Intensity: ${ev.intensity}
Persistence: ${ev.persistence}
Nearby Facility: ${ev.facility || 'N/A'}
Source: ${ev.source}
Detected Time: ${ev.detected}
Explanation: ${ev.explanation}

⚠ Generated via THERMOSAFE AI Industrial Thermal Intelligence.
`;
    const blob = new Blob([txt], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${ev.id}-report.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Report Downloaded', `${ev.id}-report.txt saved.`, 'low');
  }

  function shareReport() {
    const ev = state.selectedEvent || currentEvents[0];
    if (navigator.share) {
      navigator.share({ title: 'THERMOSAFE AI Report', text: `Incident ${ev.id} — ${ev.classification} — Risk ${ev.risk}` }).catch(()=>{});
    } else {
      showToast('Share Link', 'Report link copied to clipboard.', 'low');
    }
  }

  /* ========== AUTHENTICATION MODAL & LOGIC ========== */
  function updateAuthUI() {
    state.authToken = localStorage.getItem('thermo_jwt_token') || null;
    const profileBtn = document.getElementById('profileBtn');
    const mobileProfileBtn = document.querySelector('.mobile-nav-item[data-page="settings"]');
    const u = state.currentUser || DEFAULT_LOCAL_OPERATOR;
    const initial = (u.full_name || u.name || u.email || 'T')[0].toUpperCase();

    if (profileBtn) {
      profileBtn.innerHTML = `
        <span style="width:22px;height:22px;border-radius:50%;background:var(--blue);color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;letter-spacing:0;">${escapeHtml(initial)}</span>
      `;
      profileBtn.setAttribute('title', `${u.full_name || u.name} (${u.role || 'Analyst'})`);
    }
    if (mobileProfileBtn) {
      mobileProfileBtn.setAttribute('title', `${u.full_name || u.name} (${u.role || 'Analyst'})`);
    }
    if (state.currentPage === 'settings') renderSettingsPage();
  }

  function openEditProfileModal() {
    const modal = document.getElementById('authModal');
    const backdrop = document.getElementById('authBackdrop');
    const body = document.getElementById('authModalBody');
    const title = document.getElementById('authModalTitle');
    if (!modal || !backdrop || !body) return;

    if (title) title.textContent = 'Edit Operator Profile';
    const u = state.currentUser || DEFAULT_LOCAL_OPERATOR;
    const curRole = (u.role || 'analyst').toLowerCase();

    body.innerHTML = `
      <form id="profileEditForm" onsubmit="window.__thermosafe.handleProfileSave(event)" style="display:flex;flex-direction:column;gap:12px;">
        <div>
          <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Operator Full Name *</label>
          <input type="text" id="profFullName" required value="${escapeHtml(u.full_name || u.name || '')}" placeholder="e.g. Commander Rajesh V." style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
        </div>
        <div>
          <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Email Address *</label>
          <input type="email" id="profEmail" required value="${escapeHtml(u.email || '')}" placeholder="analyst@domain.gov.in" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
        </div>
        <div>
          <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Operational Role *</label>
          <select id="profRole" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;background:#fff;">
            <option value="admin" ${curRole === 'admin' ? 'selected' : ''}>Admin (Platform Administrator)</option>
            <option value="operator" ${curRole === 'operator' ? 'selected' : ''}>Operator (Emergency Responder)</option>
            <option value="analyst" ${curRole === 'analyst' ? 'selected' : ''}>Analyst (Thermal Intelligence Analyst)</option>
            <option value="viewer" ${curRole === 'viewer' ? 'selected' : ''}>Viewer (Facility Observer)</option>
          </select>
        </div>
        <div>
          <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Operator Team Name</label>
          <input type="text" id="profTeam" value="${escapeHtml(u.operator_team_name || 'Operations Watch Desk')}" placeholder="e.g. Jamnagar Hazmat Unit" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
        </div>
        <div style="display:flex;gap:8px;margin-top:6px;">
          <button type="submit" class="btn btn-primary" style="flex:1;height:40px;">Save Profile</button>
          <button type="button" class="btn btn-outline" style="height:40px;" onclick="window.__thermosafe.openAuthModal('profile')">Cancel</button>
        </div>
      </form>
    `;

    modal.style.display = 'block';
    backdrop.style.display = 'block';
  }

  function handleProfileSave(event) {
    if (event) event.preventDefault();
    const fullName = document.getElementById('profFullName')?.value.trim() || 'ThermoSafe Operator';
    const email = document.getElementById('profEmail')?.value.trim() || 'local@thermosafe.ai';
    const role = document.getElementById('profRole')?.value || 'Analyst';
    const team = document.getElementById('profTeam')?.value.trim() || 'Operations Watch Desk';

    state.currentUser = {
      ...state.currentUser,
      full_name: fullName,
      name: fullName,
      email: email,
      role: role,
      operator_team_name: team
    };

    try {
      localStorage.setItem('thermo_operator_user', JSON.stringify(state.currentUser));
    } catch (_) {}

    updateAuthUI();
    closeAuthModal();
    showToast('Profile Updated', `Operator profile saved as ${fullName}.`, 'low');
    if (state.currentPage === 'settings') renderSettingsPage();
  }

  function openAuthModal(mode = 'profile') {
    const modal = document.getElementById('authModal');
    const backdrop = document.getElementById('authBackdrop');
    const body = document.getElementById('authModalBody');
    const title = document.getElementById('authModalTitle');
    if (!modal || !backdrop || !body) return;

    if (mode === 'login' || mode === 'signup') {
      if (title) title.textContent = mode === 'signup' ? 'Create Analyst Account (Backend)' : 'Security Authentication (Backend)';
      const isLogin = mode === 'login';
      body.innerHTML = `
        <div style="display:flex;gap:8px;margin-bottom:18px;background:var(--bg-section);padding:4px;border-radius:8px;border:1px solid var(--border);">
          <button type="button" style="flex:1;padding:8px;border:none;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;background:${isLogin ? 'var(--blue)' : 'transparent'};color:${isLogin ? '#fff' : 'var(--navy)'};" onclick="window.__thermosafe.openAuthModal('login')">Sign In</button>
          <button type="button" style="flex:1;padding:8px;border:none;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;background:${!isLogin ? 'var(--blue)' : 'transparent'};color:${!isLogin ? '#fff' : 'var(--navy)'};" onclick="window.__thermosafe.openAuthModal('signup')">Register</button>
        </div>
        <form id="authForm" onsubmit="window.__thermosafe.handleAuthSubmit(event, '${mode}')" style="display:flex;flex-direction:column;gap:12px;">
          ${!isLogin ? `
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Full Name *</label>
              <input type="text" id="authFullName" required placeholder="e.g. Commander Rajesh V." style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
            </div>
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Operational Role *</label>
              <select id="authRole" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;background:#fff;">
                <option value="admin">Platform Administrator (Admin)</option>
                <option value="operator">Emergency Dispatch / Operator</option>
                <option value="analyst" selected>Thermal Intelligence Analyst</option>
                <option value="viewer">Facility Responder / Viewer</option>
              </select>
            </div>
          ` : ''}
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Email Address *</label>
            <input type="email" id="authEmail" required placeholder="analyst@domain.gov.in" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Password *</label>
            <input type="password" id="authPassword" required minlength="6" placeholder="••••••••••••" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
          </div>
          ${!isLogin ? `
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px;">Confirm Password *</label>
              <input type="password" id="authConfirmPassword" required minlength="6" placeholder="••••••••••••" style="width:100%;height:38px;border:1px solid var(--border);border-radius:6px;padding:0 10px;font-family:inherit;font-size:13px;outline:none;" />
            </div>
          ` : ''}
          <div id="authError" style="display:none;background:#FEE2E2;color:#DC2626;border:1px solid #FCA5A5;padding:8px 12px;border-radius:6px;font-size:12px;font-weight:600;margin-top:4px;line-height:1.4;"></div>
          <button type="submit" id="authSubmitBtn" class="btn btn-primary btn-block" style="margin-top:6px;height:40px;">
            ${isLogin ? 'Sign In to Backend' : 'Create Backend Account'}
          </button>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:12px;">
            <a href="javascript:void(0)" onclick="window.__thermosafe.openAuthModal('profile')" style="color:var(--blue);font-weight:700;text-decoration:none;">← Return to Local Profile</a>
            ${isLogin ? 
              `<a href="javascript:void(0)" onclick="window.__thermosafe.openAuthModal('signup')" style="color:var(--text-muted);text-decoration:none;">Create account</a>` : 
              `<a href="javascript:void(0)" onclick="window.__thermosafe.openAuthModal('login')" style="color:var(--text-muted);text-decoration:none;">Sign In</a>`}
          </div>
        </form>
      `;
    } else {
      if (title) title.textContent = 'Operator Profile';
      const u = state.currentUser || DEFAULT_LOCAL_OPERATOR;
      const initial = (u.full_name || u.name || u.email || 'T')[0].toUpperCase();
      const isJwt = !!state.authToken;
      body.innerHTML = `
        <div style="text-align:center;margin-bottom:16px;">
          <div style="width:56px;height:56px;background:var(--blue-light);color:var(--blue);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;margin:0 auto 12px;font-weight:800;">
            ${escapeHtml(initial)}
          </div>
          <div style="font-weight:800;font-size:17px;color:var(--navy);">${escapeHtml(u.full_name || u.name || 'ThermoSafe Operator')}</div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">${escapeHtml(u.email || 'local@thermosafe.ai')}</div>
          <div style="margin-top:8px;">
            <span class="risk-badge risk-facility" style="text-transform:uppercase;">Role: ${escapeHtml((u.role || 'Analyst').toUpperCase())}</span>
          </div>
        </div>
        <div style="background:var(--bg-section);padding:12px;border-radius:8px;font-size:12px;margin-bottom:18px;border:1px solid var(--border);">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:var(--text-muted);">Session Type:</span>
            <span style="color:${isJwt ? '#16A34A' : 'var(--blue)'};font-weight:700;">● ${isJwt ? 'Server Authenticated (JWT)' : 'Local Operator Session'}</span>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:var(--text-muted);">Team:</span>
            <span style="color:var(--navy);font-weight:600;">${escapeHtml(u.operator_team_name || 'Operations Watch Desk')}</span>
          </div>
          <div style="display:flex;justify-content:space-between;">
            <span style="color:var(--text-muted);">API Base:</span>
            <span style="font-family:'Courier New',monospace;color:var(--navy);font-weight:600;">${API_BASE_URL}</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px;">
          <button class="btn btn-primary btn-block" onclick="window.__thermosafe.openEditProfileModal()">Edit Profile</button>
          <div style="display:flex;gap:8px;">
            <button class="btn btn-outline" style="flex:1;" onclick="window.__thermosafe.logout()">Reset Session</button>
            <button class="btn btn-outline" style="flex:1;" onclick="window.__thermosafe.openAuthModal('login')">Backend Login</button>
          </div>
        </div>
      `;
    }

    modal.style.display = 'block';
    backdrop.style.display = 'block';
  }

  function closeAuthModal() {
    const modal = document.getElementById('authModal');
    const backdrop = document.getElementById('authBackdrop');
    if (modal) modal.style.display = 'none';
    if (backdrop) backdrop.style.display = 'none';
  }

  async function handleAuthSubmit(event, mode) {
    event.preventDefault();
    const btn = document.getElementById('authSubmitBtn');
    const errBox = document.getElementById('authError');
    if (errBox) errBox.style.display = 'none';
    if (btn) { btn.disabled = true; btn.textContent = 'Processing...'; }

    try {
      const email = document.getElementById('authEmail').value.trim();
      const password = document.getElementById('authPassword').value;

      let res;
      if (mode === 'signup') {
        const fullName = document.getElementById('authFullName').value.trim();
        let role = document.getElementById('authRole')?.value || 'analyst';
        if (!['admin', 'operator', 'analyst', 'viewer'].includes(role)) role = 'analyst';
        const confirmPassword = document.getElementById('authConfirmPassword')?.value;
        if (confirmPassword && password !== confirmPassword) {
          throw new Error('Passwords do not match.');
        }
        res = await apiClient.signup(fullName, email, password, confirmPassword, role);
      } else {
        res = await apiClient.login(email, password);
      }

      if (res && res.access_token) {
        localStorage.setItem('thermo_jwt_token', res.access_token);
        state.authToken = res.access_token;
        state.currentUser = res.user;
        state.authStatus = 'authenticated';
        closeAuthModal();
        updateAuthUI();
        registerCurrentDevice().catch(()=>{});
        await setDataSource('live', true);
        const targetPage = state.pendingPage || 'dashboard';
        state.pendingPage = null;
        navigateTo(targetPage);
        showToast('Authentication Successful', `Welcome, ${state.currentUser.full_name}!`, 'low');
      }
    } catch (err) {
      if (errBox) {
        errBox.textContent = err.message || 'Authentication failed. Please verify credentials.';
        errBox.style.display = 'block';
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = mode === 'signup' ? 'Create Backend Account' : 'Sign In to Backend';
      }
    }
  }

  function logout() {
    localStorage.removeItem('thermo_jwt_token');
    localStorage.removeItem('thermo_operator_user');
    state.authToken = null;
    state.currentUser = { ...DEFAULT_LOCAL_OPERATOR };
    state.authStatus = 'local';
    closeAuthModal();
    updateAuthUI();
    showToast('Session Reset', 'Reset to default local operator session.', 'low');
    if (state.currentPage === 'settings') renderSettingsPage();
  }

  /* ========== DATA SOURCE MANAGEMENT (LIVE VS DEMO) ========== */
  let livePollingInterval = null;

  function updateDataSourceUI() {
    const isLive = state.dataSource === 'live';

    // Topbar Toggle buttons
    const btnLive = document.getElementById('btnSourceLive');
    const btnDemo = document.getElementById('btnSourceDemo');
    if (btnLive) {
      btnLive.classList.toggle('active-live', isLive);
      btnLive.classList.toggle('active-demo', false);
    }
    if (btnDemo) {
      btnDemo.classList.toggle('active-demo', !isLive);
      btnDemo.classList.toggle('active-live', false);
    }

    // Map page Toggle buttons (if present)
    const btnMapLive = document.getElementById('btnMapSourceLive');
    const btnMapDemo = document.getElementById('btnMapSourceDemo');
    if (btnMapLive) {
      btnMapLive.classList.toggle('active-live', isLive);
      btnMapLive.classList.toggle('active-demo', false);
    }
    if (btnMapDemo) {
      btnMapDemo.classList.toggle('active-demo', !isLive);
      btnMapDemo.classList.toggle('active-live', false);
    }

    // Topbar Pill
    const pill = document.getElementById('backendPill');
    if (pill) {
      if (state.dataSource === 'live' && state.backendConnected && state.dataState === 'LIVE') {
        pill.innerHTML = '● NASA FIRMS LIVE (INDIA)';
        pill.style.background = 'rgba(22,163,74,0.2)';
        pill.style.color = '#86EFAC';
        pill.style.borderColor = 'rgba(34,197,94,0.4)';
      } else if (state.dataState === 'CONNECTING') {
        pill.innerHTML = '● CONNECTING...';
        pill.style.background = 'rgba(59,130,246,0.2)';
        pill.style.color = '#93C5FD';
        pill.style.borderColor = 'rgba(59,130,246,0.4)';
      } else {
        pill.innerHTML = '● DATA SOURCE: DEMO DATA';
        pill.style.background = 'rgba(202,138,4,0.2)';
        pill.style.color = '#FDE047';
        pill.style.borderColor = 'rgba(202,138,4,0.4)';
      }
    }
  }

  function setBackendStatus(isLive) {
    state.backendConnected = isLive;
    state.isLiveBackend = isLive;
    updateDataSourceUI();
  }

  function stopLivePolling() {
    if (livePollingInterval) {
      clearInterval(livePollingInterval);
      livePollingInterval = null;
    }
    state.livePollingActive = false;
  }

  function startLivePolling() {
    stopLivePolling();
    state.livePollingActive = true;
    // Controlled refresh interval: Refresh every 10 minutes (600,000 ms) as specified
    livePollingInterval = setInterval(async () => {
      if (state.dataSource !== 'live') return;
      await fetchLiveData(true); // silent refresh
    }, 10 * 60 * 1000);
  }

  async function manualRefreshFirms() {
    const btn = document.getElementById('btnManualRefresh');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '↻ Syncing...';
    }
    try {
      showToast('NASA FIRMS Refresh', 'Fetching latest VIIRS Near-Real-Time observations...', 'low');
      await fetchLiveData(false);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = '↻ Refresh';
      }
    }
  }

  async function fetchLiveData(silent = false) {
    const reqId = ++state.liveFetchRequestId;
    try {
      const isHealthy = await apiClient.checkHealth();
      if (reqId !== state.liveFetchRequestId || state.dataSource !== 'live') return;
      state.backendConnected = isHealthy;
      state.isLiveBackend = isHealthy;
      updateDataSourceUI();

      if (!isHealthy) {
        const backendOfflineMsg = 'Live backend temporarily unavailable — displaying demonstration data.';
        state.lastApiError = backendOfflineMsg;
        activateDemoFallback(backendOfflineMsg);
        updateDebugDiagnostics();
        return;
      }

      // 1. Check & Fetch Live NASA FIRMS Satellite Telemetry
      state.lastFirmsFetchAttempt = new Date();
      console.log(`[ThermoSafe FIRMS] Live telemetry fetch started (seq: ${reqId})`);
      try {
        const satResp = await apiClient.getSatelliteThermalEvents('live');
        if (reqId !== state.liveFetchRequestId) return;
        if (satResp) {
          state.satelliteTelemetry = satResp;
          const rawEvents = satResp.data || satResp.events || satResp.items || [];
          const isSuccess = satResp.success === true || satResp.status === 'success' || satResp.status === 'ok';
          const isLive = satResp.live === true || satResp.connected === true;

          if (satResp.last_successful_fetch || satResp.last_updated) {
            state.lastSuccessfulFirmsFetch = new Date(satResp.last_successful_fetch || satResp.last_updated);
          }

          if (isSuccess && isLive) {
            state.dataState = 'LIVE';
            state.firmsState = satResp.status === 'LIVE_STALE' ? 'LIVE_STALE' : 'LIVE_CONNECTED';
            state.lastSuccessfulFirmsEventCount = rawEvents.length;
            state.lastFirmsError = null;
            state.lastApiError = null;
            state.lastSuccessfulFetch = new Date();
            LIVE_DATA.events = rawEvents.map(mapBackendEvent);
            currentEvents = LIVE_DATA.events;

            if (rawEvents.length === 0) {
              state.liveStatusMessage = satResp.message || '● NASA FIRMS LIVE (0 active hotspots)';
            } else {
              state.liveStatusMessage = satResp.message || (state.firmsState === 'LIVE_STALE' ? `● NASA FIRMS LIVE — CACHED (${state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : 'Recent'})` : '● NASA FIRMS LIVE');
            }

            if (state.currentPage === 'dashboard') {
              updateDashboardLiveView();
            } else {
              renderMarkers();
              if (state.currentPage === 'incidents') renderIncidentsPage();
            }

            console.log(`[ThermoSafe FIRMS] Telemetry synchronized: count=${rawEvents.length} state=${state.firmsState}`);
            if (!silent) {
              showToast('NASA FIRMS Live Connected', `Synchronized ${rawEvents.length} active live thermal hotspots.`, 'low');
            }
          } else {
            const safeError = satResp.error || satResp.message || 'NASA FIRMS service temporarily unavailable.';
            activateFirmsUnavailable(safeError);
          }
        }
      } catch (satErr) {
        console.warn('[ThermoSafe FIRMS] Live satellite telemetry fetch error:', satErr);
        activateFirmsUnavailable(satErr.message || 'NASA FIRMS service temporarily unavailable.');
      }

      // 1b. Fetch thermal events from backend database (ensures DB synchronization)
      try {
        const evResp = await apiClient.getThermalEvents(100, false);
        if (reqId !== state.liveFetchRequestId) return;
        if (evResp && evResp.items && evResp.items.length > 0) {
          const liveStored = evResp.items.filter(item => !item.is_demo).map(mapBackendEvent);
          if (liveStored.length > 0) {
            const idMap = new Map();
            (LIVE_DATA.events || []).forEach(e => idMap.set(e.id || e.dbId, e));
            liveStored.forEach(e => idMap.set(e.id || e.dbId, e));
            LIVE_DATA.events = Array.from(idMap.values());
            if (state.dataState === 'LIVE') {
              currentEvents = LIVE_DATA.events;
            }
          }
        }
      } catch (err) {
        console.warn('[ThermoSafe Debug] Live events fetch error:', err);
      }

      if (state.dataSource === 'live' && state.dataState === 'LIVE') {
        currentEvents = LIVE_DATA.events;
        if (state.currentPage === 'dashboard') {
          updateDashboardLiveView();
        } else {
          renderMarkers();
          if (state.currentPage === 'incidents') renderIncidentsPage();
        }
      }

      // 2. Fetch facilities
      try {
        const facResp = await apiClient.getFacilities(100);
        if (reqId !== state.liveFetchRequestId) return;
        if (facResp && facResp.items && facResp.items.length > 0) {
          LIVE_DATA.facilities = facResp.items.map(mapBackendFacility);
          if (state.dataSource === 'live') {
            currentFacilities = LIVE_DATA.facilities;
            if (state.currentPage === 'dashboard') {
              updateDashboardLiveView();
            } else {
              renderFacilities();
            }
          }
        }
      } catch (err) {
        console.warn('[ThermoSafe Debug] Live facilities fetch error:', err);
      }

      // 3. Fetch alerts
      try {
        const alertResp = await apiClient.getAlerts(50);
        if (reqId !== state.liveFetchRequestId) return;
        if (alertResp && alertResp.items && alertResp.items.length > 0) {
          LIVE_DATA.notifications = alertResp.items.map(mapBackendAlert);
          if (state.dataSource === 'live') {
            state.notifications = LIVE_DATA.notifications;
            renderDrawer();
            updateNotifBadge();
            if (state.currentPage === 'alerts') renderAlertsPage();
          }
        }
      } catch (err) {
        console.warn('[ThermoSafe Debug] Live alerts fetch error:', err);
      }

      // 4. Fetch analytics aggregations
      try {
        const [summary, riskDist, eventTypes, timeSeries] = await Promise.all([
          apiClient.getAnalyticsSummary(false),
          apiClient.getRiskDistribution(false),
          apiClient.getEventTypes(false),
          apiClient.getTimeSeries(false)
        ]);
        if (reqId !== state.liveFetchRequestId) return;
        LIVE_DATA.analytics = {
          summary,
          risk_distribution: riskDist,
          event_types: eventTypes,
          time_series: timeSeries
        };
        if (state.dataSource === 'live') {
          state.backendAnalytics = LIVE_DATA.analytics;
          if (state.currentPage === 'dashboard') {
            updateDashboardLiveView();
          } else if (state.currentPage === 'analytics') {
            renderAnalyticsPage();
          }
        }
      } catch (err) {
        console.warn('[ThermoSafe Debug] Live analytics fetch error:', err);
      }

      // 5. Fetch reports
      try {
        const reportsResp = await apiClient.getReports(10);
        if (reqId !== state.liveFetchRequestId) return;
        if (reportsResp && reportsResp.items) {
          LIVE_DATA.reports = reportsResp.items;
          if (state.dataSource === 'live') {
            state.backendReports = LIVE_DATA.reports;
            if (state.currentPage === 'reports') renderReportsPage();
          }
        }
      } catch (err) {
        console.warn('[ThermoSafe Debug] Live reports fetch error:', err);
      }

      // 6. Fetch Operator Teams
      try {
        const teamsResp = await apiClient.getOperatorTeams();
        if (reqId !== state.liveFetchRequestId) return;
        if (teamsResp) {
          LIVE_DATA.operatorTeams = teamsResp;
          if (state.dataSource === 'live') {
            state.operatorTeams = LIVE_DATA.operatorTeams;
            if (state.currentPage === 'settings') renderSettingsPage();
          }
        }
      } catch (err) {
        console.warn('[ThermoSafe Debug] Live operator teams fetch error:', err);
      }

      // 7. Check FCM Status
      try {
        const fcmResp = await apiClient.getFcmStatus();
        if (reqId !== state.liveFetchRequestId) return;
        if (fcmResp) {
          state.fcmStatus = fcmResp;
          if (state.currentPage === 'settings') renderSettingsPage();
        }
      } catch (err) {}

      state.lastSuccessfulFetch = new Date();
      state.lastApiError = null;
      updateDebugDiagnostics();

    } catch (err) {
      state.backendConnected = false;
      state.isLiveBackend = false;
      state.lastApiError = err.message || 'Fetch error';
      if (state.dataState !== 'LIVE' || LIVE_DATA.events.length === 0) {
        activateDemoFallback(err.message || 'Live backend connection error');
      } else {
        state.firmsState = 'LIVE_STALE';
        if (state.currentPage === 'dashboard') updateDashboardLiveView();
      }
      updateDataSourceUI();
      updateDebugDiagnostics();
    }
  }

  async function setDataSource(source, skipToast = false) {
    if (source === 'demo') {
      state.dataSource = 'demo';
      state.dataState = 'DEMO';
      state.firmsState = 'DEMO';
      currentEvents = DEMO_DATA.events;
      currentFacilities = DEMO_DATA.facilities;
      state.notifications = DEMO_DATA.notifications;
      stopLivePolling();
      updateDataSourceUI();
      if (state.currentPage === 'dashboard') {
        updateDashboardLiveView();
      } else {
        renderMarkers();
        if (state.showFacilities) renderFacilities();
        if (state.currentPage === 'incidents') renderIncidentsPage();
      }
      if (!skipToast) {
        showToast('Demo Mode Activated', 'Displaying simulated test dataset.', 'low');
      }
      return;
    }

    // Switch to LIVE mode: Production default
    state.dataSource = 'live';
    state.dataState = LIVE_DATA.events.length > 0 ? 'LIVE' : 'CONNECTING';
    currentEvents = LIVE_DATA.events;
    currentFacilities = LIVE_DATA.facilities.length > 0 ? LIVE_DATA.facilities : currentFacilities;
    state.notifications = LIVE_DATA.notifications;
    if (LIVE_DATA.analytics) state.backendAnalytics = LIVE_DATA.analytics;
    if (LIVE_DATA.reports) state.backendReports = LIVE_DATA.reports;
    if (LIVE_DATA.operatorTeams) state.operatorTeams = LIVE_DATA.operatorTeams;

    updateDataSourceUI();
    startLivePolling();
    await fetchLiveData(skipToast);

    renderDrawer();
    updateNotifBadge();

    // Re-render current page smoothly
    if (state.currentPage === 'dashboard') {
      const mapEl = document.getElementById('map');
      if (mapEl && state.map) {
        updateDashboardLiveView();
      } else {
        renderDashboard();
      }
    }
    else if (state.currentPage === 'map') renderMapPage();
    else if (state.currentPage === 'incidents') renderIncidentsPage();
    else if (state.currentPage === 'alerts') renderAlertsPage();
    else if (state.currentPage === 'analytics') renderAnalyticsPage();
    else if (state.currentPage === 'reports') renderReportsPage();
    else if (state.currentPage === 'settings') renderSettingsPage();

    updateDebugDiagnostics();
  }

  function toggleDataSource() {
    setDataSource(state.dataSource === 'live' ? 'demo' : 'live');
  }

  function getDataSource() {
    return state.dataSource;
  }

  async function initBackendSync() {
    updateDataSourceUI();

    // Verify stored user session in background if token exists
    if (localStorage.getItem('thermo_jwt_token')) {
      try {
        const backendUser = await apiClient.getCurrentUser();
        if (backendUser && backendUser.email) {
          state.currentUser = { ...state.currentUser, ...backendUser };
          state.authStatus = 'authenticated';
          updateAuthUI();
          registerCurrentDevice().catch(()=>{});
        }
      } catch (e) {
        console.warn('[ThermoSafe Debug] Stored session check notice:', e);
        localStorage.removeItem('thermo_jwt_token');
        state.authToken = null;
        state.authStatus = 'local';
        // Keep state.currentUser as local operator!
        updateAuthUI();
      }
    } else {
      state.authStatus = 'local';
      updateAuthUI();
    }
  }

  function renderAuthInitializingState() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:calc(100vh - 120px);min-height:400px;text-align:center;padding:40px;">
        <div class="spin" style="width:48px;height:48px;border:4px solid #D6E2EF;border-top-color:#1E5AA8;border-radius:50%;margin-bottom:20px;"></div>
        <div style="font-size:20px;font-weight:800;color:#0B2545;letter-spacing:-0.3px;margin-bottom:8px;">THERMOSAFE AI</div>
        <div style="font-size:13px;color:#4A5568;font-weight:600;margin-bottom:6px;">Industrial Thermal Intelligence Platform</div>
        <div style="font-size:12px;color:#7A8699;">Initializing secure session & satellite telemetry...</div>
      </div>
    `;
  }

  /* ========== ATTACH LISTENERS ========== */
  document.querySelectorAll('.sidebar .nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = btn.getAttribute('data-page');
      if (page) navigateTo(page);
    });
  });

  document.querySelectorAll('.mobile-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = btn.getAttribute('data-page');
      if (page) navigateTo(page);
    });
  });

  document.getElementById('notifBtn')?.addEventListener('click', openDrawer);
  document.getElementById('drawerBackdrop')?.addEventListener('click', closeDrawer);

  document.getElementById('bottomSheet')?.addEventListener('click', (e) => {
    if (e.target.id === 'bottomSheet') closeBottomSheet();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeDrawer();
      closeAuthModal();
      closeTeamModal();
      closeAnalysisModal();
      closeAckModal();
    }
  });

  document.getElementById('globalSearch')?.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) return;
    const match = currentEvents.find(ev =>
      ev.id.toLowerCase().includes(q) ||
      (ev.city && ev.city.toLowerCase().includes(q)) ||
      (ev.state && ev.state.toLowerCase().includes(q)) ||
      (ev.facility && ev.facility.toLowerCase().includes(q)) ||
      (ev.classification && ev.classification.toLowerCase().includes(q))
    );
    if (match) {
      selectEvent(match.id);
    }
  });

  /* ========== GLOBAL EXPORT ========== */
  window.__thermosafe = {
    selectEvent,
    viewFullAnalysis,
    openAnalysisModal,
    closeAnalysisModal,
    viewAlertOnMap,
    showAckDetails,
    openAcknowledgementModal,
    closeAckModal,
    openBottomSheet,
    closeBottomSheet,
    simulate,
    simulateCritical,
    acknowledge,
    navigateTo,
    openDrawer,
    closeDrawer,
    markRead,
    markAllRead,
    clearNotifications,
    requestNotifPermission,
    registerCurrentDevice,
    sendTestPushNotification,
    openTeamModal,
    closeTeamModal,
    handleTeamSubmit,
    toggleTeamActive,
    deleteTeam,
    renderLoginPage,
    toggleHeatmap,
    createAlertFromEvent,
    trackEvent,
    previewReport,
    downloadReport,
    generateBackendReport,
    shareReport,
    openAuthModal,
    closeAuthModal,
    handleAuthSubmit,
    logout,
    updateAuthUI,
    apiClient,
    state,
    setDataSource,
    toggleDataSource,
    getDataSource,
    selectDataSource: setDataSource,
    LIVE_DATA,
    DEMO_DATA,
    fetchLiveData,
    stopLivePolling,
    startLivePolling,
    manualRefreshFirms,
    updateDashboardLiveView,
    updateDebugDiagnostics,
    renderAuthInitializingState,
    renderOperatorTeamsPage,
    openEditProfileModal,
    handleProfileSave,
    initializeLocalUser,
    renderApplicationShell,
    initializeNavigation,
    initializeMap,
    initializeDataSource,
    startPolling,
    configureApiGateway: function() {
      const current = localStorage.getItem('thermosafe_api_url') || API_BASE_URL;
      const input = window.prompt("Enter your ThermoSafe AI Backend API Gateway URL (e.g. https://your-service.onrender.com):\nLeave empty to reset to default origin.", current);
      if (input !== null) {
        const trimmed = input.trim();
        if (trimmed) {
          localStorage.setItem('thermosafe_api_url', trimmed.replace(/\/+$/, ''));
        } else {
          localStorage.removeItem('thermosafe_api_url');
        }
        window.location.reload();
      }
    }
  };

  /* ========== BOOT SEQUENCE (PHASE 28 STABILIZED) ========== */
  let booted = false;

  function initializeLocalUser() {
    state.currentUser = getStoredLocalOperator();
    state.authStatus = localStorage.getItem('thermo_jwt_token') ? 'authenticated' : 'local';
    updateAuthUI();
  }

  function renderApplicationShell() {
    renderDrawer();
    updateNotifBadge();
    renderDashboard();
  }

  function initializeNavigation() {
    state.currentPage = 'dashboard';
    document.querySelectorAll('.sidebar .nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-page') === 'dashboard');
    });
    document.querySelectorAll('.mobile-nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-page') === 'dashboard');
    });
  }

  function initializeMap() {
    const mapEl = document.getElementById('map');
    if (mapEl && !state.map) {
      initMap();
    }
  }

  function initializeDataSource() {
    state.dataSource = 'live';
    state.dataState = 'CONNECTING';
    state.firmsState = 'INITIALIZING';
    currentEvents = LIVE_DATA.events;
    currentFacilities = LIVE_DATA.facilities.length > 0 ? LIVE_DATA.facilities : DEMO_DATA.facilities;
    state.notifications = LIVE_DATA.notifications.length > 0 ? LIVE_DATA.notifications : DEMO_DATA.notifications;
    updateDataSourceUI();
    if (state.currentPage === 'dashboard') {
      updateDashboardLiveView();
    }
  }

  function startPolling() {
    if (state.dataSource === 'live') {
      startLivePolling();
      fetchLiveData(true).catch(() => {
        activateFirmsUnavailable('FastAPI backend connection error');
      });
    }
  }

  function initBackgroundServices() {
    if ('Notification' in window) {
      state.browserNotifPermission = Notification.permission;
    }
    setTimeout(() => {
      initBackendSync().catch(() => {});
      registerCurrentDevice().catch(() => {});
    }, 150);
  }

  async function boot() {
    if (booted) return;
    booted = true;

    initializeLocalUser();
    renderApplicationShell();
    initializeNavigation();
    initializeMap();
    initializeDataSource();
    startPolling();
    initBackgroundServices();
    updateDebugDiagnostics();

    // Check URL parameters for direct incident view (Phase 34 & Phase 39)
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const targetEventId = urlParams.get('event') || urlParams.get('eventId');
      if (targetEventId) {
        setTimeout(() => {
          viewAlertOnMap(targetEventId);
        }, 500);
      }
    } catch (_) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

})();

