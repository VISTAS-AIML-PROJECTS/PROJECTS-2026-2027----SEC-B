import React, { useState, useEffect } from 'react';
import { Package, Leaf, TrendingUp } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { getDashboardStats } from '../utils/api';

const AdminDashboard = () => {
  const [stats, setStats]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch((err) =>
        setError(
          err.message.includes('Failed to fetch')
            ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
            : err.message,
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Loading admin dashboard…
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <strong>Dashboard unavailable:</strong> {error}
      </div>
    );
  }

  const materialChartData = (stats.material_distribution || []).map((d) => ({
    name: d.class,
    count: d.count,
  }));

  const statusChartData = Object.entries(stats.recommendation_statuses || {}).map(
    ([status, count]) => ({ status, count }),
  );

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">🧾 Admin Dashboard</h1>
          <p className="text-gray-600">
            Real application usage statistics from the backend database.
          </p>
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card text-center">
          <Package className="h-12 w-12 text-blue-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-blue-600">
            {stats.total_recommendations.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Recommendations</div>
        </div>

        <div className="card text-center">
          <Leaf className="h-12 w-12 text-green-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-green-600">
            {stats.total_material_scans.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Material Scans</div>
        </div>

        <div className="card text-center">
          <TrendingUp className="h-12 w-12 text-purple-500 mx-auto mb-3" />
          <div className="text-3xl font-bold text-purple-600">
            {stats.total_review_analyses.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Review Analyses</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Material distribution */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Material Classification Distribution</h2>
          {materialChartData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              No material scans recorded yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={materialChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recommendation status */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Recommendation Status Breakdown</h2>
          {statusChartData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              No recommendations recorded yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={statusChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card mt-8">
        <p className="text-sm text-gray-500">{stats.note}</p>
        <p className="text-xs text-gray-400 mt-2">
          Per-seller analytics, CO₂ savings tracking, and implementation rate require a user
          authentication system and per-event CO₂ attribution, which are not yet implemented.
        </p>
      </div>
    </div>
  );
};

export default AdminDashboard;
