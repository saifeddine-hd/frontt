import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Plus, Shield, AlertTriangle, Clock, CheckCircle, Upload, FileSearch } from 'lucide-react';

import StatCard from '../components/StatCard';
import RecentScansTable from '../components/RecentScansTable';
import { getRecentScans } from '../lib/api';
import type { ScanJob } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();
  const [recentScans, setRecentScans] = useState<ScanJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalScans: 0,
    criticalFindings: 0,
    pendingScans: 0,
    completedScans: 0
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Mock data for now - in real implementation, fetch from API
      const mockScans: ScanJob[] = [
        {
          id: '1',
          filename: 'frontend-app.zip',
          status: 'completed',
          created_at: new Date('2024-01-15T10:30:00'),
          completed_at: new Date('2024-01-15T10:32:15'),
          findings_count: 3
        },
        {
          id: '2',
          filename: 'backend-api.zip',
          status: 'running',
          created_at: new Date('2024-01-15T11:00:00'),
          findings_count: null
        },
        {
          id: '3',
          filename: 'mobile-app.zip',
          status: 'completed',
          created_at: new Date('2024-01-14T15:20:00'),
          completed_at: new Date('2024-01-14T15:23:45'),
          findings_count: 0
        }
      ];

      setRecentScans(mockScans);
      
      // Calculate stats
      const totalScans = mockScans.length;
      const criticalFindings = mockScans.reduce((sum, scan) => sum + (scan.findings_count || 0), 0);
      const pendingScans = mockScans.filter(scan => scan.status === 'pending' || scan.status === 'running').length;
      const completedScans = mockScans.filter(scan => scan.status === 'completed').length;

      setStats({
        totalScans,
        criticalFindings,
        pendingScans,
        completedScans
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartScan = () => {
    navigate('/scan');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Monitor your secret scanning activities</p>
        </div>
        
        <motion.button
          onClick={handleStartScan}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center space-x-2 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>New Scan</span>
        </motion.button>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <StatCard
          title="Total Scans"
          value={stats.totalScans}
          icon={<FileSearch className="w-6 h-6" />}
          color="blue"
          trend={+12}
        />
        
        <StatCard
          title="Critical Findings"
          value={stats.criticalFindings}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          trend={-5}
        />
        
        <StatCard
          title="Running Scans"
          value={stats.pendingScans}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
        />
        
        <StatCard
          title="Completed"
          value={stats.completedScans}
          icon={<CheckCircle className="w-6 h-6" />}
          color="green"
          trend={+8}
        />
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-lg shadow-sm p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <motion.button
            onClick={handleStartScan}
            whileHover={{ scale: 1.02 }}
            className="p-6 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all text-left"
          >
            <div className="flex items-center mb-3">
              <Upload className="w-8 h-8 text-blue-600 mr-3" />
              <h3 className="font-semibold text-gray-900">Upload & Scan</h3>
            </div>
            <p className="text-gray-600 text-sm">Upload a ZIP file and start scanning for secrets</p>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            className="p-6 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-md transition-all text-left"
          >
            <div className="flex items-center mb-3">
              <Shield className="w-8 h-8 text-green-600 mr-3" />
              <h3 className="font-semibold text-gray-900">Security Report</h3>
            </div>
            <p className="text-gray-600 text-sm">View comprehensive security analysis</p>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            className="p-6 border border-gray-200 rounded-lg hover:border-purple-300 hover:shadow-md transition-all text-left"
          >
            <div className="flex items-center mb-3">
              <FileSearch className="w-8 h-8 text-purple-600 mr-3" />
              <h3 className="font-semibold text-gray-900">Browse Findings</h3>
            </div>
            <p className="text-gray-600 text-sm">Explore detailed scan results and findings</p>
          </motion.button>
        </div>
      </motion.div>

      {/* Recent Scans */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-lg shadow-sm"
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Recent Scans</h2>
        </div>
        
        <RecentScansTable scans={recentScans} />
      </motion.div>
    </div>
  );
}