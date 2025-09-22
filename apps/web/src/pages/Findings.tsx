import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Filter, Eye, EyeOff, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

import FindingsTable from '../components/FindingsTable';
import StatCard from '../components/StatCard';
import SeverityBadge from '../components/SeverityBadge';
import { getScanStatus, getFindings, getScanStatistics, exportFindings } from '../lib/api';
import type { ScanJob, Finding, ScanStatistics } from '../types';

export default function Findings() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  
  const [scan, setScan] = useState<ScanJob | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [statistics, setStatistics] = useState<ScanStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [showSecrets, setShowSecrets] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    if (jobId) {
      loadScanData();
    }
  }, [jobId, page, selectedSeverity, selectedType]);

  const loadScanData = async () => {
    if (!jobId) return;

    try {
      const [scanResponse, findingsResponse, statsResponse] = await Promise.all([
        getScanStatus(jobId),
        getFindings(jobId, page, 20, selectedSeverity, selectedType),
        getScanStatistics(jobId)
      ]);

      setScan(scanResponse);
      setFindings(findingsResponse.findings);
      setTotalPages(findingsResponse.pagination.pages);
      setStatistics(statsResponse);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load scan data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadScanData();
  };

  const handleExport = async (format: 'json' | 'csv') => {
    if (!jobId) return;

    try {
      const response = await exportFindings(jobId, format);
      
      if (format === 'csv') {
        // Create and download CSV file
        const blob = new Blob([response.content], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.filename || `secrethawk-findings-${jobId}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        // Create and download JSON file
        const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `secrethawk-findings-${jobId}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }

      toast.success(`Findings exported as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(error.message || 'Export failed');
    }
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

  if (!scan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Scan not found</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Return to Dashboard
        </button>
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
        <div className="flex items-center">
          <button
            onClick={() => navigate('/')}
            className="mr-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Scan Results</h1>
            <div className="flex items-center space-x-4 mt-2">
              <p className="text-gray-600">{scan.filename}</p>
              <SeverityBadge severity={scan.status} />
              <span className="text-sm text-gray-500">
                {new Date(scan.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>

          <div className="relative">
            <button className="flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            <div className="absolute right-0 top-full mt-2 bg-white shadow-lg rounded-lg border py-2 hidden group-hover:block">
              <button
                onClick={() => handleExport('json')}
                className="block px-4 py-2 hover:bg-gray-50 w-full text-left"
              >
                Export as JSON
              </button>
              <button
                onClick={() => handleExport('csv')}
                className="block px-4 py-2 hover:bg-gray-50 w-full text-left"
              >
                Export as CSV
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Statistics */}
      {statistics && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          <StatCard
            title="Total Findings"
            value={statistics.total_findings}
            color="blue"
          />
          <StatCard
            title="Critical"
            value={statistics.by_severity.critical || 0}
            color="red"
          />
          <StatCard
            title="High"
            value={statistics.by_severity.high || 0}
            color="orange"
          />
          <StatCard
            title="Files Scanned"
            value={statistics.files_scanned}
            color="green"
          />
        </motion.div>
      )}

      {/* Filters and Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-lg shadow-sm p-6"
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <Filter className="w-5 h-5 text-gray-400 mr-2" />
              <span className="font-medium text-gray-700">Filters:</span>
            </div>

            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Types</option>
              <option value="aws_access_key">AWS Access Key</option>
              <option value="github_token">GitHub Token</option>
              <option value="stripe_key">Stripe Key</option>
              <option value="jwt_token">JWT Token</option>
              <option value="private_key">Private Key</option>
            </select>
          </div>

          <button
            onClick={() => setShowSecrets(!showSecrets)}
            className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
              showSecrets
                ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {showSecrets ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
            {showSecrets ? 'Hide Secrets' : 'Show Secrets'}
          </button>
        </div>
      </motion.div>

      {/* Findings Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-lg shadow-sm"
      >
        <FindingsTable 
          findings={findings} 
          showSecrets={showSecrets}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      </motion.div>
    </div>
  );
}