const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(credentials: { username: string; password: string }) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  // Health
  async getHealth() {
    return this.request('/health');
  }

  // Scans
  async createScan(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/scans`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getScanStatus(jobId: string) {
    return this.request(`/scans/${jobId}`);
  }

  // Findings
  async getFindings(
    jobId: string, 
    page: number = 1, 
    size: number = 20,
    severity?: string,
    secretType?: string
  ) {
    const params = new URLSearchParams({
      job_id: jobId,
      page: page.toString(),
      size: size.toString()
    });

    if (severity) params.append('severity', severity);
    if (secretType) params.append('secret_type', secretType);

    return this.request(`/findings?${params}`);
  }

  async exportFindings(jobId: string, format: 'json' | 'csv') {
    return this.request(`/findings/export/${jobId}?format=${format}`);
  }

  async getScanStatistics(jobId: string) {
    return this.request(`/findings/stats/${jobId}`);
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('/dashboard/stats');
  }

  async getRecentScans(limit: number = 10) {
    return this.request(`/dashboard/recent-scans?limit=${limit}`);
  }

  async getDashboardOverview() {
    return this.request('/dashboard/overview');
  }
}

const apiClient = new ApiClient();

// Export individual functions for easier importing
export const login = (credentials: { username: string; password: string }) => 
  apiClient.login(credentials);

export const getHealth = () => apiClient.getHealth();

export const createScan = (file: File) => apiClient.createScan(file);

export const getScanStatus = (jobId: string) => apiClient.getScanStatus(jobId);

export const getFindings = (
  jobId: string, 
  page?: number, 
  size?: number,
  severity?: string,
  secretType?: string
) => apiClient.getFindings(jobId, page, size, severity, secretType);

export const exportFindings = (jobId: string, format: 'json' | 'csv') =>
  apiClient.exportFindings(jobId, format);

export const getScanStatistics = (jobId: string) => 
  apiClient.getScanStatistics(jobId);

// Dashboard
export const getDashboardStats = () => apiClient.getDashboardStats();

export const getRecentScans = (limit?: number) => apiClient.getRecentScans(limit);

export const getDashboardOverview = () => apiClient.getDashboardOverview();

// Repositories
export const getRepositories = () => apiClient.request('/repositories');

export const createRepository = (data: any) => apiClient.request('/repositories', {
  method: 'POST',
  body: JSON.stringify(data)
});

export const deleteRepository = (id: string) => apiClient.request(`/repositories/${id}`, {
  method: 'DELETE'
});

export const triggerScan = (id: string) => apiClient.request(`/repositories/${id}/scan`, {
  method: 'POST'
});

export const testWebhook = (id: string) => apiClient.request(`/repositories/${id}/test-webhook`, {
  method: 'POST'
});