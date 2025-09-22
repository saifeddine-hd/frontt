import React from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Eye, EyeOff, ExternalLink } from 'lucide-react';

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
      <div className="text-center py-12">
        <Eye className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No findings</h3>
        <p className="text-gray-500">No secrets were found in this scan.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                File & Line
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Secret
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scanner
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {findings.map((finding, index) => (
              <motion.tr
                key={`${finding.id || index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="hover:bg-gray-50"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    <div className="font-medium truncate max-w-xs" title={finding.file_path}>
                      {finding.file_path.split('/').pop()}
                    </div>
                    <div className="text-gray-500">Line {finding.line_number}</div>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {finding.secret_type.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div className="text-sm text-gray-500">{finding.rule_id}</div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <SeverityBadge severity={finding.severity} />
                </td>
                
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <code className={`text-sm px-2 py-1 rounded font-mono max-w-xs truncate ${
                      showSecrets 
                        ? 'bg-red-50 text-red-800 border border-red-200' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {displaySecret(finding.secret)}
                    </code>
                    {showSecrets && (
                      <div className="text-xs text-orange-600 flex items-center">
                        <EyeOff className="w-3 h-3 mr-1" />
                        Visible
                      </div>
                    )}
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className="capitalize">{finding.scanner || 'regex'}</span>
                  {finding.confidence && (
                    <div className="text-xs text-gray-400">
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
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Page {page} of {totalPages}
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <button
                    key={pageNum}
                    onClick={() => onPageChange(pageNum)}
                    className={`px-3 py-2 rounded-lg text-sm ${
                      pageNum === page
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}