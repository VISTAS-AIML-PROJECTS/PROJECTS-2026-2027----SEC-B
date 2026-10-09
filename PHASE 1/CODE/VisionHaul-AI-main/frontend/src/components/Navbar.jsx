import React, { useState, useEffect } from 'react';
import {
  Video,
  Bell,
  Clock,
  BarChart3,
  TrendingUp,
  ShieldAlert,
  Settings,
  Volume2,
  VolumeX,
  Radio,
  Truck,
  LogOut,
  User,
  ShieldCheck,
  Brain,
  FileCheck2
} from 'lucide-react';
import { soundAlert } from '../services/soundAlert';

export default function Navbar({ activeTab, setActiveTab, unreadAlertsCount, currentUser, onLogout }) {
  const [currentTime, setCurrentTime] = useState('');
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleSound = () => {
    const newMute = !isMuted;
    setIsMuted(newMute);
    soundAlert.setMuted(newMute);
    if (!newMute) {
      soundAlert.playWarningBeep();
    }
  };

  const isAdmin = currentUser?.role === 'Admin';

  const allNavItems = [
    { id: 'live', label: 'Live CCTV HUD', icon: Video },
    {
      id: 'alerts',
      label: 'Alerts & Siren',
      icon: ShieldAlert,
      badge: unreadAlertsCount > 0 ? unreadAlertsCount : null,
      badgeColor: 'badge-danger'
    },
    { id: 'fc', label: 'FC & Police Action', icon: FileCheck2 },
    { id: 'history', label: 'History & Cargo', icon: Clock },
    { id: 'dataset', label: 'AI Training & Images', icon: Brain },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'stats', label: 'Stats', icon: BarChart3 },
    { id: 'blocklist', label: 'Watchlist / Blocklist', icon: ShieldAlert },
    { id: 'settings', label: 'Calibration & Config', icon: Settings, adminOnly: true }
  ];


  const navItems = allNavItems.filter(item => !item.adminOnly || isAdmin);

  return (
    <header className="glass-panel" style={{
      margin: '12px 16px',
      padding: '10px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: '12px',
      zIndex: 100,
      borderBottom: '1px solid rgba(0, 242, 254, 0.25)'
    }}>
      {/* Brand & System Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px rgba(0, 242, 254, 0.4)'
        }}>
          <Truck size={24} color="#030712" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              DEMO<span style={{ color: '#00f2fe' }}></span>
            </span>
            <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>AI TRUCK C2</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#94a3b8' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }} className="animate-pulse-glow" />
            <span>YOLOv26 • ByteTrack • PaddleOCR • MTL-ViT</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                background: isActive ? 'rgba(0, 242, 254, 0.15)' : 'transparent',
                border: isActive ? '1px solid rgba(0, 242, 254, 0.5)' : '1px solid transparent',
                color: isActive ? '#00f2fe' : '#94a3b8',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.18s ease',
                position: 'relative'
              }}
            >
              <Icon size={16} color={isActive ? '#00f2fe' : '#94a3b8'} />
              <span>{item.label}</span>
              {item.badge && (
                <span className="badge badge-danger" style={{ fontSize: '0.65rem', padding: '1px 6px', borderRadius: '10px' }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Right Controls: User Profile Badge, Clock, Siren Toggle & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>

        {/* User Role Badge */}
        {currentUser && (
          <div style={{
            background: 'rgba(15, 23, 42, 0.7)',
            border: `1px solid ${isAdmin ? 'rgba(239, 68, 68, 0.4)' : 'rgba(56, 189, 248, 0.4)'}`,
            padding: '5px 10px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <div style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              backgroundColor: isAdmin ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {isAdmin ? <ShieldCheck size={14} color="#ef4444" /> : <User size={14} color="#38bdf8" />}
            </div>
            <div style={{ lineHeight: 1.1 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f8fafc' }}>
                {currentUser.name ? currentUser.name.split(' ')[0] : 'Officer'}
              </div>
              <span className={`badge ${isAdmin ? 'badge-danger' : 'badge-info'}`} style={{ fontSize: '0.58rem', padding: '0 4px' }}>
                {currentUser.role?.toUpperCase()}
              </span>
            </div>
          </div>
        )}

        {/* UTC Live Clock */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          padding: '6px 10px',
          borderRadius: '6px',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          fontSize: '0.75rem',
          fontFamily: 'JetBrains Mono, monospace',
          color: '#cbd5e1',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <Radio size={13} color="#00f2fe" className="animate-pulse-glow" />
          <span>{currentTime}</span>
        </div>

        {/* Audio Siren Toggle */}
        <button
          onClick={toggleSound}
          title={isMuted ? 'Unmute Audio Siren' : 'Mute Audio Siren'}
          className="btn-cyber-outline"
          style={{
            padding: '6px 10px',
            borderColor: isMuted ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)',
            color: isMuted ? '#f87171' : '#34d399'
          }}
        >
          {isMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
        </button>

        {/* Logout Button */}
        {onLogout && (
          <button
            onClick={onLogout}
            title="Log Out of Security Session"
            className="btn-cyber-outline"
            style={{
              padding: '6px 10px',
              borderColor: 'rgba(239, 68, 68, 0.3)',
              color: '#f87171'
            }}
          >
            <LogOut size={15} />
            <span style={{ fontSize: '0.75rem' }}>Logout</span>
          </button>
        )}
      </div>
    </header>
  );
}
