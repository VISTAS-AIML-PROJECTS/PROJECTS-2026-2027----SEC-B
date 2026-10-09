import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Layers, 
  Package, 
  Gauge, 
  FileCheck2, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Trash2, 
  Truck,
  Filter,
  PieChart as PieIcon,
  Info
} from 'lucide-react';
import {
  BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { api } from '../services/api';

const COLORS = ['#00f2fe', '#38bdf8', '#818cf8', '#a855f7', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#14b8a6'];

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('all'); // 'all', 'types', 'cargo', 'speed', 'fc'

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getTruckStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load fleet statistics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading || !stats) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', color: '#64748b' }}>
        <div style={{
          display: 'inline-block',
          width: '32px',
          height: '32px',
          border: '3px solid rgba(0, 242, 254, 0.2)',
          borderTopColor: '#00f2fe',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '14px'
        }} />
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#94a3b8' }}>Loading Fleet & Vehicle Statistics...</div>
      </div>
    );
  }

  const { summary, type_distribution, cargo_distribution, speed_buckets, fc_distribution } = stats;

  const totalTrucks = summary.total_trucks || 1;

  // Fallback for FC distribution if not present
  const fcData = fc_distribution && fc_distribution.length > 0 ? fc_distribution : [
    { name: 'FC Valid (Compliant)', count: summary.total_fc_valid || Math.round(totalTrucks * 0.88), color: '#10b981' },
    { name: 'FC Renewal Required (Fine ₹5K)', count: summary.total_fc_renewal_required || Math.round(totalTrucks * 0.085), color: '#f59e0b' },
    { name: 'Police Destroy / Scrap Order', count: summary.total_fc_destruction_orders || Math.round(totalTrucks * 0.035), color: '#ef4444' }
  ];

  const complianceRate = summary.fc_compliance_rate || 
    ((fcData[0].count / totalTrucks) * 100).toFixed(1);

  return (
    <div style={{ padding: '0 16px 28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
      
      {/* Header with Title & Sub-View Switcher */}
      <div className="glass-panel" style={{
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '14px',
        borderLeft: '4px solid #a855f7'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(168, 85, 247, 0.12)',
            border: '1px solid rgba(168, 85, 247, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <BarChart3 size={22} color="#a855f7" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, letterSpacing: '-0.01em', color: '#f8fafc' }}>
                FLEET COMPOSITION & ENFORCEMENT STATISTICS
              </h1>
              <span className="badge badge-info" style={{ fontSize: '0.68rem', textTransform: 'uppercase', borderColor: 'rgba(168, 85, 247, 0.5)', color: '#c084fc' }}>
                Categorical Census
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8' }}>
              MTL-ViT vehicle classifications, cargo freight types, speed histogram distribution, and FC compliance metrics
            </p>
          </div>
        </div>

        {/* Sub-View Navigation Pills */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          background: 'rgba(15, 23, 42, 0.85)',
          padding: '4px',
          borderRadius: '8px',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          flexWrap: 'wrap'
        }}>
          {[
            { id: 'all', label: 'All Statistics', icon: BarChart3 },
            { id: 'types', label: 'Vehicle Types', icon: Layers },
            { id: 'cargo', label: 'Cargo & Freight', icon: Package },
            { id: 'speed', label: 'Speed Histogram', icon: Gauge },
            { id: 'fc', label: 'FC Compliance', icon: FileCheck2 }
          ].map(tab => {
            const Icon = tab.icon;
            const isSel = activeSubTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                style={{
                  background: isSel ? 'rgba(168, 85, 247, 0.25)' : 'transparent',
                  color: isSel ? '#c084fc' : '#94a3b8',
                  border: isSel ? '1px solid rgba(168, 85, 247, 0.45)' : '1px solid transparent',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: isSel ? 700 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Fleet KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '14px' }}>
        
        {/* Total Monitored Fleet */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>TOTAL HEAVY FLEET</span>
            <Truck size={18} color="#00f2fe" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
            {summary.total_trucks.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#34d399', marginTop: '6px' }}>
            Active multi-camera corridor tracking
          </div>
        </div>

        {/* Vehicle Categories Count */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>MTL-ViT VEHICLE CLASSES</span>
            <Layers size={18} color="#a855f7" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#c084fc' }}>
            {type_distribution.length} <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Classes</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '6px' }}>
            Container, Concrete, Box, Flatbed & more
          </div>
        </div>

        {/* Cargo Attributes Count */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>CARGO FREIGHT TYPES</span>
            <Package size={18} color="#10b981" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399' }}>
            {cargo_distribution.length} <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Varieties</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '6px' }}>
            Aggregate, Sealed ISO, Hazmat, Canvas
          </div>
        </div>

        {/* FC Compliance Rate */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>FC COMPLIANCE RATE</span>
            <FileCheck2 size={18} color="#10b981" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#10b981' }}>
            {complianceRate}%
          </div>
          <div style={{ fontSize: '0.72rem', color: '#34d399', marginTop: '6px' }}>
            Fitness Certificate compliant fleet
          </div>
        </div>

      </div>

      {/* SECTION 1: MTL-ViT VEHICLE TYPE COMPOSITION */}
      {(activeSubTab === 'all' || activeSubTab === 'types') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#a855f7' }} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  MTL-ViT VEHICLE TYPE COMPOSITION
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Multi-Task Learning Vision Transformer classification census across all corridor checkpoints
                </div>
              </div>
            </div>
            <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
              Total Classified: {summary.total_trucks}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', alignItems: 'center' }}>
            
            {/* Donut Chart */}
            <div style={{ width: '100%', height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={type_distribution}
                    dataKey="count"
                    nameKey="type"
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={105}
                    paddingAngle={3}
                    label={({ name, percent }) => `${name.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                    fontSize={11}
                  >
                    {type_distribution.map((entry, index) => (
                      <Cell key={`type-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ background: '#0b0f19', border: '1px solid rgba(168, 85, 247, 0.4)', borderRadius: '8px', fontSize: '12px' }}
                    formatter={(val, name) => [`${val} trucks (${((val / totalTrucks) * 100).toFixed(1)}%)`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Tabular Breakdown List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                Classification Census Table
              </div>
              <div style={{ maxHeight: '250px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '6px' }}>
                {type_distribution.map((item, idx) => {
                  const pct = ((item.count / totalTrucks) * 100).toFixed(1);
                  const color = COLORS[idx % COLORS.length];
                  return (
                    <div 
                      key={item.type}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        background: 'rgba(15, 23, 42, 0.65)',
                        borderRadius: '6px',
                        borderLeft: `3px solid ${color}`,
                        fontSize: '0.8rem'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color }} />
                        <span style={{ fontWeight: 600, color: '#f8fafc' }}>{item.type}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <span className="font-mono" style={{ color: '#94a3b8' }}>{item.count} trucks</span>
                        <span className="font-mono" style={{ fontWeight: 700, color: color, minWidth: '42px', textAlign: 'right' }}>
                          {pct}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      )}

      {/* SECTION 2: CARGO & FREIGHT STATE DISTRIBUTION */}
      {(activeSubTab === 'all' || activeSubTab === 'cargo') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981' }} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  CARGO & FREIGHT STATE DISTRIBUTION
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Categorical breakdown of haulage contents, tarp seals, and hazardous cargo classifications
                </div>
              </div>
            </div>
            <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
              {cargo_distribution.length} Active Cargo Categories
            </span>
          </div>

          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cargo_distribution} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.35)" />
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis dataKey="attribute" type="category" stroke="#cbd5e1" fontSize={11} width={170} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#0b0f19', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val) => [`${val} loads (${((val / totalTrucks) * 100).toFixed(1)}%)`, 'Freight Count']}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {cargo_distribution.map((entry, index) => {
                    const isHazmat = entry.attribute.toLowerCase().includes('hazmat') || entry.attribute.toLowerCase().includes('chemical');
                    return (
                      <Cell 
                        key={`cargo-cell-${index}`} 
                        fill={isHazmat ? '#ef4444' : COLORS[index % COLORS.length]} 
                      />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Freight Safety Notice */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 14px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: '6px',
            fontSize: '0.74rem',
            color: '#94a3b8'
          }}>
            <Info size={16} color="#00f2fe" />
            <span>
              Tarped and sealed containers undergo automated geometric overhang and seal integrity validation at portal sensors. Hazmat freight is cross-checked against authorized transit manifests.
            </span>
          </div>
        </div>
      )}

      {/* SECTION 3: SPEED DISTRIBUTION HISTOGRAM */}
      {(activeSubTab === 'all' || activeSubTab === 'speed') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  SPEED DISTRIBUTION HISTOGRAM
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Corridor velocity frequency buckets from weighbridge crawling to overspeed violations
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>Avg: {summary.avg_speed} km/h</span>
              <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>Limit: 60 km/h</span>
            </div>
          </div>

          <div style={{ width: '100%', height: '270px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={speed_buckets} margin={{ top: 10, right: 15, left: -15, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.35)" />
                <XAxis dataKey="range" stroke="#64748b" fontSize={10} interval={0} angle={-10} textAnchor="end" height={45} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#0b0f19', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val) => [`${val} vehicles (${((val / totalTrucks) * 100).toFixed(1)}%)`, 'Frequency']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {speed_buckets.map((entry, index) => {
                    // Color code: safe (green), normal (sky), boundary (amber), overspeed (red), extreme (dark crimson)
                    const bucketColors = ['#10b981', '#38bdf8', '#f59e0b', '#ef4444', '#b91c1c'];
                    return (
                      <Cell key={`speed-bucket-${index}`} fill={bucketColors[index] || '#38bdf8'} />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Speed Brackets Legend Table */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
            {[
              { label: '< 40 km/h', desc: 'Slow / Crawl zone', color: '#10b981' },
              { label: '40-55 km/h', desc: 'Normal transit', color: '#38bdf8' },
              { label: '55-65 km/h', desc: 'Corridor limit zone', color: '#f59e0b' },
              { label: '65-80 km/h', desc: 'Automated citation', color: '#ef4444' },
              { label: '> 80 km/h', desc: 'Extreme violation', color: '#b91c1c' }
            ].map(b => (
              <div key={b.label} style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '8px 12px', borderRadius: '6px', borderLeft: `3px solid ${b.color}` }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: b.color }}>{b.label}</div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>{b.desc}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SECTION 4: FITNESS CERTIFICATE (FC) & POLICE ENFORCEMENT DIRECTIVES */}
      {(activeSubTab === 'all' || activeSubTab === 'fc') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981' }} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  FITNESS CERTIFICATE (FC) & ENFORCEMENT STATISTICS
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Parivahan regulatory compliance status, renewal fines, and police vehicle destruction scrap orders
                </div>
              </div>
            </div>
            <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
              Enforcement Clearance Rate: {complianceRate}%
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            
            {/* FC Valid (Compliant) */}
            <div style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '8px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={18} color="#10b981" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>FC Valid (Compliant)</span>
                </div>
                <span className="badge badge-success" style={{ fontSize: '0.68rem' }}>AUTHORIZED</span>
              </div>
              <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#10b981' }}>
                {fcData[0].count.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Vehicles with active and verified Parivahan fitness certificates. Cleared for corridor transit.
              </div>
            </div>

            {/* FC Renewal Required */}
            <div style={{
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '8px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} color="#f59e0b" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>FC Renewal Required</span>
                </div>
                <span className="badge badge-warning" style={{ fontSize: '0.68rem' }}>FINE ₹5,000</span>
              </div>
              <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24' }}>
                {fcData[1].count.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Expired FC within renewal grace period. E-challan dispatched and test station appointment assigned.
              </div>
            </div>

            {/* Police Scrap / Destruction Order */}
            <div style={{
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Trash2 size={18} color="#ef4444" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>Scrap / Destruction Order</span>
                </div>
                <span className="badge badge-danger" style={{ fontSize: '0.68rem' }}>POLICE ACTION</span>
              </div>
              <div className="font-mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f87171' }}>
                {fcData[2].count.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                End-of-life or unroadworthy vehicles subject to RTO impoundment and authorized scrapping directives.
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
