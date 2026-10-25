import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/Layout';

// ── Pages ────────────────────────────────────────────────────────────────────
import SplashScreen from './pages/SplashScreen';
import Onboarding from './pages/Onboarding';
import HomeDashboard from './pages/HomeDashboard';
import PackagingRecommender from './pages/PackagingRecommender';
import VisionScanner from './pages/VisionScanner';
import ReverseLogistics from './pages/ReverseLogistics';
import TrashGPT from './pages/TrashGPT';
import EcoPointsDashboard from './pages/EcoPointsDashboard';
import PackagingSimulator from './pages/PackagingSimulator';
import ReviewAnalyzer from './pages/ReviewAnalyzer';
import EcoShop from './pages/EcoShop';
import AdminDashboard from './pages/AdminDashboard';
import SustainabilityInsights from './pages/SustainabilityInsights';
import ProfilePage from './pages/ProfilePage';

/**
 * ScrollToTop — ensures page scroll resets on route changes
 * (important for mobile native-feel navigation)
 */
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);
  return null;
}

function App() {
  return (
    <Router>
      <ScrollToTop />
      <Layout>
        <Routes>
          {/* ── Onboarding Flow ─────────────────────────────────── */}
          <Route path="/splash" element={<SplashScreen />} />
          <Route path="/onboarding" element={<Onboarding />} />

          {/* ── Main App Screens ─────────────────────────────────── */}
          <Route path="/" element={<HomeDashboard />} />
          <Route path="/packaging" element={<PackagingRecommender />} />
          <Route path="/scanner" element={<VisionScanner />} />
          <Route path="/simulator" element={<PackagingSimulator />} />
          <Route path="/sustainability" element={<SustainabilityInsights />} />
          <Route path="/logistics" element={<ReverseLogistics />} />
          <Route path="/dashboard" element={<EcoPointsDashboard />} />
          <Route path="/chatbot" element={<TrashGPT />} />
          <Route path="/analyzer" element={<ReviewAnalyzer />} />
          <Route path="/shop" element={<EcoShop />} />
          <Route path="/eco-shop" element={<EcoShop />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/profile" element={<ProfilePage />} />

          {/* ── Fallback ─────────────────────────────────────────── */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;