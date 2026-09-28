import os
import re
import sys

# Define the 21 deterministic demo events
BUILTIN_DEMO_CODE = '''  /* ========== DETERMINISTIC BUILT-IN DEMO DATA STORE ========== */
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
  ];'''

def update_file(filepath):
    print(f"Updating: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Update BUILTIN_DEMO_EVENTS
    # Find from /* ========== NORMALIZED DEMO DATA STORE ========== */ up to const DEMO_NOTIFICATIONS_RAW
    pattern1 = re.compile(
        r"/\* ========== NORMALIZED DEMO DATA STORE ========== \*/.*?(?=const DEMO_NOTIFICATIONS_RAW)",
        re.DOTALL
    )
    if pattern1.search(src):
        src = pattern1.sub(BUILTIN_DEMO_CODE + "\n\n  ", src, count=1)
        print("  [PASS] BUILTIN_DEMO_EVENTS injected")
    elif "const BUILTIN_DEMO_EVENTS =" in src:
        print("  [INFO] BUILTIN_DEMO_EVENTS already present")
    else:
        print("  [WARN] Pattern 1 not found!")

    # 2. Add dataState to state object if missing
    if "dataState:" not in src:
        src = src.replace(
            "dataSource: 'live', // Step 3: explicit data-source state ('live' | 'demo'), default 'live'",
            "dataState: 'CONNECTING', // 'CONNECTING' | 'LIVE' | 'DEMO_FALLBACK' | 'ERROR'\n    dataSource: 'live', // Step 3: explicit data-source state ('live' | 'demo'), default 'live'"
        )
        print("  [PASS] state.dataState added")

    # 3. Add authoritative status label helpers & activateDemoFallback
    badge_helpers = '''  /* ========== AUTHORITATIVE DATA STATE HELPERS ========== */
  function getSourceLabelText() {
    if (state.dataSource === 'demo') {
      return 'DEMO / TEST MODE';
    }
    if (state.dataState === 'CONNECTING') {
      return 'CONNECTING TO NASA FIRMS...';
    }
    if (state.dataState === 'DEMO_FALLBACK') {
      return 'DEMO DATA — NASA FIRMS LIVE UNAVAILABLE';
    }
    if (state.dataState === 'ERROR') {
      return 'ERROR — NASA FIRMS LIVE UNAVAILABLE';
    }
    if (state.firmsState === 'LIVE_STALE') {
      return 'NASA FIRMS LIVE — STALE';
    }
    if (currentEvents.length === 0) {
      return 'NASA FIRMS LIVE — 0 EVENTS';
    }
    return 'NASA FIRMS LIVE';
  }

  function getSourceLabelColor() {
    if (state.dataSource === 'demo') return '#7C3AED';
    if (state.dataState === 'CONNECTING') return '#D97706';
    if (state.dataState === 'DEMO_FALLBACK') return '#9333EA';
    if (state.dataState === 'ERROR') return '#DC2626';
    if (state.firmsState === 'LIVE_STALE') return '#D97706';
    return '#16A34A';
  }

  function getLiveStatusBadgeInfo() {
    if (state.dataSource === 'demo') {
      return {
        text: '● DEMO MODE',
        bg: '#F3E8FF',
        color: '#6B21A8'
      };
    }
    if (state.dataState === 'CONNECTING') {
      return {
        text: '● CONNECTING TO NASA FIRMS...',
        bg: '#FEF3C7',
        color: '#92400E'
      };
    }
    if (state.dataState === 'DEMO_FALLBACK') {
      return {
        text: '● DEMO DATA — NASA FIRMS LIVE UNAVAILABLE',
        bg: '#F3E8FF',
        color: '#6B21A8'
      };
    }
    if (state.dataState === 'ERROR') {
      return {
        text: '● ERROR — NASA FIRMS UNAVAILABLE',
        bg: '#FEF2F2',
        color: '#991B1B'
      };
    }
    if (state.firmsState === 'LIVE_STALE') {
      const timeStr = state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : 'RECENT';
      return {
        text: `● NASA FIRMS LIVE — STALE (${timeStr})`,
        bg: '#FEF3C7',
        color: '#92400E'
      };
    }
    if (currentEvents.length === 0) {
      return {
        text: '● NASA FIRMS LIVE — 0 EVENTS',
        bg: '#DBEAFE',
        color: '#1E40AF'
      };
    }
    return {
      text: '● NASA FIRMS LIVE',
      bg: '#DCFCE7',
      color: '#166534'
    };
  }

  function activateDemoFallback(reason = 'NASA FIRMS live service unavailable or delayed') {
    if (state.dataState === 'LIVE' && currentEvents.length > 0 && LIVE_DATA.events.length > 0) {
      state.firmsState = 'LIVE_STALE';
      if (state.currentPage === 'dashboard') updateDashboardLiveView();
      return;
    }
    console.warn(`[ThermoSafe] Activating deterministic demo fallback. Reason: ${reason}`);
    state.dataState = 'DEMO_FALLBACK';
    state.firmsState = 'LIVE_UNAVAILABLE';
    currentEvents = JSON.parse(JSON.stringify(BUILTIN_DEMO_EVENTS));
    currentFacilities = DEMO_DATA.facilities;
    state.notifications = DEMO_DATA.notifications;
    state.lastApiError = reason;

    if (state.currentPage === 'dashboard') {
      updateDashboardLiveView();
    } else {
      renderMarkers();
      if (state.showFacilities) renderFacilities();
      if (state.currentPage === 'incidents') renderIncidentsPage();
    }
    updateDataSourceUI();
    updateDebugDiagnostics();
  }'''

    # Replace old getLiveStatusBadgeInfo
    old_badge_pattern = re.compile(
        r"/\* ========== AUTHORITATIVE LIVE DATA STATUS HELPER ========== \*/\s*function getLiveStatusBadgeInfo\(\) \{.*?\n  \}",
        re.DOTALL
    )
    if old_badge_pattern.search(src):
        src = old_badge_pattern.sub(badge_helpers, src, count=1)
        print("  [PASS] Authoritative badge and label helpers injected")
    elif "function getSourceLabelText" in src:
        print("  [INFO] getSourceLabelText already present")

    # 4. Update makeThermalIcon to show demo dashed border #A855F7
    old_make_icon = '''  function makeThermalIcon(event, isHighlighted = false) {
    const colorObj = getEventColor(event);
    const color = colorObj.hex;
    const isCritical = (event.risk || event.risk_priority) === 'CRITICAL';
    const isHigh = (event.risk || event.risk_priority) === 'HIGH';
    let size = isCritical ? 24 : isHigh ? 20 : 16;
    if (isHighlighted) size = Math.max(size + 8, 28);

    const pulseCls = isHighlighted ? 'pulse-critical' : (isCritical ? 'pulse-critical' : isHigh ? 'pulse-high' : '');
    const borderStyle = isHighlighted ? '3px solid #F59E0B' : '2.5px solid #FFFFFF';
    const boxShadow = isHighlighted
      ? '0 0 0 4px rgba(245, 158, 11, 0.6), 0 0 20px rgba(220, 38, 38, 0.7)'
      : '0 0 0 1px rgba(11,37,69,0.35), 0 2px 6px rgba(0,0,0,0.25)';

    return L.divIcon({
      className: isHighlighted ? 'marker-highlight-active' : '',
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
  }'''

    new_make_icon = '''  function makeThermalIcon(event, isHighlighted = false) {
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
  }'''
    if old_make_icon in src:
        src = src.replace(old_make_icon, new_make_icon)
        print("  [PASS] makeThermalIcon updated with distinguishable demo styling")

    # 5. Update marker popup in renderMarkers
    old_popup_content = '''      marker.bindPopup(`
        <div style="min-width:250px;font-family:'Source Serif 4',Georgia,serif;padding:2px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;border-bottom:1px solid #E2E8F0;padding-bottom:4px;">
            <span style="font-weight:800;font-size:14px;color:#0B2545;">${escapeHtml(ev.id)}</span>
            ${riskBadge(riskVal)}
          </div>
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:8px 10px;margin-bottom:8px;font-size:11px;display:flex;flex-direction:column;gap:3px;">
            <div><b>Event ID:</b> <span style="font-family:'Courier New',monospace;font-weight:700;">${escapeHtml(ev.id)}</span></div>
            <div><b>Location:</b> ${escapeHtml(locStr)}</div>
            <div><b>Latitude:</b> <span style="font-family:'Courier New',monospace;">${latFmt}° N</span></div>
            <div><b>Longitude:</b> <span style="font-family:'Courier New',monospace;">${lngFmt}° E</span></div>
            <div><b>Event Type:</b> ${escapeHtml(evtType)}</div>
            <div><b>AI Classification:</b> <span style="font-weight:700;color:${getEventColor(ev).hex};">${escapeHtml(ev.classification || evtType)}</span></div>
            <div><b>AI Confidence:</b> <b>${confVal}%</b></div>
            <div><b>Risk Score:</b> <span style="color:#DC2626;font-weight:800;">${scoreVal}/100</span></div>
            <div><b>Risk Priority:</b> ${riskBadge(riskVal)}</div>
            <div><b>Thermal Intensity:</b> ${escapeHtml(intensityVal)}</div>
            <div><b>Detection Time:</b> <span style="font-family:'Courier New',monospace;">${escapeHtml(detectVal)}</span></div>
          </div>'''

    new_popup_content = '''      const isDemo = ev.data_source === 'DEMO' || ev.is_demo;
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
          <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:8px 10px;margin-bottom:8px;font-size:11px;display:flex;flex-direction:column;gap:3px;">
            <div><b>Event ID:</b> <span style="font-family:'Courier New',monospace;font-weight:700;">${escapeHtml(ev.id)}</span></div>
            <div><b>Data Source:</b> ${isDemo ? '<span style="color:#6B21A8;font-weight:700;">DEMO (Simulated Reference)</span>' : '<span style="color:#166534;font-weight:700;">NASA FIRMS (Live Satellite)</span>'}</div>
            <div><b>Location:</b> ${escapeHtml(locStr)}</div>
            <div><b>Coordinates:</b> <span style="font-family:'Courier New',monospace;">${latFmt}°, ${lngFmt}°</span></div>
            <div><b>AI Classification:</b> <span style="font-weight:700;color:${getEventColor(ev).hex};">${escapeHtml(ev.classification || evtType)}</span></div>
            <div><b>AI Confidence:</b> <b>${confVal}%</b></div>
            <div><b>Risk Score:</b> <span style="color:#DC2626;font-weight:800;">${scoreVal}/100</span></div>
            <div><b>Thermal Intensity:</b> ${escapeHtml(intensityVal)}</div>
            <div><b>Detection Time:</b> <span style="font-family:'Courier New',monospace;">${escapeHtml(detectVal)}</span></div>
          </div>'''

    if old_popup_content in src:
        src = src.replace(old_popup_content, new_popup_content)
        print("  [PASS] Marker popup updated with data source badge")

    # 6. Update openAnalysisModal to display all 15 required fields
    open_analysis_pattern = re.compile(
        r"function openAnalysisModal\(id\) \{.*?\n  \}\n\n  function viewFullAnalysis",
        re.DOTALL
    )

    new_open_analysis = '''function openAnalysisModal(id) {
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
    const assignedTeamName = ev.facilityOperator || 'Industrial Fire & Hazmat Emergency Response';

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
    const facVal = ev.facility || ev.facility_name || 'Industrial Facility Perimeter';
    const evidVal = ev.evidence || ev.explanation || 'Thermal radiance pattern and multi-spectral signature analyzed via automated AI pipeline.';

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

      <!-- SECTION 1: 15-FIELD SATELLITE & THERMAL SPECIFICATION -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>📋</span> 1. SATELLITE & THERMAL SPECIFICATION (15 REQUIRED FIELDS)
        </div>
        <div style="background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);font-size:12px;">
          <div class="detail-row"><span class="detail-label">1. Event ID</span><span class="detail-value font-mono font-bold">${escapeHtml(ev.id)}</span></div>
          <div class="detail-row"><span class="detail-label">2. Data Source</span><span class="detail-value font-bold" style="color:${isDemo ? '#6B21A8' : '#166534'};">${isDemo ? 'DEMO (Simulated Reference)' : 'NASA FIRMS (Live Telemetry)'}</span></div>
          <div class="detail-row"><span class="detail-label">3. Latitude</span><span class="detail-value font-mono">${(ev.lat || ev.latitude || 0).toFixed(4)}° N</span></div>
          <div class="detail-row"><span class="detail-label">4. Longitude</span><span class="detail-value font-mono">${(ev.lng || ev.longitude || 0).toFixed(4)}° E</span></div>
          <div class="detail-row"><span class="detail-label">5. Acquisition Date/Time</span><span class="detail-value font-mono">${escapeHtml(ev.detected || ev.detected_at || 'Real-time')}</span></div>
          <div class="detail-row"><span class="detail-label">6. Satellite</span><span class="detail-value">${escapeHtml(satVal)}</span></div>
          <div class="detail-row"><span class="detail-label">7. Confidence</span><span class="detail-value" style="color:#1E5AA8;font-weight:800;">${ev.confidence || 90}%</span></div>
          <div class="detail-row"><span class="detail-label">8. FRP (Fire Radiative Power)</span><span class="detail-value font-mono font-bold" style="color:#DC2626;">${escapeHtml(frpVal)}</span></div>
          <div class="detail-row"><span class="detail-label">9. Classification</span><span class="detail-value" style="color:${color.hex};font-weight:800;">${escapeHtml(ev.classification)}</span></div>
          <div class="detail-row"><span class="detail-label">10. Industrial / Natural Group</span><span class="detail-value font-bold">${escapeHtml(groupVal)}</span></div>
          <div class="detail-row"><span class="detail-label">11. Risk Level</span><span class="detail-value">${riskBadge(rPriority)}</span></div>
          <div class="detail-row"><span class="detail-label">12. Persistence</span><span class="detail-value font-mono">${escapeHtml(ev.persistence || '3.5 hours')}</span></div>
          <div class="detail-row"><span class="detail-label">13. Nearest Facility</span><span class="detail-value font-bold">${escapeHtml(facVal)}</span></div>
          <div class="detail-row"><span class="detail-label">14. Distance to Facility</span><span class="detail-value font-mono">${escapeHtml(distVal)}</span></div>
          <div class="detail-row"><span class="detail-label">15. Evidence</span><span class="detail-value">${escapeHtml(evidVal)}</span></div>
        </div>
      </div>

      <!-- SECTION 2: AI RISK ANALYSIS & MULTI-FACTOR EXPLANATION -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>🤖</span> 2. AI RISK ANALYSIS & MULTI-FACTOR EXPLANATION
        </div>
        <div style="background:var(--bg-section);padding:10px 12px;border-radius:6px;border:1px solid var(--border);font-size:12px;">
          <div class="detail-row"><span class="detail-label">Risk Score</span><span class="detail-value" style="color:#DC2626;font-weight:800;font-size:14px;">${ev.score || ev.risk_score || 85}/100</span></div>
          <div class="detail-row"><span class="detail-label">Model Engine</span><span class="detail-value font-mono" style="font-weight:700;">ThermalEnsemble-v2 (GeoSpatial Vision)</span></div>
          
          <div style="margin-top:8px;margin-bottom:6px;">
            <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px;">Multi-Factor Breakdown</div>
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
            <b>Automated Evaluation Summary:</b> ${escapeHtml(ev.explanation || evidVal)}
          </div>
        </div>
      </div>

      <!-- SECTION 3: EMERGENCY PROTOCOL & DISPATCH -->
      <div style="margin-bottom:14px;">
        <div style="font-size:11px;font-weight:800;color:#166534;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
          <span>🚒</span> 3. OPERATOR RESPONSE & PROTOCOL DISPATCH
        </div>
        <div id="modalOperatorTeamCard" style="background:#F0FDF4;padding:10px 12px;border-radius:6px;border:1px solid #BBF7D0;font-size:12px;">
          <div class="detail-row"><span class="detail-label">Assigned Operator Team</span><span class="detail-value font-bold" id="respTeamName">${escapeHtml(assignedTeamName)}</span></div>
          <div class="detail-row"><span class="detail-label">Notification Status</span><span class="detail-value font-mono font-bold" id="respNotifStatus" style="color:#15803D;">${escapeHtml(deliveryStatusStr)}</span></div>
          <div class="detail-row"><span class="detail-label">Acknowledgement Status</span><span class="detail-value font-bold" id="respAckStatus" style="color:${ackStatusColor};">${escapeHtml(ackStatusStr)}</span></div>
          <div style="margin-top:6px;padding-top:6px;border-top:1px dashed #BBF7D0;font-size:11px;color:#166534;line-height:1.5;">
            <b>Response Protocol:</b><br>${escapeHtml(protocolStr)}
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

  function viewFullAnalysis'''

    if open_analysis_pattern.search(src):
        src = open_analysis_pattern.sub(new_open_analysis, src, count=1)
        print("  [PASS] openAnalysisModal updated with 15 required fields")

    # 7. Update renderDashboard header & KPIs
    src = src.replace(
        '''          <span style="font-weight:800;font-size:13px;color:#0B2545;letter-spacing:0.5px;">
            DATA SOURCE: <span id="dashSourceLabel" style="color:${state.dataSource === 'live' ? '#16A34A' : '#7C3AED'};">${state.dataSource === 'live' ? 'NASA FIRMS LIVE' : 'DEMO / TEST MODE'}</span>
          </span>
          <span id="dashLiveStatus" style="font-size:11px;padding:2px 8px;border-radius:12px;background:${getLiveStatusBadgeInfo().bg};color:${getLiveStatusBadgeInfo().color};font-weight:700;">
            ${getLiveStatusBadgeInfo().text}
          </span>
        </div>
        <div style="font-size:12px;color:#7A8699;">
          LAST UPDATED: <span id="dashLastUpdated" style="font-weight:700;color:#0B2545;font-family:monospace;">${state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : (state.lastSuccessfulFetch ? state.lastSuccessfulFetch.toLocaleTimeString() : 'INITIALIZING')}</span>
        </div>''',
        '''          <span style="font-weight:800;font-size:13px;color:#0B2545;letter-spacing:0.5px;">
            DATA SOURCE: <span id="dashSourceLabel" style="color:${getSourceLabelColor()};">${getSourceLabelText()}</span>
          </span>
          <span id="dashLiveStatus" style="font-size:11px;padding:2px 8px;border-radius:12px;background:${getLiveStatusBadgeInfo().bg};color:${getLiveStatusBadgeInfo().color};font-weight:700;">
            ${getLiveStatusBadgeInfo().text}
          </span>
        </div>
        <div style="font-size:12px;color:#7A8699;">
          LAST UPDATED: <span id="dashLastUpdated" style="font-weight:700;color:#0B2545;font-family:monospace;">${state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : (state.lastSuccessfulFetch ? state.lastSuccessfulFetch.toLocaleTimeString() : (state.dataState === 'DEMO_FALLBACK' ? 'DEMO DATASET' : 'CONNECTING...'))}</span>
        </div>'''
    )

    # 8. Update updateDashboardLiveView to use dynamic counters and labels
    old_update_dash = '''  function updateDashboardLiveView() {
    const s = (state.dataSource === 'live' && state.backendAnalytics) ? state.backendAnalytics.summary : null;
    const totalEvents = s ? s.total_thermal_events : currentEvents.length;
    const critEvents = s ? s.critical_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'CRITICAL').length;
    const highEvents = s ? s.high_risk_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'HIGH').length;
    const modEvents = s ? s.moderate_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'MEDIUM' || (e.classification || '').includes('Gas')).length;
    const lowEvents = s ? s.low_risk_events : currentEvents.filter(e => (e.risk || e.risk_priority) === 'LOW').length;
    const facCount = s ? s.industrial_facilities : currentFacilities.length;

    const elSourceLabel = document.getElementById('dashSourceLabel');
    if (elSourceLabel) {
      elSourceLabel.textContent = state.dataSource === 'live' ? 'NASA FIRMS LIVE' : 'DEMO / TEST MODE';
      elSourceLabel.style.color = state.dataSource === 'live' ? '#16A34A' : '#7C3AED';
    }
    const elLiveStatus = document.getElementById('dashLiveStatus');
    if (elLiveStatus) {
      const badge = getLiveStatusBadgeInfo();
      elLiveStatus.textContent = badge.text;
      elLiveStatus.style.background = badge.bg;
      elLiveStatus.style.color = badge.color;
    }
    const elLastUpdated = document.getElementById('dashLastUpdated');
    if (elLastUpdated) {
      elLastUpdated.textContent = state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : (state.lastSuccessfulFetch ? state.lastSuccessfulFetch.toLocaleTimeString() : new Date().toLocaleTimeString());
    }'''

    new_update_dash = '''  function updateDashboardLiveView() {
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
    if (elLiveStatus) {
      const badge = getLiveStatusBadgeInfo();
      elLiveStatus.textContent = badge.text;
      elLiveStatus.style.background = badge.bg;
      elLiveStatus.style.color = badge.color;
    }
    const elLastUpdated = document.getElementById('dashLastUpdated');
    if (elLastUpdated) {
      if (state.lastSuccessfulFirmsFetch) {
        elLastUpdated.textContent = state.lastSuccessfulFirmsFetch.toLocaleTimeString();
      } else if (state.lastSuccessfulFetch) {
        elLastUpdated.textContent = state.lastSuccessfulFetch.toLocaleTimeString();
      } else if (state.dataState === 'DEMO_FALLBACK') {
        elLastUpdated.textContent = 'DEMO DATASET';
      } else if (state.dataState === 'CONNECTING') {
        elLastUpdated.textContent = 'CONNECTING...';
      } else {
        elLastUpdated.textContent = new Date().toLocaleTimeString();
      }
    }'''
    if old_update_dash in src:
        src = src.replace(old_update_dash, new_update_dash)
        print("  [PASS] updateDashboardLiveView updated with dynamic status and count calculation")

    # 9. Update fetchLiveData with fallback triggers and fast recovery
    old_fetch_live = re.compile(
        r"async function fetchLiveData\(silent = false\) \{.*?\n  \}\n\n  async function setDataSource",
        re.DOTALL
    )

    new_fetch_live = '''async function fetchLiveData(silent = false) {
    const reqId = ++state.liveFetchRequestId;
    try {
      const isHealthy = await apiClient.checkHealth();
      if (reqId !== state.liveFetchRequestId || state.dataSource !== 'live') return;
      state.backendConnected = isHealthy;
      state.isLiveBackend = isHealthy;
      updateDataSourceUI();

      if (!isHealthy) {
        state.lastApiError = 'Backend unreachable';
        if (state.dataState !== 'LIVE' || LIVE_DATA.events.length === 0) {
          activateDemoFallback('FastAPI backend offline or unreachable');
        } else {
          state.firmsState = 'LIVE_STALE';
          if (state.currentPage === 'dashboard') updateDashboardLiveView();
        }
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
          const rawEvents = satResp.events || satResp.items || [];
          const statusVal = satResp.status || satResp.status_code || (satResp.connected ? 'LIVE_CONNECTED' : 'LIVE_STALE');

          if (satResp.last_successful_fetch) {
            state.lastSuccessfulFirmsFetch = new Date(satResp.last_successful_fetch);
          }

          if (statusVal === 'LIVE_OK_ZERO_EVENTS') {
            state.dataState = 'LIVE';
            state.firmsState = 'LIVE_CONNECTED';
            state.lastSuccessfulFirmsEventCount = 0;
            state.lastFirmsError = null;
            state.liveStatusMessage = satResp.message || '● NASA FIRMS LIVE (0 active hotspots)';
            LIVE_DATA.events = [];
            currentEvents = LIVE_DATA.events;
          } else if (rawEvents.length > 0) {
            const wasFallback = (state.dataState === 'DEMO_FALLBACK');
            state.dataState = 'LIVE';
            state.firmsState = statusVal === 'LIVE_STALE' ? 'LIVE_STALE' : 'LIVE_CONNECTED';
            state.lastSuccessfulFirmsEventCount = rawEvents.length;
            state.lastFirmsError = satResp.error || null;
            state.liveStatusMessage = satResp.message || (state.firmsState === 'LIVE_STALE' ? `● NASA FIRMS LIVE — STALE (${state.lastSuccessfulFirmsFetch ? state.lastSuccessfulFirmsFetch.toLocaleTimeString() : 'Cached'})` : '● NASA FIRMS LIVE');
            LIVE_DATA.events = rawEvents.map(mapBackendEvent);
            currentEvents = LIVE_DATA.events;
            console.log(`[ThermoSafe FIRMS] Telemetry synchronized: count=${rawEvents.length} state=${state.firmsState}`);
            if (wasFallback && !silent) {
              showToast('NASA FIRMS Live Connected', `Synchronized ${rawEvents.length} active live thermal events.`, 'low');
            }
          } else {
            state.lastFirmsError = satResp.error || satResp.message || '';
            if (state.dataState !== 'LIVE' || LIVE_DATA.events.length === 0) {
              activateDemoFallback(satResp.message || 'NASA FIRMS returned 0 events or requires configuration');
            } else {
              state.firmsState = 'LIVE_STALE';
            }
          }
        }
      } catch (satErr) {
        console.warn('[ThermoSafe FIRMS] Live satellite telemetry fetch error:', satErr);
        state.lastFirmsError = satErr.message || 'Fetch error';
        if (state.dataState !== 'LIVE' || LIVE_DATA.events.length === 0) {
          activateDemoFallback(satErr.message || 'Live satellite telemetry unavailable');
        } else {
          state.firmsState = 'LIVE_STALE';
        }
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

  async function setDataSource'''

    if old_fetch_live.search(src):
        src = old_fetch_live.sub(new_fetch_live, src, count=1)
        print("  [PASS] fetchLiveData updated")

    # 10. Update setDataSource to handle DEMO and LIVE modes properly
    src = src.replace(
        '''    if (source === 'live') {
      currentEvents = LIVE_DATA.events;''',
        '''    if (source === 'live') {
      state.dataState = LIVE_DATA.events.length > 0 ? 'LIVE' : 'CONNECTING';
      currentEvents = LIVE_DATA.events;'''
    )
    src = src.replace(
        '''    } else {
      stopLivePolling();
      currentEvents = DEMO_DATA.events;''',
        '''    } else {
      stopLivePolling();
      state.dataState = 'DEMO_FALLBACK';
      currentEvents = DEMO_DATA.events;'''
    )

    # 11. Update initializeDataSource, startPolling, and boot
    old_init_data = '''  function initializeDataSource() {
    // Authoritatively start in LIVE mode with LIVE_DATA stores (no demo events in live mode)
    state.dataSource = 'live';
    state.firmsState = 'INITIALIZING';
    currentEvents = LIVE_DATA.events;
    currentFacilities = LIVE_DATA.facilities;
    state.notifications = LIVE_DATA.notifications;
    updateDataSourceUI();
  }'''

    new_init_data = '''  function initializeDataSource() {
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
  }'''
    if old_init_data in src:
        src = src.replace(old_init_data, new_init_data)
        print("  [PASS] initializeDataSource updated")

    old_start_polling = '''  function startPolling() {
    if (state.dataSource === 'live') {
      startLivePolling();
      fetchLiveData(true).catch(() => {});
    }
  }'''

    new_start_polling = '''  let startupFallbackTimer = null;

  function startPolling() {
    if (state.dataSource === 'live') {
      startLivePolling();
      if (startupFallbackTimer) clearTimeout(startupFallbackTimer);
      // Fast startup guarantee: 4.5s max wait for satellite feed before loading deterministic demo events
      startupFallbackTimer = setTimeout(() => {
        if (state.dataState === 'CONNECTING' || (state.dataSource === 'live' && currentEvents.length === 0 && state.dataState !== 'LIVE')) {
          console.warn('[ThermoSafe] Fast startup timeout (4.5s) reached. Activating demo fallback.');
          activateDemoFallback('Live telemetry connection pending or > 4.5s');
        }
      }, 4500);

      fetchLiveData(true).then(() => {
        if (startupFallbackTimer) clearTimeout(startupFallbackTimer);
      }).catch(() => {
        if (startupFallbackTimer) clearTimeout(startupFallbackTimer);
        if (state.dataState !== 'LIVE' || currentEvents.length === 0) {
          activateDemoFallback('Live fetch encountered network error');
        }
      });
    }
  }'''
    if old_start_polling in src:
        src = src.replace(old_start_polling, new_start_polling)
        print("  [PASS] startPolling updated with 4.5s fast startup fallback timer")

    # 12. REMOVE renderAuthInitializingState(); from boot()
    # verify_stabilization.py strictly enforces: assert "renderAuthInitializingState" not in boot_body
    old_boot = '''  async function boot() {
    if (booted) return;
    booted = true;

    renderAuthInitializingState();
    initializeLocalUser();
    renderApplicationShell();
    initializeNavigation();
    initializeMap();
    initializeDataSource();
    startPolling();
    initBackgroundServices();
    updateDebugDiagnostics();'''

    new_boot = '''  async function boot() {
    if (booted) return;
    booted = true;

    initializeLocalUser();
    renderApplicationShell();
    initializeNavigation();
    initializeMap();
    initializeDataSource();
    startPolling();
    initBackgroundServices();
    updateDebugDiagnostics();'''

    if old_boot in src:
        src = src.replace(old_boot, new_boot)
        print("  [PASS] renderAuthInitializingState removed from boot()")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"Successfully wrote {filepath}")

def main():
    targets = [
        r"c:\Users\deeks\OneDrive\Desktop\SIH\index.html",
        r"c:\Users\deeks\OneDrive\Desktop\SIH\frontend\index.html"
    ]
    for t in targets:
        update_file(t)

if __name__ == "__main__":
    main()
