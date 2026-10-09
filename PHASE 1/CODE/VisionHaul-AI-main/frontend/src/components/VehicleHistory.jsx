import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Search, 
  Download, 
  FileText, 
  FileSpreadsheet, 
  Filter, 
  ChevronLeft, 
  ChevronRight,
  ShieldAlert,
  Truck,
  Eye,
  X,
  LayoutGrid,
  List,
  Image as ImageIcon,
  Camera,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';

export default function VehicleHistory({ selectedTruck, onCloseDetail }) {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [truckType, setTruckType] = useState('');
  const [isOverspeed, setIsOverspeed] = useState('');
  const [fcStatus, setFcStatus] = useState('');
  const [policeAction, setPoliceAction] = useState('');
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('gallery'); // 'gallery' or 'table'
  const [activeModalTruck, setActiveModalTruck] = useState(selectedTruck || null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getTruckLogs({
        page,
        limit: viewMode === 'gallery' ? 18 : 15,
        search,
        truck_type: truckType,
        is_overspeed: isOverspeed,
        fc_status: fcStatus,
        police_action: policeAction
      });
      setLogs(res.logs || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (e) {
      console.error('Failed to fetch truck logs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, truckType, isOverspeed, fcStatus, policeAction, viewMode]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  return (
    <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Top Filter, Search & View Switcher Bar */}
      <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: '280px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search Plate (TN38AB1234), Track (TRK001), Cargo..."
              style={{
                width: '100%',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                padding: '8px 12px 8px 34px',
                borderRadius: '6px',
                color: '#f8fafc',
                fontSize: '0.85rem'
              }}
            />
          </div>
          <button type="submit" className="btn-cyber-primary" style={{ padding: '8px 14px', fontSize: '0.82rem' }}>
            Search
          </button>
        </form>

        {/* Dropdown Filters & View Mode */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          
          {/* View Switcher */}
          <div style={{
            display: 'flex',
            background: 'rgba(15, 23, 42, 0.9)',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid rgba(56, 189, 248, 0.2)'
          }}>
            <button
              onClick={() => setViewMode('gallery')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.78rem',
                cursor: 'pointer',
                background: viewMode === 'gallery' ? 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)' : 'transparent',
                color: viewMode === 'gallery' ? '#030712' : '#94a3b8',
                fontWeight: viewMode === 'gallery' ? 700 : 500
              }}
            >
              <LayoutGrid size={14} /> Image Gallery
            </button>
            <button
              onClick={() => setViewMode('table')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.78rem',
                cursor: 'pointer',
                background: viewMode === 'table' ? 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)' : 'transparent',
                color: viewMode === 'table' ? '#030712' : '#94a3b8',
                fontWeight: viewMode === 'table' ? 700 : 500
              }}
            >
              <List size={14} /> Table View
            </button>
          </div>

          <select
            value={truckType}
            onChange={(e) => { setTruckType(e.target.value); setPage(1); }}
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '7px 10px',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem'
            }}
          >
            <option value="">All Vehicle Types</option>
            <option value="Container Carrier">Container Carrier</option>
            <option value="Flatbed Hauler">Flatbed Hauler</option>
            <option value="Petroleum Tanker">Petroleum Tanker</option>
            <option value="Tipper / Dump Truck">Tipper / Dump Truck</option>
            <option value="Box Freight Truck">Box Freight Truck</option>
            <option value="Refrigerated Carrier">Refrigerated Carrier</option>
            <option value="Concrete Mixer">Concrete Mixer</option>
          </select>

          <select
            value={isOverspeed}
            onChange={(e) => { setIsOverspeed(e.target.value); setPage(1); }}
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '7px 10px',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem'
            }}
          >
            <option value="">All Speed Records</option>
            <option value="true">Overspeeding Only (&gt; 60 km/h)</option>
            <option value="false">Compliant Speed (&le; 60 km/h)</option>
          </select>

          <select
            value={fcStatus}
            onChange={(e) => { setFcStatus(e.target.value); setPage(1); }}
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '7px 10px',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem'
            }}
          >
            <option value="">All FC Compliance</option>
            <option value="VALID">FC Valid (Compliant)</option>
            <option value="EXPIRED">FC Expired (Violation)</option>
            <option value="SCRAPPED">Vehicle Scrapped</option>
          </select>

          <select
            value={policeAction}
            onChange={(e) => { setPoliceAction(e.target.value); setPage(1); }}
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '7px 10px',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem'
            }}
          >
            <option value="">All Police Mandates</option>
            <option value="DESTROY_VEHICLE_SCRAP">🚨 Scrap / Destroy (&ge;15yr)</option>
            <option value="FC_RENEWAL_PROCESS">⚠️ Renewal Notice (&lt;15yr)</option>
            <option value="NONE">No Action (Clean)</option>
          </select>

          {/* Export Buttons */}
          <a
            href={api.csvDownloadUrl}
            download
            className="btn-cyber-outline"
            style={{ fontSize: '0.8rem', padding: '7px 12px', textDecoration: 'none' }}
          >
            <FileSpreadsheet size={15} color="#10b981" /> CSV
          </a>

          <a
            href={api.pdfDownloadUrl}
            download
            className="btn-cyber-outline"
            style={{ fontSize: '0.8rem', padding: '7px 12px', textDecoration: 'none' }}
          >
            <FileText size={15} color="#ef4444" /> PDF
          </a>
        </div>

      </div>

      {/* Main Records Container */}
      {viewMode === 'gallery' ? (
        /* Visual Image Gallery Grid */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '16px'
        }}>
          {logs.length === 0 ? (
            <div className="glass-panel" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '48px', color: '#64748b' }}>
              No image-backed vehicle dossiers found matching your query.
            </div>
          ) : (
            logs.map((l) => {
              const snapshotUrl = api.getSnapshotUrl(l.snapshot_path);
              const plateCropUrl = l.snapshot_path ? api.getSnapshotUrl(l.snapshot_path.replace('.jpg', '_plate.jpg')) : null;

              return (
                <div
                  key={l.id}
                  className="glass-panel"
                  style={{
                    padding: '12px',
                    borderRadius: '10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    border: l.is_blocklisted
                      ? '1px solid rgba(239, 68, 68, 0.4)'
                      : (l.is_overspeed ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid rgba(56, 189, 248, 0.2)'),
                    background: l.is_blocklisted
                      ? 'rgba(239, 68, 68, 0.05)'
                      : (l.is_overspeed ? 'rgba(245, 158, 11, 0.03)' : 'rgba(15, 23, 42, 0.65)'),
                    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onClick={() => setActiveModalTruck(l)}
                >
                  {/* Vehicle Image Snapshot Container */}
                  <div style={{
                    position: 'relative',
                    width: '100%',
                    height: '180px',
                    borderRadius: '6px',
                    overflow: 'hidden',
                    background: '#090d16',
                    border: '1px solid rgba(56, 189, 248, 0.15)'
                  }}>
                    {snapshotUrl ? (
                      <img
                        src={snapshotUrl}
                        alt={`Vehicle ${l.license_plate}`}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                        loading="lazy"
                      />
                    ) : (
                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                        <ImageIcon size={36} />
                      </div>
                    )}

                    {/* Top Overlay Badges */}
                    <div style={{ position: 'absolute', top: '8px', left: '8px', display: 'flex', gap: '6px' }}>
                      <span className="badge badge-info font-mono" style={{ fontSize: '0.7rem' }}>
                        {l.track_id}
                      </span>
                      {l.is_blocklisted && (
                        <span className="badge badge-danger font-mono" style={{ fontSize: '0.68rem' }}>
                          WATCHLIST
                        </span>
                      )}
                      {l.is_overspeed && (
                        <span className="badge badge-warning font-mono" style={{ fontSize: '0.68rem' }}>
                          OVERSPEED
                        </span>
                      )}
                    </div>

                    {/* Speed Radar Watermark */}
                    <div style={{
                      position: 'absolute',
                      bottom: '8px',
                      right: '8px',
                      background: 'rgba(3, 7, 18, 0.85)',
                      backdropFilter: 'blur(4px)',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      color: l.is_overspeed ? '#ef4444' : '#10b981',
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      fontFamily: 'monospace'
                    }}>
                      ⚡ {l.speed} km/h
                    </div>
                  </div>

                  {/* Vehicle Details & Plate Evidence */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div className="license-plate-chip">
                      <span className="ind-badge">IND</span>
                      <span>{l.license_plate}</span>
                    </div>

                    <span className="badge badge-purple" style={{ fontSize: '0.72rem', textTransform: 'none' }}>
                      {l.truck_type}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: '#94a3b8' }}>
                    <span>Color: <strong style={{ color: '#f8fafc' }}>{l.color}</strong></span>
                    <span>Visits: <strong style={{ color: '#38bdf8' }}>#{l.visit_count}</strong></span>
                  </div>

                  <div style={{
                    fontSize: '0.72rem',
                    color: '#64748b',
                    borderTop: '1px solid rgba(56, 189, 248, 0.1)',
                    paddingTop: '6px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span>{l.arrival_time ? l.arrival_time.replace('T', ' ').substring(0, 16) : '-'}</span>
                    <button
                      className="btn-cyber-outline"
                      style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveModalTruck(l);
                      }}
                    >
                      <Eye size={12} /> View Dossier
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        /* Audit Log Table View */
        <div className="glass-panel" style={{ padding: '16px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'left', color: '#94a3b8' }}>
                <th style={{ padding: '10px 12px' }}>EVIDENCE</th>
                <th style={{ padding: '10px 12px' }}>TRACK ID</th>
                <th style={{ padding: '10px 12px' }}>LICENSE PLATE</th>
                <th style={{ padding: '10px 12px' }}>SPEED (KM/H)</th>
                <th style={{ padding: '10px 12px' }}>VIOLATION</th>
                <th style={{ padding: '10px 12px' }}>MTL-ViT TYPE & COLOR</th>
                <th style={{ padding: '10px 12px' }}>CARGO ATTRIBUTES</th>
                <th style={{ padding: '10px 12px' }}>ARRIVAL TIME (UTC)</th>
                <th style={{ padding: '10px 12px' }}>VISIT COUNT</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>DETAILS</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="10" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
                    No vehicle audit records match your query.
                  </td>
                </tr>
              ) : (
                logs.map((l) => {
                  const snapshotUrl = api.getSnapshotUrl(l.snapshot_path);
                  return (
                    <tr
                      key={l.id}
                      style={{
                        borderBottom: '1px solid rgba(30, 41, 59, 0.6)',
                        backgroundColor: l.is_blocklisted ? 'rgba(239, 68, 68, 0.08)' : (l.is_overspeed ? 'rgba(245, 158, 11, 0.04)' : 'transparent')
                      }}
                    >
                      <td style={{ padding: '8px 12px' }}>
                        <div
                          style={{
                            width: '56px',
                            height: '36px',
                            borderRadius: '4px',
                            overflow: 'hidden',
                            background: '#090d16',
                            border: '1px solid rgba(56, 189, 248, 0.2)',
                            cursor: 'pointer'
                          }}
                          onClick={() => setActiveModalTruck(l)}
                        >
                          {snapshotUrl ? (
                            <img
                              src={snapshotUrl}
                              alt="Vehicle snapshot"
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                          ) : (
                            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                              <Camera size={14} />
                            </div>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className="badge badge-info font-mono">{l.track_id}</span>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <div className="license-plate-chip">
                          <span className="ind-badge">IND</span>
                          <span>{l.license_plate}</span>
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px' }} className="font-mono">
                        <span style={{ fontWeight: 700, color: l.is_overspeed ? '#ef4444' : '#10b981' }}>
                          {l.speed} km/h
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        {l.is_overspeed ? (
                          <span className="badge badge-danger">OVERSPEED ⚠️</span>
                        ) : (
                          <span className="badge badge-success">COMPLIANT</span>
                        )}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ color: '#f8fafc', fontWeight: 600 }}>{l.truck_type}</span>
                          <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>({l.color})</span>
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className="badge badge-purple" style={{ textTransform: 'none' }}>
                          {l.cargo_attributes}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: '#cbd5e1' }} className="font-mono">
                        {l.arrival_time ? l.arrival_time.replace('T', ' ').substring(0, 19) : '-'}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className={`badge ${l.visit_count > 3 ? 'badge-warning' : 'badge-info'}`}>
                          Visit #{l.visit_count}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                        <button
                          onClick={() => setActiveModalTruck(l)}
                          className="btn-cyber-outline"
                          style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                        >
                          <Eye size={13} /> View
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Footer */}
      <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
          Showing page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total records)
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="btn-cyber-outline"
            style={{ padding: '6px 12px', fontSize: '0.78rem' }}
          >
            <ChevronLeft size={14} /> Prev
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="btn-cyber-outline"
            style={{ padding: '6px 12px', fontSize: '0.78rem' }}
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Vehicle Detail Modal with Full HD CCTV Image & Plate Crop */}
      {activeModalTruck && (
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
            maxWidth: '680px',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '24px',
            borderRadius: '12px',
            position: 'relative'
          }}>
            <button
              onClick={() => {
                setActiveModalTruck(null);
                if (onCloseDetail) onCloseDetail();
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
                background: 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Truck size={24} color="#030712" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>
                  VEHICLE AUDIT DOSSIER [{activeModalTruck.track_id}]
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <div className="license-plate-chip">
                    <span className="ind-badge">IND</span>
                    <span>{activeModalTruck.license_plate}</span>
                  </div>
                  {activeModalTruck.is_blocklisted && (
                    <span className="badge badge-danger">WATCHLIST HIT</span>
                  )}
                  {activeModalTruck.is_overspeed && (
                    <span className="badge badge-warning">OVERSPEED VIOLATION</span>
                  )}
                </div>
              </div>
            </div>

            {/* High-Resolution CCTV Image Snapshot Frame */}
            {activeModalTruck.snapshot_path && (
              <div style={{
                width: '100%',
                borderRadius: '8px',
                overflow: 'hidden',
                marginBottom: '16px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                background: '#090d16',
                position: 'relative'
              }}>
                <img
                  src={api.getSnapshotUrl(activeModalTruck.snapshot_path)}
                  alt="High Resolution CCTV Snapshot"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  background: 'rgba(3, 7, 18, 0.8)',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  color: '#38bdf8',
                  fontFamily: 'monospace'
                }}>
                  HD CCTV 1280x720 • AI BBOX ANNOTATED
                </div>
              </div>
            )}

            {/* Cropped Plate Evidence Banner */}
            {activeModalTruck.snapshot_path && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(15, 23, 42, 0.7)',
                padding: '10px 14px',
                borderRadius: '6px',
                marginBottom: '16px',
                border: '1px solid rgba(56, 189, 248, 0.15)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <ImageIcon size={18} color="#38bdf8" />
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>ALPR / ANPR Plate Crop:</span>
                </div>
                <img
                  src={api.getSnapshotUrl(activeModalTruck.snapshot_path.replace('.jpg', '_plate.jpg'))}
                  alt="Cropped Plate"
                  style={{ height: '36px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.2)' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>
            )}

            {/* Telemetry Metrics Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.82rem', marginBottom: '18px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>SPEED RECORD</div>
                <div className="font-mono" style={{ fontWeight: 700, fontSize: '1rem', color: activeModalTruck.is_overspeed ? '#ef4444' : '#10b981' }}>
                  {activeModalTruck.speed} km/h (Limit: {activeModalTruck.speed_limit || 60} km/h)
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>VISIT FREQUENCY</div>
                <div className="font-mono" style={{ fontWeight: 700, fontSize: '1rem', color: '#38bdf8' }}>
                  Visit #{activeModalTruck.visit_count || 1}
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>MTL-ViT CLASSIFICATION</div>
                <div style={{ fontWeight: 600, color: '#f8fafc' }}>
                  {activeModalTruck.truck_type} ({activeModalTruck.color})
                </div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>CARGO / FREIGHT ATTRIBUTES</div>
                <div style={{ fontWeight: 600, color: '#c084fc' }}>
                  {activeModalTruck.cargo_attributes}
                </div>
              </div>
            </div>

            <div style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div><strong>Arrival Timestamp:</strong> {activeModalTruck.arrival_time}</div>
              <div><strong>Departure Timestamp:</strong> {activeModalTruck.departure_time || 'Active / Dwell in Progress'}</div>
              <div><strong>Camera Source:</strong> {activeModalTruck.camera_id || 'CAM-01 [HWY-NORTH GATE]'}</div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => {
                  setActiveModalTruck(null);
                  if (onCloseDetail) onCloseDetail();
                }}
                className="btn-cyber-primary"
              >
                Close Dossier
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
