import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield, Info, CheckCircle } from 'lucide-react';

interface SeverityBadgeProps {
  severity: string;
  size?: 'sm' | 'md' | 'lg';
}

const severityConfig = {
  critical: {
    label: 'Critical',
    className: 'bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-lg shadow-red-500/25',
    icon: AlertTriangle,
    pulse: true
  },
  high: {
    label: 'High',
    className: 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/25',
    icon: AlertTriangle,
    pulse: false
  },
  medium: {
    label: 'Medium',
    className: 'bg-gradient-to-r from-yellow-500 to-amber-500 text-white shadow-lg shadow-yellow-500/25',
    icon: Info,
    pulse: false
  },
  low: {
    label: 'Low',
    className: 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/25',
    icon: Info,
    pulse: false
  },
  // Scan statuses
  pending: {
    label: 'Pending',
    className: 'bg-gradient-to-r from-gray-400 to-gray-500 text-white shadow-lg shadow-gray-500/25',
    icon: Shield,
    pulse: true
  },
  running: {
    label: 'Running',
    className: 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/25',
    icon: Shield,
    pulse: true
  },
  completed: {
    label: 'Completed',
    className: 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg shadow-green-500/25',
    icon: CheckCircle,
    pulse: false
  },
  failed: {
    label: 'Failed',
    className: 'bg-gradient-to-r from-red-600 to-red-700 text-white shadow-lg shadow-red-600/25',
    icon: AlertTriangle,
    pulse: false
  },
  active: {
    label: 'Active',
    className: 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg shadow-green-500/25',
    icon: CheckCircle,
    pulse: false
  },
  inactive: {
    label: 'Inactive',
    className: 'bg-gradient-to-r from-gray-400 to-gray-500 text-white shadow-lg shadow-gray-500/25',
    icon: Shield,
    pulse: false
  },
  error: {
    label: 'Error',
    className: 'bg-gradient-to-r from-red-600 to-red-700 text-white shadow-lg shadow-red-600/25',
    icon: AlertTriangle,
    pulse: false
  }
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base'
};

export default function SeverityBadge({ severity, size = 'md' }: SeverityBadgeProps) {
  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low;
  const Icon = config.icon;
  
  return (
    <motion.span 
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      className={`
      inline-flex items-center rounded-full font-semibold backdrop-blur-sm
      ${config.className}
      ${sizeClasses[size]}
      ${config.pulse ? 'animate-pulse' : ''}
      transition-all duration-200 ease-out cursor-default
    `}
    >
      <Icon className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} mr-1.5`} />
      <span className="tracking-wide">{config.label}</span>
    </motion.span>
  );
}