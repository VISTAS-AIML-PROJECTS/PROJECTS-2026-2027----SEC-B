import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import LiveHUD from './components/LiveHUD';
import AlertsCenter from './components/AlertsCenter';
import FCEnforcementManager from './components/FCEnforcementManager';
import VehicleHistory from './components/VehicleHistory';
import DatasetTrainingStudio from './components/DatasetTrainingStudio';
import Analytics from './components/Analytics';
import Stats from './components/Stats';
import BlocklistManager from './components/BlocklistManager';
import SystemSettings from './components/SystemSettings';
import Login from './components/Login';
import { api } from './services/api';
import { soundAlert } from './services/soundAlert';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('visionhaul_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState('live');
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);
  const [selectedTruckForDetail, setSelectedTruckForDetail] = useState(null);
  const lastAlertIdRef = useRef(null);

  // Global Alert Poller for Real-Time Siren Alarms (only when logged in)
  const checkAlerts = async () => {
    if (!currentUser) return;
    try {
      const data = await api.getRecentAlerts();
      const count = data.unacknowledged_count || 0;
      setUnreadAlertsCount(count);

      if (data.recent_alerts && data.recent_alerts.length > 0) {
        const newest = data.recent_alerts[0];
        if (lastAlertIdRef.current !== null && newest.id > lastAlertIdRef.current) {
          // New alert arrived -> trigger siren audio!
          if (newest.severity === 'CRITICAL' || newest.severity === 'HIGH') {
            soundAlert.playSiren(2.2);
          } else {
            soundAlert.playWarningBeep();
          }
        }
        lastAlertIdRef.current = newest.id;
      }
    } catch (e) {
      // Silently retry
    }
  };

  useEffect(() => {
    if (currentUser) {
      checkAlerts();
      const interval = setInterval(checkAlerts, 2500);
      return () => clearInterval(interval);
    }
  }, [currentUser]);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setActiveTab('live');
  };

  const handleLogout = () => {
    localStorage.removeItem('visionhaul_token');
    localStorage.removeItem('visionhaul_user');
    setCurrentUser(null);
    setActiveTab('live');
  };

  const handleSelectTruck = (truck) => {
    setSelectedTruckForDetail(truck);
    setActiveTab('history');
  };

  // If not logged in, render dedicated Admin/Manager Login Portal
  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Sticky Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        unreadAlertsCount={unreadAlertsCount}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Main Viewport Content */}
      <main style={{ flex: 1 }}>
        {activeTab === 'live' && (
          <LiveHUD onSelectTruck={handleSelectTruck} />
        )}
        {activeTab === 'alerts' && (
          <AlertsCenter onAlertAcknowledged={checkAlerts} />
        )}
        {activeTab === 'fc' && (
          <FCEnforcementManager />
        )}
        {activeTab === 'history' && (
          <VehicleHistory
            selectedTruck={selectedTruckForDetail}
            onCloseDetail={() => setSelectedTruckForDetail(null)}
          />
        )}
        {activeTab === 'dataset' && (
          <DatasetTrainingStudio />
        )}
        {activeTab === 'analytics' && (
          <Analytics />
        )}
        {activeTab === 'stats' && (
          <Stats />
        )}
        {activeTab === 'blocklist' && (
          <BlocklistManager />
        )}
        {activeTab === 'settings' && currentUser.role === 'Admin' && (
          <SystemSettings />
        )}
      </main>


      {/* Modern Status Bar Footer */}
      <footer style={{
        padding: '12px 20px',
        borderTop: '1px solid rgba(56, 189, 248, 0.15)',
        background: 'rgba(7, 10, 18, 0.95)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        color: '#64748b'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: '#00f2fe', fontWeight: 600 }}>DEMO v2.6.0</span>
          <span>&bull;</span>
          <span>Security Clearance: {currentUser.clearance}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            Flask REST API: ONLINE
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#00f2fe' }} />
            Officer: {currentUser.name} ({currentUser.badge_id})
          </span>
        </div>
      </footer>
    </div>
  );
}
