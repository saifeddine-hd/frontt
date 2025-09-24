import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Sparkles } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactElement; // plus précis que ReactNode
  color?: 'blue' | 'red' | 'green' | 'yellow' | 'orange' | 'purple';
  trend?: number;
}

const colorConfig = {
  blue: {
    gradient: 'from-blue-500 to-cyan-500',
    bg: 'from-blue-50 to-cyan-50',
    text: 'text-blue-600',
    shadow: 'shadow-blue-500/20'
  },
  red: {
    gradient: 'from-red-500 to-rose-500',
    bg: 'from-red-50 to-rose-50',
    text: 'text-red-600',
    shadow: 'shadow-red-500/20'
  },
  green: {
    gradient: 'from-green-500 to-emerald-500',
    bg: 'from-green-50 to-emerald-50',
    text: 'text-green-600',
    shadow: 'shadow-green-500/20'
  },
  yellow: {
    gradient: 'from-yellow-500 to-amber-500',
    bg: 'from-yellow-50 to-amber-50',
    text: 'text-yellow-600',
    shadow: 'shadow-yellow-500/20'
  },
  orange: {
    gradient: 'from-orange-500 to-red-500',
    bg: 'from-orange-50 to-red-50',
    text: 'text-orange-600',
    shadow: 'shadow-orange-500/20'
  },
  purple: {
    gradient: 'from-purple-500 to-violet-500',
    bg: 'from-purple-50 to-violet-50',
    text: 'text-purple-600',
    shadow: 'shadow-purple-500/20'
  }
};

export default function StatCard({
  title,
  value,
  icon,
  color = 'blue',
  trend
}: StatCardProps) {
  const config = colorConfig[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{
        scale: 1.02,
        y: -4,
        transition: { duration: 0.2, ease: 'easeOut' }
      }}
      className={`relative overflow-hidden group cursor-pointer rounded-2xl p-6 bg-white shadow-md`}
    >
      {/* Background Gradient */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${config.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
      />

      {/* Sparkle Effect */}
      <motion.div
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100"
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      >
        <Sparkles className="w-4 h-4 text-neutral-300" />
      </motion.div>

      <div className="flex items-center justify-between mb-6 relative z-10">
        {icon && (
          <motion.div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center bg-gradient-to-br ${config.gradient} shadow-lg ${config.shadow} group-hover:scale-110 transition-transform duration-300`}
            whileHover={{ rotate: 5 }}
          >
            {React.cloneElement(icon, { className: 'w-6 h-6 text-white' })}
          </motion.div>
        )}

        {typeof trend === 'number' && (
          <motion.div
            className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              trend >= 0
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            {trend >= 0 ? (
              <TrendingUp className="w-4 h-4 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 mr-1" />
            )}
            <span>{Math.abs(trend)}%</span>
          </motion.div>
        )}
      </div>

      <div className="relative z-10">
        <motion.h3
          className="text-3xl font-bold text-neutral-900 mb-2"
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1, type: 'spring', bounce: 0.4 }}
        >
          {value}
        </motion.h3>
        <p className="text-neutral-600 text-sm font-medium tracking-wide">
          {title}
        </p>
      </div>

      {/* Hover Glow Effect */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${config.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300 rounded-2xl`}
      />
    </motion.div>
  );
}
