import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Gauge, 
  Volume2, 
  Mail, 
  Save, 
  Camera, 
  CheckCircle2, 
  RefreshCw,
  Sliders
} from 'lucide-react';
import { api } from '../services/api';
import { soundAlert } from '../services/soundAlert';

export default function SystemSettings() {
  const [config, setConfig] = useState({
    speed_limit: 60.0,
    sound_alert_enabled: true,
    email_alert_enabled: true,
    alert_recipient_email: 'security.director@portlogistics.com',
    homography_calibration: 18.5,
    camera_source: 'SIMULATED'
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await api.getConfig();
        setConfig(data);
      } catch (err) {
        console.error('Failed to load system config:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg(null);
    try {
      await api.updateConfig(config);
      setStatusMsg({ type: 'success', text: 'System configuration and AI calibration synchronized successfully!' });
      soundAlert.playWarningBeep();
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Failed to update settings: ' + err.message });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading settings...</div>;
  }

  return (
    <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '900px', margin: '0 auto' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sliders size={24} color="#030712" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>
              SURVEILLANCE CALIBRATION & SYSTEM SETTINGS
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
              Configure AI detection thresholds, radar speed limits, sound alarms, and SMTP alert dispatchers.
            </p>
          </div>
        </div>

        {statusMsg && (
          <div style={{
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '0.78rem',
            background: statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            color: statusMsg.type === 'success' ? '#34d399' : '#f87171',
            border: `1px solid ${statusMsg.type === 'success' ? '#10b981' : '#ef4444'}`
          }}>
            {statusMsg.text}
          </div>
        )}
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Section 1: Radar Speed & Homography Calibration */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 14px', fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Gauge size={18} color="#00f2fe" /> SPEED DETECTION & RADAR CALIBRATION
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Speed Limit Slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600 }}>
                  MAX SPEED LIMIT THRESHOLD
                </label>
                <span className="font-mono" style={{ color: '#00f2fe', fontWeight: 700, fontSize: '0.9rem' }}>
                  {config.speed_limit} km/h
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="120"
                step="5"
                value={config.speed_limit}
                onChange={(e) => setConfig({ ...config, speed_limit: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#00f2fe', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginTop: '2px' }}>
                <span>30 km/h (Slow Yard)</span>
                <span>60 km/h (Highway)</span>
                <span>120 km/h (Expressway)</span>
              </div>
            </div>

            {/* Homography Pixels per Meter */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
                CAMERA CALIBRATION (PIXELS PER METER)
              </label>
              <input
                type="number"
                step="0.5"
                value={config.homography_calibration}
                onChange={(e) => setConfig({ ...config, homography_calibration: parseFloat(e.target.value) })}
                style={{
                  width: '100%',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.85rem'
                }}
              />
              <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '4px' }}>
                Standard Highway Focal Length Calibration (Default: 18.5 px/m)
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Alert Dispatch & Audio Siren */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 14px', fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Volume2 size={18} color="#f59e0b" /> SOUND & AUDIO SIREN SETTINGS
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#f8fafc' }}>
                Synthesized High-Pitch Audio Siren
              </div>
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8' }}>
                Triggers acoustic alarm pulses in browser when critical blocklist or overspeed incidents occur.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                type="button"
                onClick={() => soundAlert.playSiren(2.0)}
                className="btn-cyber-outline"
                style={{ fontSize: '0.75rem', padding: '6px 12px' }}
              >
                Test Sound
              </button>

              <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px' }}>
                <input
                  type="checkbox"
                  checked={config.sound_alert_enabled}
                  onChange={(e) => setConfig({ ...config, sound_alert_enabled: e.target.checked })}
                  style={{ opacity: 0, width: 0, height: 0 }}
                />
                <span style={{
                  position: 'absolute',
                  cursor: 'pointer',
                  top: 0, left: 0, right: 0, bottom: 0,
                  backgroundColor: config.sound_alert_enabled ? '#10b981' : '#334155',
                  borderRadius: '24px',
                  transition: '0.3s'
                }}>
                  <span style={{
                    position: 'absolute',
                    content: '',
                    height: '18px',
                    width: '18px',
                    left: config.sound_alert_enabled ? '23px' : '3px',
                    bottom: '3px',
                    backgroundColor: 'white',
                    borderRadius: '50%',
                    transition: '0.3s'
                  }} />
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Section 3: Email Notification & Authorized Person Dispatch */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 14px', fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mail size={18} color="#ef4444" /> AUTHORIZED PERSONNEL EMAIL DISPATCH
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
                SECURITY DIRECTOR / OFFICER EMAIL RECIPIENT
              </label>
              <input
                type="email"
                required
                value={config.alert_recipient_email}
                onChange={(e) => setConfig({ ...config, alert_recipient_email: e.target.value })}
                placeholder="e.g. security.director@portlogistics.com"
                style={{
                  width: '100%',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.85rem'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '8px' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#f8fafc' }}>
                  Enable Automated Incident Email Dispatch
                </div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Sends detailed incident dossiers with speed and plate metadata.
                </div>
              </div>

              <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px' }}>
                <input
                  type="checkbox"
                  checked={config.email_alert_enabled}
                  onChange={(e) => setConfig({ ...config, email_alert_enabled: e.target.checked })}
                  style={{ opacity: 0, width: 0, height: 0 }}
                />
                <span style={{
                  position: 'absolute',
                  cursor: 'pointer',
                  top: 0, left: 0, right: 0, bottom: 0,
                  backgroundColor: config.email_alert_enabled ? '#10b981' : '#334155',
                  borderRadius: '24px',
                  transition: '0.3s'
                }}>
                  <span style={{
                    position: 'absolute',
                    content: '',
                    height: '18px',
                    width: '18px',
                    left: config.email_alert_enabled ? '23px' : '3px',
                    bottom: '3px',
                    backgroundColor: 'white',
                    borderRadius: '50%',
                    transition: '0.3s'
                  }} />
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Submit Save Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            disabled={saving}
            className="btn-cyber-primary"
            style={{ padding: '10px 24px', fontSize: '0.9rem' }}
          >
            <Save size={16} /> {saving ? 'Synchronizing...' : 'Save Configuration'}
          </button>
        </div>

      </form>

    </div>
  );
}
