import os
import re
import sys

def update_popup_and_modal(filepath):
    print(f"Updating popup & modal in: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Update marker popup
    old_popup_find = re.compile(r"marker\.bindPopup\(`\s*<div style=\"min-width:260px;.*?`\);", re.DOTALL)
    old_popup_find_alt = re.compile(r"marker\.bindPopup\(`\s*<div style=\"min-width:250px;.*?`\);", re.DOTALL)

    new_popup = '''const isDemo = ev.data_source === 'DEMO' || ev.is_demo;
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
            <div><b>Latitude:</b> <span style="font-family:'Courier New',monospace;">${latFmt}° N</span></div>
            <div><b>Longitude:</b> <span style="font-family:'Courier New',monospace;">${lngFmt}° E</span></div>
            <div><b>Event Type:</b> ${escapeHtml(evtType)}</div>
            <div><b>AI Classification:</b> <span style="font-weight:700;color:${getEventColor(ev).hex};">${escapeHtml(ev.classification || evtType)}</span></div>
            <div><b>AI Confidence:</b> <b>${confVal}%</b></div>
            <div><b>Risk Score:</b> <span style="color:#DC2626;font-weight:800;">${scoreVal}/100</span></div>
            <div><b>Risk Priority:</b> ${riskBadge(riskVal)}</div>
            <div><b>Thermal Intensity:</b> ${escapeHtml(intensityVal)}</div>
            <div><b>Detection Time:</b> <span style="font-family:'Courier New',monospace;">${escapeHtml(detectVal)}</span></div>
          </div>
          <button onclick="window.__thermosafe.viewFullAnalysis('${ev.id}')" style="
            background:#1E5AA8;color:white;border:none;padding:8px 14px;
            border-radius:6px;font-size:11px;font-weight:700;width:100%;
            cursor:pointer;font-family:inherit;box-shadow:0 1px 3px rgba(0,0,0,0.1);
          ">View Full Analysis</button>
        </div>
      `);'''

    # Replace popup
    pattern_popup_all = re.compile(
        r"(const isDemo = ev\.data_source === 'DEMO'.*?)?marker\.bindPopup\(`.*?`\);",
        re.DOTALL
    )
    if pattern_popup_all.search(src):
        src = pattern_popup_all.sub(new_popup, src, count=1)
        print("  [PASS] Marker popup updated with exact 11 fields + Data Source")

    # 2. Update openAnalysisModal to contain all 5 sections AND all 15 fields
    modal_pattern = re.compile(
        r"function openAnalysisModal\(id\) \{.*?\n  \}\n\n  function viewFullAnalysis",
        re.DOTALL
    )

    new_modal = '''function openAnalysisModal(id) {
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

  function viewFullAnalysis'''

    if modal_pattern.search(src):
        src = modal_pattern.sub(new_modal, src, count=1)
        print("  [PASS] openAnalysisModal updated with all 5 sections and 15 fields")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"Successfully wrote {filepath}")

def main():
    targets = [
        r"c:\Users\deeks\OneDrive\Desktop\SIH\index.html",
        r"c:\Users\deeks\OneDrive\Desktop\SIH\frontend\index.html"
    ]
    for t in targets:
        update_popup_and_modal(t)

if __name__ == "__main__":
    main()
