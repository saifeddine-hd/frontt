export interface ScanJob {
  id: string;
  filename: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: Date;
  completed_at?: Date;findings_count?: number | null;
  error?: string;
}

export interface Finding {
  id?: string;
  job_id: string;
  file_path: string;
  line_number: number;
  secret_type: string;
  secret: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  rule_id: string;
  confidence?: number;
  created_at?: Date;
  scanner?: string;
}

export interface ScanStatistics {
  job_id: string;
  total_findings: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  by_type: Record<string, number>;
  files_scanned: number;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  provider: 'github' | 'gitlab';
  status: 'active' | 'inactive' | 'error';
  last_scan?: string;
  last_scan_status?: string;
  findings_count?: number;
  discord_webhook_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RepositoryCreate {
  name: string;
  url: string;
  provider: 'github' | 'gitlab';
  token: string;
  discord_webhook_url?: string;
}

export interface PaginatedResponse<T> {
  findings: T[];
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
}