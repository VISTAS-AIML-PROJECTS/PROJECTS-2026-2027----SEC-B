import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle, 
  Mail, 
  Volume2, 
  Send, 
  Filter, 
  RefreshCw,
  BellRing,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import { soundAlert } from '../services/soundAlert';

export default function AlertsCenter({ onAlertAcknowledged }) {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [testPlate, setTestPlate] = useState('TN38AB1234');
  const [testType, setTestType] = useState('OVERSPEED');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [testMessage, setTestMessage] = useState(null);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.getAlerts({ page, limit: 15, severity: severityFilter });
      setAlerts(res.alerts || []);
      setTotal(res.total || 0);
    } catch (e) {
      console.error('Failed to fetch alerts:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 3000);
    return () => clearInterval(interval);
  }, [page, severityFilter]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts(alerts.map(a => a.id === alertId ? { ...a, acknowledged: true } : a));
      if (onAlertAcknowledged) onAlertAcknowledged();
    } catch (e) {
      alert('Error acknowledging alert: ' + e.message);
    }
  };

  const handleTestEmail = async (e) => {
    e.preventDefault();
    setSendingEmail(true);
    setTestMessage(null);
    try {
      const res = await api.testEmailAlert({
        license_plate: testPlate,
        alert_type: testType,
        severity: testType === 'BLOCKLIST_MATCH' ? 'CRITICAL' : 'HIGH'
      });
      setTestMessage({ type: 'success', text: `Test alert dispatched to authorized security email.` });
      soundAlert.playSiren(2.0);
      fetchAlerts();
    } catch (err) {
      setTestMessage({ type: 'error', text: err.message });
    } finally {
      setSendingEmail(false);
    }
  };

  const unackCount = alerts.filter(a => !a.acknowledged).length;

  return (
    <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Top Banner & Quick Trigger */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '16px' }}>
        
        {/* Left Status Hero */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '8px',
                background: unackCount > 0 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                border: `1px solid ${unackCount > 0 ? '#ef4444' : '#10b981'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <ShieldAlert size={24} color={unackCount > 0 ? '#ef4444' : '#10b981'} />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>
                  ALERT MANAGER & AUTHORIZED PERSON DISPATCHER
                </h2>
                <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
                  Real-time multi-channel incident broadcasting: 🔊 Audio Siren, 📧 SMTP Email, 🖥️ Dashboard HUD.
                </p>
              </div>
            </div>
            
            <button 
              onClick={() => soundAlert.playSiren(2.5)}
              className="btn-cyber-outline"
              style={{ fontSize: '0.8rem' }}
            >
              <Volume2 size={15} color="#00f2fe" /> Test Siren Audio
            </button>
          </div>

          <div style={{ display: 'flex', gap: '16px', marginTop: '6px' }}>
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              padding: '10px 16px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.15)',
              flex: 1
            }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>UNACKNOWLEDGED ALERTS</div>
              <div className="font-mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: unackCount > 0 ? '#ef4444' : '#10b981' }}>
                {unackCount}
              </div>
            </div>

            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              padding: '10px 16px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.15)',
              flex: 1
            }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>TOTAL LOGGED ALERTS</div>
              <div className="font-mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                {total}
              </div>
            </div>
          </div>
        </div>

        {/* Right: Manual Security Test Dispatcher */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 10px', fontSize: '0.92rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mail size={16} color="#00f2fe" /> EMAIL NOTIFICATION TESTER
          </h3>
          <p style={{ margin: '0 0 12px', fontSize: '0.75rem', color: '#94a3b8' }}>
            Simulate a security alert email dispatch to authorized personnel.
          </p>

          <form onSubmit={handleTestEmail} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={testPlate}
                onChange={(e) => setTestPlate(e.target.value.toUpperCase())}
                placeholder="Target Plate (e.g. TN38AB1234)"
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  padding: '7px 10px',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.8rem',
                  flex: 1,
                  fontFamily: 'JetBrains Mono, monospace'
                }}
              />
              <select
                value={testType}
                onChange={(e) => setTestType(e.target.value)}
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  padding: '7px 10px',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.8rem'
                }}
              >
                <option value="OVERSPEED">Overspeed</option>
                <option value="BLOCKLIST_MATCH">Blocklist Hit</option>
                <option value="HAZMAT_RESTRICTION">Hazmat Alert</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={sendingEmail}
              className="btn-cyber-primary"
              style={{ justifyContent: 'center', fontSize: '0.82rem', padding: '8px' }}
            >
              <Send size={14} /> {sendingEmail ? 'Dispatching...' : 'Dispatch Test Alert'}
            </button>

            {testMessage && (
              <div style={{
                fontSize: '0.75rem',
                color: testMessage.type === 'success' ? '#34d399' : '#f87171',
                marginTop: '4px'
              }}>
                {testMessage.text}
              </div>
            )}
          </form>
        </div>

      </div>

      {/* Filter Bar */}
      <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="#00f2fe" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Filter by Severity:</span>
          {['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => { setSeverityFilter(sev); setPage(1); }}
              className={severityFilter === sev ? 'btn-cyber-primary' : 'btn-cyber-outline'}
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
            >
              {sev || 'ALL SEVERITIES'}
            </button>
          ))}
        </div>

        <button onClick={fetchAlerts} className="btn-cyber-outline" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Alerts Feed Table */}
      <div className="glass-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'left', color: '#94a3b8' }}>
              <th style={{ padding: '10px 12px' }}>TIMESTAMP</th>
              <th style={{ padding: '10px 12px' }}>SEVERITY</th>
              <th style={{ padding: '10px 12px' }}>ALERT TYPE</th>
              <th style={{ padding: '10px 12px' }}>TRACK / PLATE</th>
              <th style={{ padding: '10px 12px' }}>RECORDED SPEED</th>
              <th style={{ padding: '10px 12px' }}>INCIDENT DETAILS</th>
              <th style={{ padding: '10px 12px' }}>DISPATCH STATUS</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
                  No security alerts found matching filter criteria.
                </td>
              </tr>
            ) : (
              alerts.map((a) => {
                const isCrit = a.severity === 'CRITICAL';
                const isHigh = a.severity === 'HIGH';

                return (
                  <tr
                    key={a.id}
                    style={{
                      borderBottom: '1px solid rgba(30, 41, 59, 0.6)',
                      backgroundColor: !a.acknowledged ? (isCrit ? 'rgba(239, 68, 68, 0.08)' : 'rgba(245, 158, 11, 0.05)') : 'transparent'
                    }}
                  >
                    <td style={{ padding: '10px 12px', color: '#cbd5e1', whiteSpace: 'nowrap' }} className="font-mono">
                      {a.timestamp ? a.timestamp.replace('T', ' ').substring(0, 19) : '-'}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`badge ${isCrit ? 'badge-danger' : isHigh ? 'badge-warning' : 'badge-info'}`}>
                        {a.severity}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: isCrit ? '#f87171' : '#f8fafc' }}>
                      {a.alert_type}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {a.track_id && <span className="badge badge-info font-mono">{a.track_id}</span>}
                        {a.license_plate && (
                          <div className="license-plate-chip" style={{ fontSize: '0.72rem', padding: '1px 5px' }}>
                            <span className="ind-badge" style={{ fontSize: '0.5rem' }}>IND</span>
                            <span>{a.license_plate}</span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px' }} className="font-mono">
                      {a.speed ? `${a.speed} km/h` : '-'}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#cbd5e1', maxWidth: '320px' }}>
                      {a.message}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <span title="Audio Siren Dispatched" style={{ color: a.sound_played ? '#34d399' : '#64748b' }}>
                          🔊
                        </span>
                        <span title="Email Dispatched" style={{ color: a.email_sent ? '#34d399' : '#64748b' }}>
                          📧
                        </span>
                        <span title="Dashboard Banner Active" style={{ color: '#00f2fe' }}>
                          🖥️
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      {a.acknowledged ? (
                        <span style={{ color: '#34d399', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle size={14} /> Resolved
                        </span>
                      ) : (
                        <button
                          onClick={() => handleAcknowledge(a.id)}
                          className="btn-cyber-primary"
                          style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                        >
                          Acknowledge
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}
