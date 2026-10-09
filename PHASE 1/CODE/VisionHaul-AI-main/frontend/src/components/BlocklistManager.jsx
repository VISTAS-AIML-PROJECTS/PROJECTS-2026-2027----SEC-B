import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Plus, 
  Search, 
  Trash2, 
  Power, 
  CheckCircle2, 
  X,
  AlertOctagon,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function BlocklistManager() {
  const [blocklist, setBlocklist] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  
  // New entry form state
  const [newPlate, setNewPlate] = useState('');
  const [newReason, setNewReason] = useState('');
  const [newSeverity, setNewSeverity] = useState('CRITICAL');
  const [newAddedBy, setNewAddedBy] = useState('Security Officer');

  const fetchBlocklist = async () => {
    setLoading(true);
    try {
      const data = await api.getBlocklist(search);
      setBlocklist(data.blocklist || []);
    } catch (e) {
      console.error('Failed to load blocklist:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlocklist();
  }, [search]);

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!newPlate || !newReason) {
      alert('Please provide license plate and reason.');
      return;
    }

    try {
      await api.addBlocklist({
        license_plate: newPlate.toUpperCase().trim(),
        reason: newReason.trim(),
        severity: newSeverity,
        added_by: newAddedBy.trim()
      });
      setIsAddModalOpen(false);
      setNewPlate('');
      setNewReason('');
      fetchBlocklist();
    } catch (err) {
      alert('Failed to add entry: ' + err.message);
    }
  };

  const handleToggleActive = async (entry) => {
    try {
      await api.updateBlocklist(entry.id, { active: !entry.active });
      setBlocklist(blocklist.map(b => b.id === entry.id ? { ...b, active: !b.active } : b));
    } catch (err) {
      alert('Failed to update status: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to remove this plate from the watchlist?')) return;
    try {
      await api.deleteBlocklist(id);
      setBlocklist(blocklist.filter(b => b.id !== id));
    } catch (err) {
      alert('Failed to delete entry: ' + err.message);
    }
  };

  return (
    <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Top Header & Add Action */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid #ef4444',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <AlertOctagon size={24} color="#ef4444" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>
              SECURITY WATCHLIST & BLOCKLIST REGISTRY
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
              Flagged license plates will trigger immediate audio sirens, email dispatches, and HUD interception alerts.
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="btn-cyber-danger"
          style={{ fontSize: '0.85rem' }}
        >
          <Plus size={16} /> Flag License Plate
        </button>
      </div>

      {/* Search Filter Bar */}
      <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
          <Search size={16} color="#64748b" style={{ position: 'absolute', left: '10px', top: '9px' }} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search watchlist by plate number..."
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '7px 12px 7px 32px',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem'
            }}
          />
        </div>

        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
          <strong>{blocklist.length}</strong> flagged vehicles registered
        </div>
      </div>

      {/* Blocklist Registry Table */}
      <div className="glass-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'left', color: '#94a3b8' }}>
              <th style={{ padding: '10px 12px' }}>STATUS</th>
              <th style={{ padding: '10px 12px' }}>FLAGGED LICENSE PLATE</th>
              <th style={{ padding: '10px 12px' }}>SEVERITY</th>
              <th style={{ padding: '10px 12px' }}>SECURITY REASON / DIRECTIVE</th>
              <th style={{ padding: '10px 12px' }}>ISSUED BY</th>
              <th style={{ padding: '10px 12px' }}>DATE REGISTERED</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {blocklist.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
                  No vehicles found in watchlist registry.
                </td>
              </tr>
            ) : (
              blocklist.map((b) => (
                <tr
                  key={b.id}
                  style={{
                    borderBottom: '1px solid rgba(30, 41, 59, 0.6)',
                    backgroundColor: b.active ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                    opacity: b.active ? 1 : 0.6
                  }}
                >
                  <td style={{ padding: '10px 12px' }}>
                    <span className={`badge ${b.active ? 'badge-danger' : 'badge-info'}`}>
                      {b.active ? 'ACTIVE WATCH' : 'INACTIVE'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div className="license-plate-chip">
                      <span className="ind-badge">IND</span>
                      <span>{b.license_plate}</span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span className={`badge ${b.severity === 'CRITICAL' ? 'badge-danger' : 'badge-warning'}`}>
                      {b.severity}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', color: '#f8fafc', fontWeight: 500 }}>
                    {b.reason}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#94a3b8' }}>
                    {b.added_by}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#cbd5e1' }} className="font-mono">
                    {b.date_added ? b.date_added.replace('T', ' ').substring(0, 10) : '-'}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      <button
                        onClick={() => handleToggleActive(b)}
                        title={b.active ? 'Deactivate Watch' : 'Activate Watch'}
                        className="btn-cyber-outline"
                        style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                      >
                        <Power size={13} color={b.active ? '#34d399' : '#94a3b8'} />
                      </button>
                      <button
                        onClick={() => handleDelete(b.id)}
                        title="Delete from Watchlist"
                        className="btn-cyber-outline"
                        style={{ padding: '4px 8px', fontSize: '0.72rem', borderColor: 'rgba(239, 68, 68, 0.4)' }}
                      >
                        <Trash2 size={13} color="#ef4444" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add Blocklist Modal */}
      {isAddModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(3, 7, 18, 0.85)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 200,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '480px',
            padding: '24px',
            borderRadius: '12px',
            position: 'relative'
          }}>
            <button
              onClick={() => setIsAddModalOpen(false)}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer'
              }}
            >
              <X size={20} />
            </button>

            <h3 style={{ margin: '0 0 6px', fontSize: '1.1rem', fontWeight: 800, color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertOctagon size={20} /> REGISTER FLAGGED VEHICLE
            </h3>
            <p style={{ margin: '0 0 16px', fontSize: '0.78rem', color: '#94a3b8' }}>
              Enter the heavy vehicle details to broadcast instant security alerts upon detection.
            </p>

            <form onSubmit={handleAddSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
                  LICENSE PLATE NUMBER
                </label>
                <input
                  type="text"
                  required
                  value={newPlate}
                  onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
                  placeholder="e.g. TN38AB1234"
                  style={{
                    width: '100%',
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.9rem',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontWeight: 700
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
                  ALERT REASON / OFFENSE
                </label>
                <input
                  type="text"
                  required
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  placeholder="e.g. Stolen Vehicle, Expired Hazardous Permit"
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

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
                    SEVERITY LEVEL
                  </label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '8px 10px',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem'
                    }}
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
                    REGISTERED BY
                  </label>
                  <input
                    type="text"
                    value={newAddedBy}
                    onChange={(e) => setNewAddedBy(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="btn-cyber-outline"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-cyber-danger"
                >
                  Add to Watchlist
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
}
