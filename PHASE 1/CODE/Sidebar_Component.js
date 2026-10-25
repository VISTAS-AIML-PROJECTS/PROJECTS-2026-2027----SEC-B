import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Package, Camera, MapPin, MessageCircle, Trophy, Box, Star, ShoppingCart, BarChart3 } from 'lucide-react';

const Layout = ({ children }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Package, label: 'Recommender' },
    { path: '/scanner', icon: Camera, label: 'Scanner' },
    { path: '/logistics', icon: MapPin, label: 'Logistics' },
    { path: '/chatbot', icon: MessageCircle, label: 'TrashGPT' },
    { path: '/dashboard', icon: Trophy, label: 'EcoPoints' },
    { path: '/simulator', icon: Box, label: '3D Simulator' },
    { path: '/analyzer', icon: Star, label: 'Reviews' },
    { path: '/shop', icon: ShoppingCart, label: 'Eco Shop' },
    { path: '/admin', icon: BarChart3, label: 'Admin' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex">
      {/* Left Sidebar */}
      <div className="w-64 bg-white shadow-lg border-r border-green-100 fixed h-full z-10">
        <div className="p-6 border-b border-green-100">
          <Link to="/" className="flex items-center space-x-3">
            <Package className="h-8 w-8 text-green-600" />
            <span className="text-xl font-bold text-green-800">Wrapture</span>
          </Link>
        </div>
        <nav className="p-4">
          <div className="space-y-2">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  location.pathname === path
                    ? 'bg-green-100 text-green-700 shadow-sm'
                    : 'text-gray-600 hover:text-green-600 hover:bg-green-50'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{label}</span>
              </Link>
            ))}
          </div>
        </nav>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 ml-64">
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;