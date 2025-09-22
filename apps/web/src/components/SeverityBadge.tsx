import React from 'react';

interface SeverityBadgeProps {
  severity: string;
  size?: 'sm' | 'md' | 'lg';
}

const severityConfig = {
  critical: {
    label: 'Critical',
    className: 'bg-red-100 text-red-800 border-red-200'
  },
  high: {
    label: 'High',
    className: 'bg-orange-100 text-orange-800 border-orange-200'
  },
  medium: {
    label: 'Medium',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
  },
  low: {
    label: 'Low',
    className: 'bg-blue-100 text-blue-800 border-blue-200'
  },
  // Scan statuses
  pending: {
    label: 'Pending',
    className: 'bg-gray-100 text-gray-800 border-gray-200'
  },
  running: {
    label: 'Running',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-100 text-green-800 border-green-200'
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-800 border-red-200'
  }
};

const sizeClasses = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-2 text-base'
};

export default function SeverityBadge({ severity, size = 'md' }: SeverityBadgeProps) {
  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low;
  
  return (
    <span className={`
      inline-flex items-center rounded-full font-medium border
      ${config.className}
      ${sizeClasses[size]}
    `}>
      {config.label}
    </span>
  );
}