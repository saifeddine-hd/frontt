import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Shield,
  AlertTriangle,
  CheckCircle,
  Upload,
  FileSearch,
  Zap,
  TrendingUp,
  Activity
} from 'lucide-react';

import StatCard from '../components/StatCard';
import RecentScansTable from '../components/RecentScansTable';
import { getDashboardStats, getRecentScans } from '../lib/api';
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
    const loadDashboardData = async () => {
      try {
        // Load dashboard stats and recent scans
        const [statsResponse, scansResponse] = await Promise.all([
          getDashboardStats(),
          getRecentScans(10)
        ]);

        // Update stats
        if (statsResponse.success) {
          setStats({
            totalScans: statsResponse.data.total_scans,
            criticalFindings: statsResponse.data.critical_findings,
            pendingScans: statsResponse.data.running_scans,
            completedScans: statsResponse.data.completed_scans
          });
        }

        // Update recent scans
        if (scansResponse.success) {
          const formattedScans = scansResponse.data.map((scan: any) => ({
            id: scan.id,
            filename: scan.filename,
            status: scan.status,
            created_at: scan.created_at,
            completed_at: scan.completed_at,
            findings_count: scan.findings_count,
            error: scan.error
          }));
          setRecentScans(formattedScans);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const handleStartScan = () => navigate('/scan');

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
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
      >
        <div className="space-y-2">
          <motion.h1
            className="text-4xl font-bold text-gradient-primary"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            Dashboard
          </motion.h1>
          <motion.p
            className="text-neutral-600 text-lg"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            Monitor your secret scanning activities with real-time insights
          </motion.p>
        </div>

        <motion.button
          onClick={handleStartScan}
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, duration: 0.6, type: 'spring', bounce: 0.3 }}
          className="btn btn-primary btn-lg group shadow-xl hover:shadow-2xl"
        >
          <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
          <span>New Scan</span>
          <Zap className="w-4 h-4 ml-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </motion.button>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <StatCard
          title="Total Scans"
          value={stats.totalScans}
          icon={<FileSearch />}
          color="blue"
          trend={12}
        />
        <StatCard
          title="Critical Findings"
          value={stats.criticalFindings}
          icon={<AlertTriangle />}
          color="red"
          trend={-5}
        />
        <StatCard
          title="Running Scans"
          value={stats.pendingScans}
          icon={<Activity />}
          color="yellow"
        />
        <StatCard
          title="Completed"
          value={stats.completedScans}
          icon={<CheckCircle />}
          color="green"
          trend={8}
        />
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.6 }}
        className="card p-8"
      >
        <motion.h2
          className="text-2xl font-bold text-neutral-900 mb-6 flex items-center"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Zap className="w-6 h-6 text-primary-500 mr-2" />
          Quick Actions
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <motion.button
            onClick={handleStartScan}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="p-6 card hover:shadow-xl transition-all duration-300 text-left group border-2 border-transparent hover:border-primary-200"
          >
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                <Upload className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-bold text-neutral-900 text-lg">Upload & Scan</h3>
            </div>
            <p className="text-neutral-600">
              Upload a ZIP file and start scanning for secrets with our advanced detection engine
            </p>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="p-6 card hover:shadow-xl transition-all duration-300 text-left group border-2 border-transparent hover:border-green-200"
          >
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-bold text-neutral-900 text-lg">Security Report</h3>
            </div>
            <p className="text-neutral-600">
              View comprehensive security analysis and detailed vulnerability reports
            </p>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
            className="p-6 card hover:shadow-xl transition-all duration-300 text-left group border-2 border-transparent hover:border-purple-200"
          >
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-violet-500 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300">
                <FileSearch className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-bold text-neutral-900 text-lg">Browse Findings</h3>
            </div>
            <p className="text-neutral-600">
              Explore detailed scan results and findings with advanced filtering options
            </p>
          </motion.button>
        </div>
      </motion.div>

      {/* Recent Scans */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="card-elevated"
      >
        <div className="px-8 py-6 border-b border-neutral-100">
          <motion.h2
            className="text-2xl font-bold text-neutral-900 flex items-center"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.8 }}
          >
            <TrendingUp className="w-6 h-6 text-primary-500 mr-2" />
            Recent Scans
          </motion.h2>
        </div>

        <RecentScansTable scans={recentScans} />
      </motion.div>
    </div>
  );
}
