import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus, Github, GitBranch, Settings, Trash2, Play, TestTube, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

import { getRepositories, createRepository, deleteRepository, triggerScan, testWebhook } from '../lib/api';
import SeverityBadge from '../components/SeverityBadge';
import type { Repository } from '../types';

export default function Repositories() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    provider: 'github',
    token: '',
    discord_webhook_url: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      const data = await getRepositories();
      setRepositories(data);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load repositories');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.url || !formData.token) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);
    
    try {
      await createRepository({
        name: formData.name,
        url: formData.url,
        provider: formData.provider as 'github' | 'gitlab',
        token: formData.token,
        discord_webhook_url: formData.discord_webhook_url || undefined
      });
      
      toast.success('Repository added successfully!');
      setShowAddForm(false);
      setFormData({ name: '', url: '', provider: 'github', token: '', discord_webhook_url: '' });
      loadRepositories();
    } catch (error: any) {
      toast.error(error.message || 'Failed to add repository');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      await deleteRepository(id);
      toast.success('Repository deleted successfully');
      loadRepositories();
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete repository');
    }
  };

  const handleTriggerScan = async (id: string, name: string) => {
    try {
      await triggerScan(id);
      toast.success(`Scan triggered for ${name}`);
      // Refresh repositories to show updated status
      setTimeout(loadRepositories, 1000);
    } catch (error: any) {
      toast.error(error.message || 'Failed to trigger scan');
    }
  };

  const handleTestWebhook = async (id: string, name: string) => {
    try {
      await testWebhook(id);
      toast.success(`Test notification sent for ${name}`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to send test notification');
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
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
          <h1 className="text-3xl font-bold text-gray-900">Repository Monitoring</h1>
          <p className="text-gray-600 mt-2">Monitor GitHub and GitLab repositories for exposed secrets</p>
        </div>
        
        <motion.button
          onClick={() => setShowAddForm(true)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center space-x-2 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>Add Repository</span>
        </motion.button>
      </motion.div>

      {/* Add Repository Form */}
      {showAddForm && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm p-6 border border-gray-200"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Add New Repository</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Repository Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="my-awesome-project"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Provider *
                </label>
                <select
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Repository URL *
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="https://github.com/username/repository"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Access Token *
              </label>
              <input
                type="password"
                value={formData.token}
                onChange={(e) => setFormData({ ...formData, token: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                {formData.provider === 'github' 
                  ? 'GitHub Personal Access Token with repo permissions'
                  : 'GitLab Personal Access Token with read_repository permissions'
                }
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Discord Webhook URL (Optional)
              </label>
              <input
                type="url"
                value={formData.discord_webhook_url}
                onChange={(e) => setFormData({ ...formData, discord_webhook_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="https://discord.com/api/webhooks/..."
              />
              <p className="text-sm text-gray-500 mt-1">
                Repository-specific Discord webhook for notifications
              </p>
            </div>

            <div className="flex items-center space-x-3 pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {isSubmitting ? 'Adding...' : 'Add Repository'}
              </button>
              
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-2 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Repositories List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-lg shadow-sm"
      >
        {repositories.length === 0 ? (
          <div className="text-center py-12">
            <GitBranch className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No repositories yet</h3>
            <p className="text-gray-500 mb-4">Add your first repository to start monitoring for secrets.</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Add Repository
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Repository
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Scan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Findings
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {repositories.map((repo, index) => (
                  <motion.tr
                    key={repo.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          {repo.provider === 'github' ? (
                            <Github className="w-5 h-5 text-gray-900" />
                          ) : (
                            <GitBranch className="w-5 h-5 text-orange-500" />
                          )}
                        </div>
                        <div className="ml-3">
                          <div className="text-sm font-medium text-gray-900">{repo.name}</div>
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {repo.url}
                          </div>
                        </div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <SeverityBadge severity={repo.status} size="sm" />
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {repo.last_scan ? formatTimeAgo(repo.last_scan) : 'Never'}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {repo.findings_count !== null ? (
                          <span className={`font-medium ${
                            repo.findings_count > 0 ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {repo.findings_count}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleTriggerScan(repo.id, repo.name)}
                          className="text-blue-600 hover:text-blue-900 p-1 rounded"
                          title="Trigger scan"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                        
                        {repo.discord_webhook_url && (
                          <button
                            onClick={() => handleTestWebhook(repo.id, repo.name)}
                            className="text-green-600 hover:text-green-900 p-1 rounded"
                            title="Test Discord webhook"
                          >
                            <TestTube className="w-4 h-4" />
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDelete(repo.id, repo.name)}
                          className="text-red-600 hover:text-red-900 p-1 rounded"
                          title="Delete repository"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-blue-50 border border-blue-200 rounded-lg p-6"
      >
        <div className="flex items-start">
          <AlertCircle className="w-6 h-6 text-blue-600 mt-1 mr-3 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-blue-900 mb-2">How Repository Monitoring Works</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• <strong>Automatic Scanning:</strong> Repositories are scanned every 30 minutes</li>
              <li>• <strong>Webhook Integration:</strong> Instant scans triggered on push events</li>
              <li>• <strong>Discord Notifications:</strong> Real-time alerts for critical findings</li>
              <li>• <strong>Secure Storage:</strong> Access tokens are encrypted at rest</li>
              <li>• <strong>Remediation Guides:</strong> Actionable steps included in alerts</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  );
}