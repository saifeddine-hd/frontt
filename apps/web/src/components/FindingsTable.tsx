import React from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Eye, EyeOff, ExternalLink, FileText, AlertCircle } from 'lucide-react';

import SeverityBadge from './SeverityBadge';
import type { Finding } from '../types';

interface FindingsTableProps {
  findings: Finding[];
  showSecrets: boolean;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function FindingsTable({ 
  findings, 
  showSecrets, 
  page, 
  totalPages, 
  onPageChange 
}: FindingsTableProps) {
  const displaySecret = (secret: string, secretRedacted?: string) => {
    if (showSecrets) {
      return secret;
    }
    return secretRedacted || `${secret.slice(0, 4)}${'*'.repeat(Math.max(0, secret.length - 8))}${secret.slice(-4)}`;
  };

  if (findings.length === 0) {
    return (
      <motion.div 
        className="text-center py-16"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <motion.div
          className="w-20 h-20 bg-gradient-to-br from-green-100 to-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-6"
          animate={{ rotate: [0, 5, -5, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <Eye className="w-10 h-10 text-green-600" />
        </motion.div>
        <h3 className="text-2xl font-bold text-neutral-900 mb-3">All Clear!</h3>
        <p className="text-neutral-600 text-lg">No secrets were found in this scan. Your code is secure.</p>
      </motion.div>
    );
  }

  return (
    <div>
      {/* Table */}
      <div className="overflow-x-auto scrollbar-modern">
        <table className="table-modern">
          <thead>
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-neutral-600 uppercase tracking-wider">
                <div className="flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                File & Line
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-neutral-600 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-neutral-600 uppercase tracking-wider">
                <div className="flex items-center">
                  <AlertCircle className="w-4 h-4 mr-2" />
                Severity
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-neutral-600 uppercase tracking-wider">
                Secret
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-neutral-600 uppercase tracking-wider">
                Scanner
              </th>
            </tr>
          </thead>
          <tbody>
            {findings.map((finding, index) => (
              <motion.tr
                key={`${finding.id || index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                whileHover={{ scale: 1.01 }}
                className="group cursor-pointer"
              >
                <td className="px-6 py-5">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gradient-to-br from-neutral-100 to-neutral-200 rounded-lg flex items-center justify-center mr-3 group-hover:from-primary-100 group-hover:to-primary-200 transition-all duration-200">
                      <FileText className="w-4 h-4 text-neutral-600 group-hover:text-primary-600" />
                    </div>
                    <div>
                      <div className="font-semibold text-neutral-900 truncate max-w-xs group-hover:text-primary-700 transition-colors" title={finding.file_path}>
                      {finding.file_path.split('/').pop()}
                      </div>
                      <div className="text-neutral-500 text-sm">Line {finding.line_number}</div>
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-5">
                  <div className="text-sm font-semibold text-neutral-900">
                    {finding.secret_type.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div className="text-sm text-neutral-500 font-mono">{finding.rule_id}</div>
                </td>
                
                <td className="px-6 py-5">
                  <SeverityBadge severity={finding.severity} />
                </td>
                
                <td className="px-6 py-5">
                  <div className="flex items-center space-x-2">
                    <motion.code 
                      className={`text-sm px-3 py-2 rounded-lg font-mono max-w-xs truncate border transition-all duration-200 ${
                      showSecrets 
                        ? 'bg-red-50 text-red-800 border-red-200 shadow-sm' 
                        : 'bg-neutral-100 text-neutral-700 border-neutral-200'
                    }`}
                      whileHover={{ scale: 1.02 }}
                    >
                      {displaySecret(finding.secret)}
                    </motion.code>
                    {showSecrets && (
                      <motion.div 
                        className="text-xs text-orange-600 flex items-center bg-orange-50 px-2 py-1 rounded-full border border-orange-200"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.1 }}
                      >
                        <EyeOff className="w-3 h-3 mr-1" />
                        Visible
                      </motion.div>
                    )}
                  </div>
                </td>
                
                <td className="px-6 py-5">
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-2 ${
                      finding.scanner === 'gitleaks' ? 'bg-blue-400' : 'bg-green-400'
                    }`} />
                    <span className="capitalize font-medium text-neutral-700">{finding.scanner || 'regex'}</span>
                  </div>
                  {finding.confidence && (
                    <div className="text-xs text-neutral-500 mt-1">
                      {Math.round((finding.confidence || 0) * 100)}% confidence
                    </div>
                  )}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <motion.div 
          className="px-8 py-6 border-t border-neutral-100 bg-gradient-to-r from-neutral-50 to-white"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <div className="text-sm text-neutral-700 font-medium">
              Page {page} of {totalPages}
            </div>
            
            <div className="flex items-center space-x-2">
              <motion.button
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-3 rounded-xl border border-neutral-200 hover:bg-white hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <ChevronLeft className="w-4 h-4" />
              </motion.button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <motion.button
                    key={pageNum}
                    onClick={() => onPageChange(pageNum)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                      pageNum === page
                        ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-lg'
                        : 'border border-neutral-200 hover:bg-white hover:shadow-md text-neutral-700'
                    }`}
                  >
                    {pageNum}
                  </motion.button>
                );
              })}
              
              <motion.button
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-3 rounded-xl border border-neutral-200 hover:bg-white hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <ChevronRight className="w-4 h-4" />
              </motion.button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}