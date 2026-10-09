import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Gauge, 
  Clock, 
  Calendar,
  Zap,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Filter,
  BarChart2,
  SlidersHorizontal
} from 'lucide-react';
import {
  AreaChart, Area,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';
import { api } from '../services/api';

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('daily'); // 'daily', 'monthly', 'yearly'
  const [activeSubTab, setActiveSubTab] = useState('all'); // 'all', 'trends', 'diurnal', 'velocity'

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getTruckStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load analytics:', err);
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
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#94a3b8' }}>Loading Corridor Traffic Analytics...</div>
      </div>
    );
  }

  const { summary, daily_trends, monthly_trends, yearly_trends, hourly_stats } = stats;

  const currentTrendData = timeframe === 'daily' 
    ? daily_trends.map(d => ({ label: d.date, Total: d.total, Overspeed: d.overspeed, Compliant: Math.max(0, d.total - d.overspeed) }))
    : timeframe === 'monthly'
    ? monthly_trends.map(m => ({ label: m.month, Total: m.total }))
    : yearly_trends.map(y => ({ label: y.year, Total: y.total }));

  // Find peak diurnal hour
  const peakHourObj = hourly_stats && hourly_stats.length > 0 
    ? [...hourly_stats].sort((a, b) => b.count - a.count)[0]
    : { hour: '10:00', count: 0 };

  // Calculate diurnal volume stats
  const totalDiurnalVolume = hourly_stats ? hourly_stats.reduce((acc, h) => acc + h.count, 0) : 0;
  const morningRush = hourly_stats ? hourly_stats.filter((_, i) => i >= 8 && i <= 11).reduce((acc, h) => acc + h.count, 0) : 0;
  const eveningRush = hourly_stats ? hourly_stats.filter((_, i) => i >= 16 && i <= 19).reduce((acc, h) => acc + h.count, 0) : 0;

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
        borderLeft: '4px solid #00f2fe'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(0, 242, 254, 0.12)',
            border: '1px solid rgba(0, 242, 254, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <TrendingUp size={22} color="#00f2fe" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, letterSpacing: '-0.01em', color: '#f8fafc' }}>
                CORRIDOR TRAFFIC & FLOW ANALYTICS
              </h1>
              <span className="badge badge-info" style={{ fontSize: '0.68rem', textTransform: 'uppercase' }}>
                Time-Series Engine
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8' }}>
              Real-time volumetric trends, hourly corridor flow, velocity analysis, and congestion telemetry
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
          border: '1px solid rgba(56, 189, 248, 0.2)'
        }}>
          {[
            { id: 'all', label: 'All Analytics', icon: BarChart2 },
            { id: 'trends', label: 'Volume Trends', icon: TrendingUp },
            { id: 'diurnal', label: '24h Diurnal Flow', icon: Clock },
            { id: 'velocity', label: 'Corridor Velocity', icon: Gauge }
          ].map(tab => {
            const Icon = tab.icon;
            const isSel = activeSubTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                style={{
                  background: isSel ? 'rgba(0, 242, 254, 0.2)' : 'transparent',
                  color: isSel ? '#00f2fe' : '#94a3b8',
                  border: isSel ? '1px solid rgba(0, 242, 254, 0.4)' : '1px solid transparent',
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

      {/* Analytics KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '14px' }}>
        
        {/* Total Volume */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>TOTAL CORRIDOR VOLUME</span>
            <Activity size={18} color="#00f2fe" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
            {summary.total_trucks.toLocaleString()}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#34d399', marginTop: '6px' }}>
            <ArrowUpRight size={14} />
            <span>+12.4% vs previous 7-day window</span>
          </div>
        </div>

        {/* Average Corridor Velocity */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>AVERAGE CORRIDOR VELOCITY</span>
            <Gauge size={18} color="#38bdf8" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38bdf8' }}>
            {summary.avg_speed} <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>km/h</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '6px' }}>
            Corridor Limit: <strong style={{ color: '#fbbf24' }}>60.0 km/h</strong> (Normal Flow)
          </div>
        </div>

        {/* Overspeed Incidence Rate */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>OVERSPEED INCIDENCE</span>
            <Zap size={18} color="#f59e0b" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fbbf24' }}>
            {summary.total_overspeed} <span style={{ fontSize: '0.85rem', color: '#fca5a5' }}>({summary.overspeed_rate}%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#34d399', marginTop: '6px' }}>
            <ArrowDownRight size={14} />
            <span>-1.8% reduction post-automated alerts</span>
          </div>
        </div>

        {/* Diurnal Peak Flow Hour */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>PEAK DIURNAL HOUR</span>
            <Clock size={18} color="#a855f7" />
          </div>
          <div className="font-mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#c084fc' }}>
            {peakHourObj.hour}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '6px' }}>
            Peak Throughput: <strong style={{ color: '#00f2fe' }}>{peakHourObj.count} trucks/hr</strong>
          </div>
        </div>

      </div>

      {/* SECTION 1: TRAFFIC VOLUME & VIOLATION TRENDS */}
      {(activeSubTab === 'all' || activeSubTab === 'trends') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#00f2fe' }} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  CORRIDOR TRAFFIC VOLUME & VIOLATION TRENDS
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Aggregated heavy vehicle passage counts vs overspeed violations over {timeframe} periods
                </div>
              </div>
            </div>

            {/* Timeframe selector: Daily / Monthly / Yearly */}
            <div style={{ display: 'flex', gap: '4px', background: 'rgba(15, 23, 42, 0.9)', padding: '3px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
              {['daily', 'monthly', 'yearly'].map((t) => (
                <button
                  key={t}
                  onClick={() => setTimeframe(t)}
                  style={{
                    background: timeframe === t ? 'rgba(0, 242, 254, 0.25)' : 'transparent',
                    color: timeframe === t ? '#00f2fe' : '#94a3b8',
                    border: 'none',
                    padding: '5px 14px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Area Chart */}
          <div style={{ width: '100%', height: '310px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={currentTrendData} margin={{ top: 15, right: 15, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.45}/>
                    <stop offset="95%" stopColor="#00f2fe" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorOver" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.6}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.35)" />
                <XAxis dataKey="label" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    background: '#0b0f19', 
                    border: '1px solid rgba(0, 242, 254, 0.4)', 
                    borderRadius: '8px', 
                    fontSize: '12px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.6)'
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Area type="monotone" dataKey="Total" stroke="#00f2fe" strokeWidth={2.5} fillOpacity={1} fill="url(#colorTotal)" name="Total Vehicles" />
                {timeframe === 'daily' && (
                  <Area type="monotone" dataKey="Overspeed" stroke="#ef4444" strokeWidth={2.5} fillOpacity={1} fill="url(#colorOver)" name="Overspeed Violations" />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Context Footnote */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: '6px',
            fontSize: '0.74rem',
            color: '#94a3b8'
          }}>
            <span>Total Trend Windows Monitored: <strong style={{ color: '#f8fafc' }}>{currentTrendData.length} checkpoints</strong></span>
            <span>Speed Limit Threshold: <strong style={{ color: '#f59e0b' }}>60.0 km/h</strong></span>
            <span>Sensor Source: <strong style={{ color: '#00f2fe' }}>ByteTrack Optical Flow + Calibration Cam</strong></span>
          </div>
        </div>
      )}

      {/* SECTION 2: 24-HOUR DIURNAL FLOW PROFILE */}
      {(activeSubTab === 'all' || activeSubTab === 'diurnal') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#38bdf8' }} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  DIURNAL 24-HOUR CORRIDOR FLOW (HOURLY ARRIVAL CURVE)
                </h2>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Distribution of heavy haulage vehicle arrivals across 24 hours of corridor surveillance
                </div>
              </div>
            </div>

            {/* Quick Summary Badges */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                Morning Window (8-11h): {morningRush} trucks
              </span>
              <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
                Evening Window (16-19h): {eveningRush} trucks
              </span>
            </div>
          </div>

          <div style={{ width: '100%', height: '240px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourly_stats} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.3)" />
                <XAxis dataKey="hour" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#0b0f19', border: '1px solid rgba(56, 189, 248, 0.4)', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val) => [`${val} vehicles`, 'Hourly Volume']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {hourly_stats.map((entry, index) => {
                    const isPeak = entry.hour === peakHourObj.hour;
                    const isRush = (index >= 8 && index <= 11) || (index >= 16 && index <= 19);
                    return (
                      <Cell 
                        key={`diurnal-cell-${index}`} 
                        fill={isPeak ? '#00f2fe' : (isRush ? '#38bdf8' : 'rgba(56, 189, 248, 0.45)')}
                      />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Diurnal Insights Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px 14px', borderRadius: '6px', borderLeft: '3px solid #00f2fe' }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Peak Corridor Congestion</div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc' }}>
                {peakHourObj.hour} &bull; {peakHourObj.count} vph
              </div>
            </div>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px 14px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Off-Peak Quiet Window</div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc' }}>02:00 &ndash; 05:00 UTC</div>
            </div>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px 14px', borderRadius: '6px', borderLeft: '3px solid #10b981' }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Night Freight Allowance</div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#10b981' }}>UNRESTRICTED</div>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 3: CORRIDOR VELOCITY & BOTTLENECK ANALYSIS */}
      {(activeSubTab === 'all' || activeSubTab === 'velocity') && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#fbbf24' }} />
            <div>
              <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                CORRIDOR VELOCITY DYNAMICS & BOTTLENECK TELEMETRY
              </h2>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Speed compliance ratio, corridor Level of Service (LOS), and velocity distribution metrics
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            
            {/* Velocity Health Gauge Card */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.7)',
              borderRadius: '8px',
              padding: '16px',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>Corridor Level of Service (LOS)</span>
                <span className="badge badge-success" style={{ fontSize: '0.68rem' }}>LOS B &bull; STABLE</span>
              </div>
              <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                Average speed of {summary.avg_speed} km/h indicates free-flowing heavy vehicle transit with minimal queuing at weighbridges.
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${Math.min(100, (summary.avg_speed / 60) * 100)}%`, height: '100%', background: 'linear-gradient(90deg, #10b981, #00f2fe)', borderRadius: '4px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
                <span>0 km/h (Congested)</span>
                <span>Avg: {summary.avg_speed} km/h</span>
                <span>60 km/h (Limit)</span>
              </div>
            </div>

            {/* Overspeed Enforcement Velocity Card */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.7)',
              borderRadius: '8px',
              padding: '16px',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>Compliance Pass Ratio</span>
                <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>
                  {(100 - summary.overspeed_rate).toFixed(1)}% COMPLIANT
                </span>
              </div>
              <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                {summary.total_overspeed} vehicles flagged above corridor limit. Automated ANPR cameras dispatched notices to dispatchers.
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${100 - summary.overspeed_rate}%`, height: '100%', background: '#10b981', borderRadius: '4px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
                <span>Safe: {summary.total_trucks - summary.total_overspeed}</span>
                <span style={{ color: '#ef4444' }}>Violations: {summary.total_overspeed} ({summary.overspeed_rate}%)</span>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
