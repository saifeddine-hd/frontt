import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, Home, Upload, GitBranch, LogOut, User, Sparkles } from 'lucide-react';

interface NavbarProps {
  onLogout: () => void;
}

export default function Navbar({ onLogout }: NavbarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/scan', label: 'New Scan', icon: Upload },
    { path: '/repositories', label: 'Repositories', icon: GitBranch }
  ];

  return (
    <nav className="glass-strong border-b border-white/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <motion.div
            whileHover={{ scale: 1.05, rotate: 1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/')}
            className="flex items-center cursor-pointer group"
          >
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center mr-3 shadow-lg shadow-primary/40 group-hover:shadow-xl transition-all duration-300">
              <Shield className="w-5 h-5 text-white group-hover:scale-110 transition-transform duration-300" />
            </div>
            <div className="flex items-center">
              <span className="text-xl font-bold text-gradient-primary">SecretHawk</span>
              <Sparkles className="w-4 h-4 text-secondary-400 ml-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
          </motion.div>

          {/* Navigation Items */}
          <div className="flex items-center space-x-2">
            {navItems.map(({ path, label, icon: Icon }) => {
              const isActive = location.pathname === path;

              return (
                <motion.button
                  key={path}
                  onClick={() => navigate(path)}
                  whileHover={{ scale: 1.05, y: -1 }}
                  whileTap={{ scale: 0.95 }}
                  className={`relative nav-item flex items-center px-4 py-2.5 rounded-xl font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-primary-50 to-secondary-50 text-primary-700 shadow-sm'
                      : 'text-neutral-600 hover:text-neutral-900 hover:bg-white/50'
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 mr-2 transition-colors duration-200 ${
                      isActive ? 'text-primary-600' : ''
                    }`}
                  />
                  {label}
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-gradient-to-r from-primary-100/50 to-secondary-100/50 rounded-xl -z-10"
                      transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </motion.button>
              );
            })}
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-3">
            <motion.div
              className="flex items-center px-3 py-2 rounded-lg bg-white/30 backdrop-blur-sm border border-white/20"
              whileHover={{ scale: 1.02 }}
            >
              <div className="w-6 h-6 bg-gradient-to-br from-primary-400 to-secondary-400 rounded-full flex items-center justify-center mr-2">
                <User className="w-3 h-3 text-white" />
              </div>
              <span className="text-sm font-medium text-neutral-700">admin</span>
            </motion.div>

            <motion.button
              onClick={onLogout}
              whileHover={{ scale: 1.05, rotate: 1 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center px-3 py-2 text-neutral-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200 group"
            >
              <LogOut className="w-4 h-4 mr-2 group-hover:rotate-12 transition-transform duration-200" />
              Logout
            </motion.button>
          </div>
        </div>
      </div>
    </nav>
  );
}
