import React, { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  Mail,
  Eye,
  EyeOff,
  Truck,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Fingerprint,
  UserCheck,
  UserPlus,
  Building,
  Badge,
  Phone,
  User,
  LogIn
} from 'lucide-react';
import { api } from '../services/api';
import { soundAlert } from '../services/soundAlert';

export default function Login({ onLoginSuccess }) {
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  const [roleMode, setRoleMode] = useState('Admin'); // 'Admin' or 'Manager'

  // Login fields
  const [email, setEmail] = useState('admin@visionhaul.ai');
  const [password, setPassword] = useState('admin');

  // Registration / Profile creation fields
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [regRole, setRegRole] = useState('Admin');
  const [regDepartment, setRegDepartment] = useState('National Heavy Transport Security Command');
  const [regBadgeId, setRegBadgeId] = useState('');
  const [regPhone, setRegPhone] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  const handleRoleTab = (role) => {
    setRoleMode(role);
    setErrorMsg('');
    setSuccessMsg('');
    if (role === 'Admin') {
      setEmail('admin@visionhaul.ai');
      setPassword('admin');
    } else {
      setEmail('manager@visionhaul.ai');
      setPassword('manager');
    }
  };

  const handleLoginSubmit = async (e) => {
    if (e) e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setLoading(true);
    setIsScanning(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      const res = await api.login(email, password);

      localStorage.setItem('visionhaul_token', res.token);
      localStorage.setItem('visionhaul_user', JSON.stringify(res.user));

      soundAlert.playWarningBeep();
      onLoginSuccess(res.user);
    } catch (err) {
      setErrorMsg(err.message || 'Security Authentication Failed');
      soundAlert.playSiren(1.2);
    } finally {
      setLoading(false);
      setIsScanning(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (regPassword !== regConfirmPassword) {
      setErrorMsg('Passwords do not match. Please verify your passphrase.');
      return;
    }

    setLoading(true);
    setIsScanning(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 600));
      const res = await api.register({
        name: regName,
        email: regEmail,
        password: regPassword,
        role: regRole,
        department: regDepartment,
        badge_id: regBadgeId,
        phone: regPhone
      });

      localStorage.setItem('visionhaul_token', res.token);
      localStorage.setItem('visionhaul_user', JSON.stringify(res.user));

      setSuccessMsg(`Officer Profile Created: ${res.user.name} (${res.user.badge_id})`);
      soundAlert.playWarningBeep();

      setTimeout(() => {
        onLoginSuccess(res.user);
      }, 500);

    } catch (err) {
      setErrorMsg(err.message || 'Failed to create officer profile');
      soundAlert.playSiren(1.2);
    } finally {
      setLoading(false);
      setIsScanning(false);
    }
  };

  const handleQuickLogin = (role) => {
    setAuthMode('login');
    if (role === 'Admin') {
      setEmail('admin@visionhaul.ai');
      setPassword('admin');
      setRoleMode('Admin');
    } else {
      setEmail('manager@visionhaul.ai');
      setPassword('manager');
      setRoleMode('Manager');
    }
    setTimeout(() => {
      handleLoginSubmit();
    }, 100);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px',
      position: 'relative',
      background: 'radial-gradient(circle at 50% 25%, #0f1c3f 0%, #070a12 65%, #020408 100%)'
    }}>

      {/* Background Cyber Grid Lines */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundImage: 'linear-gradient(to right, rgba(56, 189, 248, 0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(56, 189, 248, 0.04) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
        pointerEvents: 'none'
      }} />

      {/* Main Container Card */}
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: authMode === 'register' ? '540px' : '460px',
        padding: '32px',
        borderRadius: '16px',
        border: '1px solid rgba(0, 242, 254, 0.3)',
        boxShadow: '0 0 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 242, 254, 0.15)',
        position: 'relative',
        zIndex: 10,
        transition: 'max-width 0.3s ease'
      }}>

        {/* Top Header Logo */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 10px',
            boxShadow: '0 0 24px rgba(0, 242, 254, 0.5)'
          }}>
            <Truck size={30} color="#030712" />
          </div>

          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', margin: '0 0 4px', color: '#f8fafc' }}>
            DEMO<span style={{ color: '#00f2fe' }}></span> AI
          </h1>
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
            Heavy Vehicle Surveillance & Logistics Command Center
          </p>
        </div>

        {/* Auth Mode Toggle: Sign In vs Create Profile */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid rgba(56, 189, 248, 0.2)',
          marginBottom: '20px'
        }}>
          <button
            type="button"
            onClick={() => { setAuthMode('login'); setErrorMsg(''); setSuccessMsg(''); }}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              borderBottom: authMode === 'login' ? '2px solid #00f2fe' : '2px solid transparent',
              color: authMode === 'login' ? '#00f2fe' : '#64748b',
              padding: '10px',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <LogIn size={15} /> Sign In
          </button>

          <button
            type="button"
            onClick={() => { setAuthMode('register'); setErrorMsg(''); setSuccessMsg(''); }}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              borderBottom: authMode === 'register' ? '2px solid #00f2fe' : '2px solid transparent',
              color: authMode === 'register' ? '#00f2fe' : '#64748b',
              padding: '10px',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <UserPlus size={15} /> Create Officer Profile
          </button>
        </div>

        {/* Messages */}
        {errorMsg && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            padding: '10px 12px',
            borderRadius: '8px',
            color: '#f87171',
            fontSize: '0.78rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.5)',
            padding: '10px 12px',
            borderRadius: '8px',
            color: '#34d399',
            fontSize: '0.78rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* MODE 1: LOGIN PORTAL */}
        {authMode === 'login' && (
          <div>
            {/* Role Quick Selector */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '6px',
              background: 'rgba(15, 23, 42, 0.8)',
              padding: '4px',
              borderRadius: '10px',
              marginBottom: '16px',
              border: '1px solid rgba(56, 189, 248, 0.2)'
            }}>
              <button
                type="button"
                onClick={() => handleRoleTab('Admin')}
                style={{
                  background: roleMode === 'Admin' ? 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)' : 'transparent',
                  color: roleMode === 'Admin' ? '#030712' : '#94a3b8',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <ShieldCheck size={15} /> ADMIN PORTAL
              </button>

              <button
                type="button"
                onClick={() => handleRoleTab('Manager')}
                style={{
                  background: roleMode === 'Manager' ? 'linear-gradient(135deg, #0284c7 0%, #00f2fe 100%)' : 'transparent',
                  color: roleMode === 'Manager' ? '#030712' : '#94a3b8',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <UserCheck size={15} /> MANAGER PORTAL
              </button>
            </div>

            <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, marginBottom: '6px' }}>
                  OFFICER EMAIL ADDRESS
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="officer@visionhaul.ai"
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '10px 12px 10px 38px',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '0.85rem'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, marginBottom: '6px' }}>
                  SECURITY PASSPHRASE
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter passphrase"
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '10px 38px 10px 38px',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '0.85rem'
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '10px',
                      top: '10px',
                      background: 'transparent',
                      border: 'none',
                      color: '#64748b',
                      cursor: 'pointer'
                    }}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-cyber-primary"
                style={{
                  padding: '12px',
                  fontSize: '0.9rem',
                  justifyContent: 'center',
                  marginTop: '8px'
                }}
              >
                {isScanning ? (
                  <>
                    <Fingerprint size={18} className="animate-pulse-glow" />
                    <span>Verifying Security Clearance...</span>
                  </>
                ) : (
                  <>
                    <KeyRound size={18} />
                    <span>Authenticate & Access Command Center</span>
                  </>
                )}
              </button>
            </form>

            {/* 1-Click Quick Demo Login */}
            <div style={{
              marginTop: '20px',
              paddingTop: '14px',
              borderTop: '1px solid rgba(56, 189, 248, 0.15)',
              textAlign: 'center'
            }}>
              <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>
                QUICK ACCESS DEMO ACCOUNTS:
              </span>
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('Admin')}
                  className="btn-cyber-outline"
                  style={{ flex: 1, fontSize: '0.75rem', padding: '6px', justifyContent: 'center' }}
                >
                  👑 Login as Admin
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('Manager')}
                  className="btn-cyber-outline"
                  style={{ flex: 1, fontSize: '0.75rem', padding: '6px', justifyContent: 'center' }}
                >
                  📋 Login as Manager
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODE 2: CREATE OFFICER PROFILE / REGISTER */}
        {authMode === 'register' && (
          <form onSubmit={handleRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

            {/* Role Radio Selection */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, marginBottom: '6px' }}>
                OFFICER ROLE & CLEARANCE LEVEL
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div
                  onClick={() => {
                    setRegRole('Admin');
                    setRegDepartment('National Heavy Transport Security Command');
                  }}
                  style={{
                    background: regRole === 'Admin' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(15, 23, 42, 0.8)',
                    border: `1px solid ${regRole === 'Admin' ? '#ef4444' : 'rgba(56, 189, 248, 0.2)'}`,
                    padding: '10px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '0.82rem', color: regRole === 'Admin' ? '#f87171' : '#f8fafc' }}>
                    <ShieldCheck size={16} /> Security Admin
                  </div>
                  <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                    Level 5: Full Calibration, Speed Limits & System Settings
                  </span>
                </div>

                <div
                  onClick={() => {
                    setRegRole('Manager');
                    setRegDepartment('Port & Highway Logistics Operations');
                  }}
                  style={{
                    background: regRole === 'Manager' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(15, 23, 42, 0.8)',
                    border: `1px solid ${regRole === 'Manager' ? '#38bdf8' : 'rgba(56, 189, 248, 0.2)'}`,
                    padding: '10px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '0.82rem', color: regRole === 'Manager' ? '#38bdf8' : '#f8fafc' }}>
                    <UserCheck size={16} /> Logistics Manager
                  </div>
                  <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                    Level 3: Live CCTV HUD, Incidents, History & Analytics
                  </span>
                </div>
              </div>
            </div>

            {/* Full Name & Official Email */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                  OFFICER FULL NAME
                </label>
                <div style={{ position: 'relative' }}>
                  <User size={15} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                  <input
                    type="text"
                    required
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    placeholder="e.g. Maya Patel"
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '8px 10px 8px 32px',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                  OFFICIAL EMAIL
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={15} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="officer@agency.gov"
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '8px 10px 8px 32px',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Department & Badge ID */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                  DEPARTMENT / UNIT
                </label>
                <div style={{ position: 'relative' }}>
                  <Building size={15} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                  <input
                    type="text"
                    value={regDepartment}
                    onChange={(e) => setRegDepartment(e.target.value)}
                    placeholder="Logistics Operations"
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      padding: '8px 10px 8px 32px',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                  BADGE ID (OPTIONAL)
                </label>
                <input
                  type="text"
                  value={regBadgeId}
                  onChange={(e) => setRegBadgeId(e.target.value.toUpperCase())}
                  placeholder="e.g. SEC-08"
                  style={{
                    width: '100%',
                    background: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.82rem',
                    fontFamily: 'JetBrains Mono, monospace'
                  }}
                />
              </div>
            </div>

            {/* Passphrase & Confirm */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                  CREATE PASSPHRASE
                </label>
                <input
                  type="password"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Passphrase"
                  style={{
                    width: '100%',
                    background: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.82rem'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
                  CONFIRM PASSPHRASE
                </label>
                <input
                  type="password"
                  required
                  value={regConfirmPassword}
                  onChange={(e) => setRegConfirmPassword(e.target.value)}
                  placeholder="Confirm passphrase"
                  style={{
                    width: '100%',
                    background: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.82rem'
                  }}
                />
              </div>
            </div>

            {/* Submit Create Profile */}
            <button
              type="submit"
              disabled={loading}
              className="btn-cyber-primary"
              style={{
                padding: '11px',
                fontSize: '0.88rem',
                justifyContent: 'center',
                marginTop: '8px'
              }}
            >
              {isScanning ? (
                <>
                  <Fingerprint size={17} className="animate-pulse-glow" />
                  <span>Enrolling Officer Security Profile...</span>
                </>
              ) : (
                <>
                  <UserPlus size={17} />
                  <span>Register Profile & Enter Command Center</span>
                </>
              )}
            </button>

            <div style={{ textAlign: 'center', marginTop: '4px' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                Already have an officer account?{' '}
                <button
                  type="button"
                  onClick={() => setAuthMode('login')}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#00f2fe',
                    fontWeight: 600,
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Sign In here
                </button>
              </span>
            </div>

          </form>
        )}

      </div>

    </div>
  );
}
