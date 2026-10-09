import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Flame, 
  RefreshCw, 
  Search, 
  FileText, 
  Download, 
  Trash2, 
  Sparkles, 
  Calendar, 
  Truck, 
  Gauge, 
  CreditCard, 
  Check, 
  X, 
  AlertOctagon, 
  FileCheck2, 
  ExternalLink,
  Building2,
  Cpu,
  BadgeAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import { soundAlert } from '../services/soundAlert';

export default function FCEnforcementManager() {
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState(''); // '', 'VALID', 'EXPIRED_RENEWAL_REQUIRED', 'DESTROY_VEHICLE_SCRAP'
  const [loading, setLoading] = useState(false);

  // Quick Plate Lookup State
  const [scannerPlate, setScannerPlate] = useState('');
  const [scannedResult, setScannedResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);

  // Modals
  const [selectedNoticeVehicle, setSelectedNoticeVehicle] = useState(null);
  const [policeNoticeData, setPoliceNoticeData] = useState(null);
  const [loadingNotice, setLoadingNotice] = useState(false);

  const [renewalModalVehicle, setRenewalModalVehicle] = useState(null);
  const [isRenewing, setIsRenewing] = useState(false);
  const [renewalSuccess, setRenewalSuccess] = useState(null);

  const [destructionModalVehicle, setDestructionModalVehicle] = useState(null);
  const [isDestroying, setIsDestroying] = useState(false);
  const [destructionCert, setDestructionCert] = useState(null);

  const [payFineModalVehicle, setPayFineModalVehicle] = useState(null);
  const [isPayingFine, setIsPayingFine] = useState(false);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const res = await api.getFCRecords({
        page,
        limit: 15,
        search,
        fc_status: statusFilter
      });
      setRecords(res.records || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      console.error('Failed to fetch FC records:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await api.getFCStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load FC stats:', err);
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchStats();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchRecords();
  };

  const handleQuickScan = async (e) => {
    e.preventDefault();
    if (!scannerPlate.trim()) return;
    setIsScanning(true);
    setScannedResult(null);
    try {
      const res = await api.verifyPlateFC(scannerPlate.trim().toUpperCase());
      setScannedResult(res);
      if (res.police_action_required === 'DESTROY_VEHICLE_SCRAP') {
        soundAlert.playSiren(1.8);
      } else if (res.police_action_required === 'FC_RENEWAL_PROCESS') {
        soundAlert.playWarningBeep();
      }
    } catch (err) {
      alert('Error verifying plate: ' + err.message);
    } finally {
      setIsScanning(false);
    }
  };

  const openPoliceNoticeModal = async (vehicle) => {
    setSelectedNoticeVehicle(vehicle);
    setLoadingNotice(true);
    setPoliceNoticeData(null);
    try {
      const data = await api.getPoliceNotice(vehicle.license_plate);
      setPoliceNoticeData(data);
    } catch (err) {
      alert('Failed to load police notice: ' + err.message);
    } finally {
      setLoadingNotice(false);
    }
  };

  const handleExecuteRenewal = async () => {
    if (!renewalModalVehicle) return;
    setIsRenewing(true);
    setRenewalSuccess(null);
    try {
      const res = await api.processFCRenewal(renewalModalVehicle.license_plate, {
        brake_efficiency: 92.4,
        suspension_rating: 88.6,
        structural_integrity: 94.0,
        emission_level: 'BS-VI Pass (CO: 0.11%, HC: 38 ppm)'
      });
      setRenewalSuccess(res);
      fetchRecords();
      fetchStats();
      if (scannedResult && scannedResult.license_plate === renewalModalVehicle.license_plate) {
        setScannedResult(res.record);
      }
    } catch (err) {
      alert('FC Renewal failed: ' + err.message);
    } finally {
      setIsRenewing(false);
    }
  };

  const handleExecuteDestruction = async () => {
    if (!destructionModalVehicle) return;
    setIsDestroying(true);
    setDestructionCert(null);
    try {
      const res = await api.confirmScrapping(
        destructionModalVehicle.license_plate,
        'RVSF National Heavy Vehicle Scrapping Facility #07',
        'SEC-CMD-01'
      );
      setDestructionCert(res.certificate);
      fetchRecords();
      fetchStats();
      if (scannedResult && scannedResult.license_plate === destructionModalVehicle.license_plate) {
        setScannedResult(res.record);
      }
    } catch (err) {
      alert('Scrapping confirmation failed: ' + err.message);
    } finally {
      setIsDestroying(false);
    }
  };

  const handlePayFine = async () => {
    if (!payFineModalVehicle) return;
    setIsPayingFine(true);
    try {
      await api.payFCFine(payFineModalVehicle.license_plate);
      alert(`Payment for vehicle ${payFineModalVehicle.license_plate} recorded successfully.`);
      setPayFineModalVehicle(null);
      fetchRecords();
      fetchStats();
    } catch (err) {
      alert('Fine payment failed: ' + err.message);
    } finally {
      setIsPayingFine(false);
    }
  };

  return (
    <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* KPI Stats Header */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '14px' }}>
        
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>REGISTERED HEAVY FLEET</span>
            <Truck size={18} color="#00f2fe" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc' }}>
            {stats?.total_registered_vehicles || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '4px' }}>
            National MoRTH & RTO Connected
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>VALID FC COMPLIANT</span>
            <CheckCircle2 size={18} color="#10b981" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#10b981' }}>
            {stats?.valid_fc_count || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#34d399', marginTop: '4px' }}>
            {stats?.compliance_rate || 0}% Roadworthy Compliance Rate
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: '#fcd34d', fontWeight: 600 }}>FC RENEWAL REQUIRED</span>
            <AlertTriangle size={18} color="#f59e0b" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24' }}>
            {stats?.renewal_required_count || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#fca5a5', marginTop: '4px' }}>
            Eligible for RTO Testing & ₹5,000 Fine
          </div>
        </div>

        <div className="glass-panel glass-panel-danger" style={{ padding: '16px', borderLeft: '4px solid #ef4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 600 }}>POLICE: DESTROY / SCRAP</span>
            <Flame size={18} color="#ef4444" className="animate-pulse-glow" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f87171' }}>
            {stats?.destruction_order_count || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#fca5a5', marginTop: '4px' }}>
            End-of-Life (&gt;15 Yrs) Mandatory Impound
          </div>
        </div>

      </div>

      {/* Instant Plate FC Scanner Radar & Quick Action Box */}
      <div className="glass-panel" style={{ padding: '20px', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Cpu size={20} color="#030712" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.08rem', fontWeight: 800 }}>
                INSTANT PLATE FC AUDIT & POLICE DISPATCH RADAR
              </h2>
              <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8' }}>
                Query national transport database to verify fitness validity, age, and determine if vehicle needs <strong>FC Process</strong> or <strong>Police Destruction</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Search Input for Scanner */}
        <form onSubmit={handleQuickScan} style={{ display: 'flex', gap: '10px', maxWidth: '640px' }}>
          <input
            type="text"
            value={scannerPlate}
            onChange={(e) => setScannerPlate(e.target.value.toUpperCase())}
            placeholder="Enter License Plate (e.g., TN38AB1234, KA01MJ9944, MH12PK4321)..."
            style={{
              flex: 1,
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(0, 242, 254, 0.35)',
              padding: '10px 14px',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '0.9rem',
              fontFamily: 'JetBrains Mono, monospace'
            }}
          />
          <button
            type="submit"
            disabled={isScanning}
            className="btn-cyber-primary"
            style={{ padding: '10px 20px', fontSize: '0.85rem' }}
          >
            <Search size={15} /> {isScanning ? 'Auditing...' : 'Run FC Audit'}
          </button>
        </form>

        {/* Scanned Result Banner */}
        {scannedResult && (
          <div style={{
            marginTop: '16px',
            padding: '16px',
            borderRadius: '8px',
            background: scannedResult.police_action_required === 'DESTROY_VEHICLE_SCRAP'
              ? 'rgba(239, 68, 68, 0.12)'
              : scannedResult.police_action_required === 'FC_RENEWAL_PROCESS'
              ? 'rgba(245, 158, 11, 0.12)'
              : 'rgba(16, 185, 129, 0.12)',
            border: `1px solid ${
              scannedResult.police_action_required === 'DESTROY_VEHICLE_SCRAP'
                ? '#ef4444'
                : scannedResult.police_action_required === 'FC_RENEWAL_PROCESS'
                ? '#f59e0b'
                : '#10b981'
            }`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div className="license-plate-chip" style={{ fontSize: '1rem', padding: '6px 14px' }}>
                <span className="ind-badge">IND</span>
                <span>{scannedResult.license_plate}</span>
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.98rem', color: '#f8fafc' }}>
                    {scannedResult.owner_name}
                  </span>
                  <span className="badge badge-info font-mono">
                    Age: {scannedResult.vehicle_age_years} Yrs
                  </span>
                  <span className={`badge ${
                    scannedResult.police_action_required === 'DESTROY_VEHICLE_SCRAP'
                      ? 'badge-danger'
                      : scannedResult.police_action_required === 'FC_RENEWAL_PROCESS'
                      ? 'badge-warning'
                      : 'badge-success'
                  }`}>
                    {scannedResult.fc_status}
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: '4px' }}>
                  <strong>FC Expiry:</strong> {scannedResult.fc_expiry_date ? scannedResult.fc_expiry_date.substring(0, 10) : 'EXPIRED'} • <strong>RTO:</strong> {scannedResult.rto_office} • <strong>Fitness Score:</strong> {scannedResult.fitness_score}%
                </div>
              </div>
            </div>

            {/* Quick Action Buttons according to Police Rules */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {scannedResult.police_action_required === 'DESTROY_VEHICLE_SCRAP' ? (
                <>
                  <button
                    onClick={() => openPoliceNoticeModal(scannedResult)}
                    className="btn-cyber-outline"
                    style={{ borderColor: '#ef4444', color: '#f87171', padding: '6px 12px', fontSize: '0.8rem' }}
                  >
                    <FileText size={14} /> Police Destruction Notice
                  </button>
                  <button
                    onClick={() => setDestructionModalVehicle(scannedResult)}
                    className="btn-cyber-primary"
                    style={{ background: 'linear-gradient(135deg, #b91c1c 0%, #ef4444 100%)', color: '#ffffff', padding: '6px 14px', fontSize: '0.8rem' }}
                  >
                    <Flame size={14} /> Impound & Scrapping Terminal
                  </button>
                </>
              ) : scannedResult.police_action_required === 'FC_RENEWAL_PROCESS' ? (
                <>
                  <button
                    onClick={() => openPoliceNoticeModal(scannedResult)}
                    className="btn-cyber-outline"
                    style={{ borderColor: '#f59e0b', color: '#fbbf24', padding: '6px 12px', fontSize: '0.8rem' }}
                  >
                    <FileText size={14} /> Police Challan Notice
                  </button>
                  <button
                    onClick={() => setRenewalModalVehicle(scannedResult)}
                    className="btn-cyber-primary"
                    style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                  >
                    <RefreshCw size={14} /> Run FC Renewal Process
                  </button>
                </>
              ) : (
                <span className="badge badge-success" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                  <CheckCircle2 size={14} /> Fully Roadworthy & Compliant
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Registry Management Table with Filters */}
      <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* Filter Bar & Search */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          
          {/* Status Tabs */}
          <div style={{
            display: 'flex',
            background: 'rgba(15, 23, 42, 0.9)',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid rgba(56, 189, 248, 0.2)'
          }}>
            {[
              { id: '', label: 'All Vehicles' },
              { id: 'DESTROY_VEHICLE_SCRAP', label: '🔥 Police Destroy / Scrap Orders', badge: stats?.destruction_order_count },
              { id: 'EXPIRED_RENEWAL_REQUIRED', label: '⚠️ FC Renewal Required', badge: stats?.renewal_required_count },
              { id: 'VALID', label: '🟢 Compliant Fleet', badge: stats?.valid_fc_count }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => { setStatusFilter(tab.id); setPage(1); }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  background: statusFilter === tab.id ? 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)' : 'transparent',
                  color: statusFilter === tab.id ? '#030712' : '#94a3b8',
                  fontWeight: statusFilter === tab.id ? 700 : 500
                }}
              >
                <span>{tab.label}</span>
                {tab.badge !== undefined && (
                  <span style={{
                    fontSize: '0.68rem',
                    padding: '1px 6px',
                    borderRadius: '10px',
                    background: statusFilter === tab.id ? 'rgba(3, 7, 18, 0.8)' : 'rgba(255, 255, 255, 0.1)',
                    color: statusFilter === tab.id ? '#00f2fe' : '#cbd5e1'
                  }}>
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Search Filter */}
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '6px' }}>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search Plate, Owner, Notice #..."
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                padding: '6px 10px',
                borderRadius: '6px',
                color: '#f8fafc',
                fontSize: '0.8rem',
                minWidth: '220px'
              }}
            />
            <button type="submit" className="btn-cyber-primary" style={{ padding: '6px 12px', fontSize: '0.78rem' }}>
              Search
            </button>
          </form>

        </div>

        {/* FC Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'left', color: '#94a3b8' }}>
                <th style={{ padding: '10px 12px' }}>LICENSE PLATE</th>
                <th style={{ padding: '10px 12px' }}>OWNER / CARRIER</th>
                <th style={{ padding: '10px 12px' }}>VEHICLE AGE</th>
                <th style={{ padding: '10px 12px' }}>FC STATUS</th>
                <th style={{ padding: '10px 12px' }}>POLICE MANDATE / ACTION</th>
                <th style={{ padding: '10px 12px' }}>PENALTY CHALLAN</th>
                <th style={{ padding: '10px 12px' }}>EMISSION GRADE</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
                    No vehicle records match your query.
                  </td>
                </tr>
              ) : (
                records.map((r) => {
                  const isScrap = r.police_action_required === 'DESTROY_VEHICLE_SCRAP';
                  const isRenewal = r.police_action_required === 'FC_RENEWAL_PROCESS';

                  return (
                    <tr
                      key={r.id}
                      style={{
                        borderBottom: '1px solid rgba(30, 41, 59, 0.6)',
                        backgroundColor: isScrap ? 'rgba(239, 68, 68, 0.08)' : (isRenewal ? 'rgba(245, 158, 11, 0.04)' : 'transparent')
                      }}
                    >
                      <td style={{ padding: '10px 12px' }}>
                        <div className="license-plate-chip">
                          <span className="ind-badge">IND</span>
                          <span>{r.license_plate}</span>
                        </div>
                      </td>

                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ color: '#f8fafc', fontWeight: 600 }}>{r.owner_name}</div>
                        <div style={{ color: '#64748b', fontSize: '0.72rem' }}>{r.vehicle_type}</div>
                      </td>

                      <td style={{ padding: '10px 12px' }} className="font-mono">
                        <span style={{
                          fontWeight: 700,
                          color: r.vehicle_age_years >= 15 ? '#ef4444' : (r.vehicle_age_years >= 10 ? '#f59e0b' : '#10b981')
                        }}>
                          {r.vehicle_age_years} Years {r.vehicle_age_years >= 15 ? '(End-of-Life)' : ''}
                        </span>
                      </td>

                      <td style={{ padding: '10px 12px' }}>
                        <span className={`badge ${
                          isScrap ? 'badge-danger' : (isRenewal ? 'badge-warning' : 'badge-success')
                        }`}>
                          {r.fc_status}
                        </span>
                      </td>

                      <td style={{ padding: '10px 12px' }}>
                        {isScrap ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span className="badge badge-danger font-mono">
                              🚨 IMPOUND & DESTROY
                            </span>
                            {r.destruction_order_status === 'DESTROYED' && (
                              <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>SCRAPPED</span>
                            )}
                          </div>
                        ) : isRenewal ? (
                          <span className="badge badge-warning font-mono">
                            ⚠️ MANDATORY FC RENEWAL
                          </span>
                        ) : (
                          <span className="badge badge-success font-mono">
                            AUTHORIZED
                          </span>
                        )}
                      </td>

                      <td style={{ padding: '10px 12px' }} className="font-mono">
                        {r.fine_amount > 0 ? (
                          <span style={{ color: '#ef4444', fontWeight: 700 }}>
                            ₹{r.fine_amount.toLocaleString()}
                          </span>
                        ) : (
                          <span style={{ color: '#10b981' }}>₹0 (Cleared)</span>
                        )}
                      </td>

                      <td style={{ padding: '10px 12px' }}>
                        <span style={{ color: '#cbd5e1', fontSize: '0.75rem' }}>
                          {r.emission_compliance}
                        </span>
                      </td>

                      <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                          <button
                            onClick={() => openPoliceNoticeModal(r)}
                            className="btn-cyber-outline"
                            title="View Police Notice & Statute Document"
                            style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                          >
                            <FileText size={13} /> Notice
                          </button>

                          {isScrap && r.destruction_order_status !== 'DESTROYED' && (
                            <button
                              onClick={() => setDestructionModalVehicle(r)}
                              className="btn-cyber-primary"
                              style={{ background: 'linear-gradient(135deg, #b91c1c 0%, #ef4444 100%)', padding: '4px 8px', fontSize: '0.72rem' }}
                              title="Impound & Confirm Scrapping"
                            >
                              <Flame size={13} /> Destroy
                            </button>
                          )}

                          {isRenewal && (
                            <button
                              onClick={() => setRenewalModalVehicle(r)}
                              className="btn-cyber-primary"
                              style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                              title="Launch Automated RTO Diagnostic Test"
                            >
                              <RefreshCw size={13} /> Renew FC
                            </button>
                          )}

                          {r.fine_amount > 0 && (
                            <button
                              onClick={() => setPayFineModalVehicle(r)}
                              className="btn-cyber-outline"
                              style={{ padding: '4px 8px', fontSize: '0.72rem', borderColor: '#f59e0b', color: '#fbbf24' }}
                              title="Pay Fine"
                            >
                              <CreditCard size={13} /> Pay
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
            Showing page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total records)
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="btn-cyber-outline"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
            >
              Prev
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="btn-cyber-outline"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
            >
              Next
            </button>
          </div>
        </div>

      </div>

      {/* MODAL 1: Official Government / Police Notice Viewer */}
      {selectedNoticeVehicle && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(3, 7, 18, 0.88)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 200,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '24px',
            borderRadius: '12px',
            position: 'relative'
          }}>
            <button
              onClick={() => setSelectedNoticeVehicle(null)}
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

            {loadingNotice ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px' }} />
                Generating Official Police Notice...
              </div>
            ) : policeNoticeData ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {/* Government Header */}
                <div style={{
                  textAlign: 'center',
                  borderBottom: '2px solid rgba(56, 189, 248, 0.3)',
                  paddingBottom: '14px'
                }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.08em' }}>
                    MINISTRY OF ROAD TRANSPORT & HIGHWAYS • GOVT. OF INDIA
                  </div>
                  <h3 style={{ margin: '4px 0', fontSize: '1.2rem', fontWeight: 900, color: '#f8fafc' }}>
                    {policeNoticeData.order_type === 'DESTRUCTION_ORDER'
                      ? '🚨 POLICE IMPOUND & VEHICLE DESTRUCTION NOTICE'
                      : '⚠️ STATUTORY FITNESS CERTIFICATE RENEWAL ORDER'}
                  </h3>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                    Statute: {policeNoticeData.statute}
                  </div>
                </div>

                {/* Notice Metadata Badge */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  background: 'rgba(15, 23, 42, 0.7)',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  fontSize: '0.78rem'
                }}>
                  <div>
                    <span style={{ color: '#94a3b8' }}>Notice Reference:</span>{' '}
                    <strong style={{ color: '#00f2fe' }} className="font-mono">{policeNoticeData.notice_number}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#94a3b8' }}>Date:</span>{' '}
                    <strong style={{ color: '#f8fafc' }}>{policeNoticeData.date_issued.substring(0, 19)}</strong>
                  </div>
                </div>

                {/* Target Vehicle Particulars */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '10px',
                  background: 'rgba(15, 23, 42, 0.5)',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '0.82rem'
                }}>
                  <div>
                    <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>LICENSE PLATE NUMBER:</span>
                    <div style={{ fontWeight: 800, color: '#00f2fe', fontSize: '1.1rem', fontFamily: 'monospace' }}>
                      {policeNoticeData.license_plate}
                    </div>
                  </div>

                  <div>
                    <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>REGISTERED OWNER:</span>
                    <div style={{ fontWeight: 700, color: '#f8fafc' }}>
                      {policeNoticeData.owner_name}
                    </div>
                  </div>

                  <div>
                    <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>VEHICLE AGE & CLASS:</span>
                    <div style={{ color: '#cbd5e1' }}>
                      {policeNoticeData.vehicle_age} • {policeNoticeData.vehicle_type}
                    </div>
                  </div>

                  <div>
                    <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>STATUTORY FINE PENALTY:</span>
                    <div style={{ color: '#ef4444', fontWeight: 800 }}>
                      ₹{policeNoticeData.fine_amount?.toLocaleString()} (Under Sec 192)
                    </div>
                  </div>
                </div>

                {/* Legal Enforcement Mandate Box */}
                <div style={{
                  background: policeNoticeData.order_type === 'DESTRUCTION_ORDER' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  borderLeft: `4px solid ${policeNoticeData.order_type === 'DESTRUCTION_ORDER' ? '#ef4444' : '#f59e0b'}`,
                  padding: '14px',
                  borderRadius: '6px'
                }}>
                  <div style={{ fontWeight: 700, color: policeNoticeData.order_type === 'DESTRUCTION_ORDER' ? '#f87171' : '#fbbf24', fontSize: '0.88rem', marginBottom: '6px' }}>
                    LEGAL DIRECTIVE & POLICE ENFORCEMENT ORDER:
                  </div>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#f8fafc', lineHeight: 1.5 }}>
                    {policeNoticeData.action_summary}
                  </p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
                  <button
                    onClick={() => window.print()}
                    className="btn-cyber-outline"
                    style={{ fontSize: '0.8rem' }}
                  >
                    <Download size={14} /> Print Police Notice
                  </button>
                  <button
                    onClick={() => setSelectedNoticeVehicle(null)}
                    className="btn-cyber-primary"
                    style={{ fontSize: '0.8rem' }}
                  >
                    Close Notice
                  </button>
                </div>

              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* MODAL 2: Automated RTO Fitness Diagnostic & FC Renewal Studio */}
      {renewalModalVehicle && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(3, 7, 18, 0.88)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 200,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '620px',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '24px',
            borderRadius: '12px',
            position: 'relative'
          }}>
            <button
              onClick={() => {
                setRenewalModalVehicle(null);
                setRenewalSuccess(null);
              }}
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

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <FileCheck2 size={24} color="#030712" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>
                  RTO AUTOMATED FITNESS TESTING & FC RENEWAL
                </h3>
                <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8' }}>
                  Multi-point brake, emission, suspension, and chassis diagnostic certification.
                </p>
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '12px', borderRadius: '6px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span>Target Vehicle: <strong style={{ color: '#00f2fe' }}>{renewalModalVehicle.license_plate}</strong></span>
                <span>Age: <strong>{renewalModalVehicle.vehicle_age_years} Years</strong></span>
                <span>RTO: <strong>{renewalModalVehicle.rto_office}</strong></span>
              </div>
            </div>

            {/* Diagnostic Parameters Breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                  <span>1. Roller Brake Efficiency Test (Dry/Wet)</span>
                  <span style={{ color: '#10b981', fontWeight: 700 }}>92.4% (PASS)</span>
                </div>
                <div style={{ width: '100%', height: '5px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '3px' }}>
                  <div style={{ width: '92.4%', height: '100%', background: '#10b981', borderRadius: '3px' }} />
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                  <span>2. Smoke Opacity & Exhaust Emissions (BS-VI)</span>
                  <span style={{ color: '#10b981', fontWeight: 700 }}>BS-VI Pass (CO: 0.11%)</span>
                </div>
                <div style={{ width: '100%', height: '5px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '3px' }}>
                  <div style={{ width: '96%', height: '100%', background: '#10b981', borderRadius: '3px' }} />
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                  <span>3. Chassis & Structural Load Fatigue</span>
                  <span style={{ color: '#10b981', fontWeight: 700 }}>94.0% (PASS)</span>
                </div>
                <div style={{ width: '100%', height: '5px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '3px' }}>
                  <div style={{ width: '94%', height: '100%', background: '#10b981', borderRadius: '3px' }} />
                </div>
              </div>
            </div>

            {renewalSuccess && (
              <div style={{
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid #10b981',
                padding: '14px',
                borderRadius: '8px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#10b981', fontWeight: 700, fontSize: '0.9rem' }}>
                  <CheckCircle2 size={18} /> {renewalSuccess.message}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: '6px' }}>
                  Certificate ID: <strong className="font-mono">{renewalSuccess.inspection_summary?.rto_cert_id}</strong> • Certified Valid Until: <strong style={{ color: '#00f2fe' }}>{renewalSuccess.inspection_summary?.certified_until}</strong>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => {
                  setRenewalModalVehicle(null);
                  setRenewalSuccess(null);
                }}
                className="btn-cyber-outline"
                style={{ fontSize: '0.8rem' }}
              >
                Close
              </button>
              {!renewalSuccess && (
                <button
                  onClick={handleExecuteRenewal}
                  disabled={isRenewing}
                  className="btn-cyber-primary"
                  style={{ fontSize: '0.8rem' }}
                >
                  <RefreshCw size={14} className={isRenewing ? 'animate-spin' : ''} />
                  {isRenewing ? 'Certifying...' : 'Certify & Issue 1-Year FC'}
                </button>
              )}
            </div>

          </div>
        </div>
      )}

      {/* MODAL 3: Police Vehicle Destruction & Scrapping Terminal */}
      {destructionModalVehicle && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(3, 7, 18, 0.88)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 200,
          padding: '20px'
        }}>
          <div className="glass-panel glass-panel-danger" style={{
            width: '100%',
            maxWidth: '640px',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '24px',
            borderRadius: '12px',
            position: 'relative'
          }}>
            <button
              onClick={() => {
                setDestructionModalVehicle(null);
                setDestructionCert(null);
              }}
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

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #b91c1c 0%, #ef4444 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Flame size={24} color="#ffffff" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#f87171' }}>
                  REGISTERED VEHICLE SCRAPPING FACILITY (RVSF) TERMINAL
                </h3>
                <p style={{ margin: 0, fontSize: '0.78rem', color: '#fca5a5' }}>
                  Execution of Mandatory End-of-Life Commercial Vehicle Scrappage & Destruction Warrant.
                </p>
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px', borderRadius: '6px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span>Vehicle: <strong style={{ color: '#f87171' }}>{destructionModalVehicle.license_plate}</strong></span>
                <span>Age: <strong style={{ color: '#ef4444' }}>{destructionModalVehicle.vehicle_age_years} Years (&gt;15 Yrs)</strong></span>
                <span>Owner: <strong>{destructionModalVehicle.owner_name}</strong></span>
              </div>
            </div>

            {!destructionCert ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '18px' }}>
                <div style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  color: '#f8fafc',
                  lineHeight: 1.5
                }}>
                  <strong>LEGAL MANDATE:</strong> Under Section 56 of the Motor Vehicles Act and the National Vehicle Scrappage Policy, commercial vehicles exceeding 15 years with expired fitness cannot be renewed and are mandated for permanent deregistration and physical shredding/scrapping at an authorized RVSF facility.
                </div>

                <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  Authorized Facility: <strong>RVSF National Heavy Vehicle Scrapping Facility #07</strong><br />
                  Scrappage Incentive Payout to Owner: <strong>₹55,000 - ₹75,000 (Scrap Value Credit)</strong>
                </div>
              </div>
            ) : (
              <div style={{
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid #10b981',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '16px'
              }}>
                <div style={{ color: '#10b981', fontWeight: 800, fontSize: '1rem', marginBottom: '6px' }}>
                  ✅ OFFICIAL CERTIFICATE OF DESTRUCTION (COD) ISSUED
                </div>
                <div style={{ fontSize: '0.78rem', color: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div>COD Number: <strong className="font-mono" style={{ color: '#00f2fe' }}>{destructionCert.certificate_number}</strong></div>
                  <div>Vehicle: <strong>{destructionCert.license_plate}</strong> ({destructionCert.vehicle_age})</div>
                  <div>Destruction Timestamp: <strong>{destructionCert.destruction_date}</strong></div>
                  <div>Facility: <strong>{destructionCert.facility_name}</strong></div>
                  <div>Authorizing Officer: <strong>{destructionCert.authorizing_officer}</strong></div>
                  <div>Scrappage Incentive Credit: <strong style={{ color: '#34d399' }}>{destructionCert.scrappage_incentive_credit}</strong></div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => {
                  setDestructionModalVehicle(null);
                  setDestructionCert(null);
                }}
                className="btn-cyber-outline"
                style={{ fontSize: '0.8rem' }}
              >
                Close
              </button>
              {!destructionCert && (
                <button
                  onClick={handleExecuteDestruction}
                  disabled={isDestroying}
                  className="btn-cyber-primary"
                  style={{ background: 'linear-gradient(135deg, #b91c1c 0%, #ef4444 100%)', color: '#ffffff', fontSize: '0.8rem' }}
                >
                  <Flame size={14} className={isDestroying ? 'animate-spin' : ''} />
                  {isDestroying ? 'Executing Scrapping...' : 'Confirm Physical Destruction & Issue COD'}
                </button>
              )}
            </div>

          </div>
        </div>
      )}

      {/* MODAL 4: Pay Fine Modal */}
      {payFineModalVehicle && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(3, 7, 18, 0.88)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 200,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '460px',
            padding: '24px',
            borderRadius: '12px',
            position: 'relative'
          }}>
            <button
              onClick={() => setPayFineModalVehicle(null)}
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

            <h3 style={{ margin: '0 0 12px', fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CreditCard size={20} color="#00f2fe" /> SETTLE FC PENALTY CHALLAN
            </h3>

            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Target Vehicle Plate:</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#00f2fe', fontFamily: 'monospace' }}>
                {payFineModalVehicle.license_plate}
              </div>
              <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '8px' }}>Outstanding Challan Amount:</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ef4444', fontFamily: 'monospace' }}>
                ₹{payFineModalVehicle.fine_amount?.toLocaleString()}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => setPayFineModalVehicle(null)}
                className="btn-cyber-outline"
                style={{ fontSize: '0.8rem' }}
              >
                Cancel
              </button>
              <button
                onClick={handlePayFine}
                disabled={isPayingFine}
                className="btn-cyber-primary"
                style={{ fontSize: '0.8rem' }}
              >
                <Check size={14} /> {isPayingFine ? 'Processing...' : 'Confirm e-Challan Payment'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
