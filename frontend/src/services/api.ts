import axios from 'axios';
import type { Report, ReportDetail, UploadResponse } from '../types';
import { getAccessToken } from './authService';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;
const API_ROOT_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach authentication token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Failed to get access token:', error);
      // Continue without token - backend will handle authentication
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Authentication required - redirecting to login');
      // The MSAL provider will handle the redirect
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export type { Report, ReportDetail, UploadResponse };

/* Moved to types/index.ts
export interface Report {
  id: string;
  site_number: string;
  country: string;
  institution: string;
  visit_start_date: string;
  visit_end_date: string;
  visit_type: string;
  quality: string;
  questions_count: number;
  action_items_count: number;
}

export interface ReportDetail {
  id: string;
  protocol_number: string;
  site_info: {
    site_number: string;
    country: string;
    institution: string;
    pi_first_name: string;
    pi_last_name: string;
    city?: string;
    anthos_staff: string;
    cra_name?: string;
  };
  visit_start_date: string;
  visit_end_date: string;
  visit_type: string;
  recruitment_stats: {
    screened: number;
    screen_failures: number;
    randomized_enrolled: number;
    early_discontinued: number;
    completed_treatment: number;
    completed_study: number;
  };
  question_responses: Array<{
    question_number: number;
    question_text: string;
    answer: string;
    narrative_summary?: string;
    key_finding?: string;
    evidence?: string;
    confidence: number;
  }>;
  action_items: Array<{
    item_number: number;
    description: string;
    action_to_be_taken: string;
    responsible: string;
    due_date: string;
    status?: string;
  }>;
  risk_assessment: {
    site_level_risks_identified: boolean;
    cra_level_risks_identified: boolean;
    impact_country_level: boolean;
    impact_study_level: boolean;
    narrative: string;
  };
  overall_site_quality: string;
  key_concerns: string[];
  key_strengths: string[];
  extraction_timestamp: string;
  llm_model: string;
  source_file: string;
}

export interface UploadResponse {
  status: string;
  report_id: string;
  questions: number;
  action_items: number;
  quality: string;
}
*/

export const uploadReport = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>(
    '/reports/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

export const listReports = async (): Promise<Report[]> => {
  const response = await api.get<{ reports: Report[]; total: number }>('/reports');
  return response.data.reports;
};

export const getReport = async (reportId: string): Promise<ReportDetail> => {
  const response = await api.get<ReportDetail>(`/reports/${reportId}`);
  return response.data;
};

export const deleteReport = async (reportId: string): Promise<void> => {
  await api.delete(`/reports/${reportId}`);
};

// ===== ANALYTICS API =====

export interface KPIData {
  total_sites: number;
  total_reports: number;
  compliance_rate: number;
  non_compliance_rate: number;
  completeness_rate: number;
  avg_site_quality_score: number;
  high_risk_sites: number;
  avg_enrollment_rate: number;
  avg_completion_rate: number;
  total_action_items: number;
  overdue_action_items: number;
  answer_distribution: {
    yes: number;
    no: number;
    na: number;
    nr: number;
  };
}

export interface TrendDataPoint {
  period: string;
  compliance_rate: number;
  non_compliance_rate: number;
  report_count: number;
}

export interface QuestionStatistic {
  question_number: number;
  question_text: string;
  compliance_rate: number;
  yes_count: number;
  no_count: number;
  na_count: number;
  nr_count: number;
  total_responses: number;
  sentiment_positive: number;
  sentiment_negative: number;
}

export interface SiteLeaderboardEntry {
  site_number: string;
  country: string;
  institution: string;
  pi_name: string;
  compliance_rate: number;
  avg_quality_score: number;
  enrollment_rate: number;
  completion_rate: number;
  report_count: number;
  last_visit_date: string | null;
}

export interface GeographicSummary {
  country: string;
  site_count: number;
  report_count: number;
  compliance_rate: number;
  yes_count: number;
  no_count: number;
  na_count: number;
  nr_count: number;
}

export const getKPIs = async (params?: {
  date_from?: string;
  date_to?: string;
  country?: string;
  protocol?: string;
  site_number?: string;
}): Promise<KPIData> => {
  const response = await api.get<KPIData>('/analytics/kpi', { params });
  return response.data;
};

export const getComplianceTrends = async (params: {
  date_from: string;
  date_to: string;
  granularity?: 'day' | 'week' | 'month' | 'quarter';
  country?: string;
  protocol?: string;
}): Promise<TrendDataPoint[]> => {
  const response = await api.get<{ trends: TrendDataPoint[] }>('/analytics/compliance/trends', { params });
  return response.data.trends;
};

export const getQuestionStatistics = async (params?: {
  date_from?: string;
  date_to?: string;
  country?: string;
  protocol?: string;
}): Promise<QuestionStatistic[]> => {
  const response = await api.get<{ questions: QuestionStatistic[] }>('/analytics/compliance/questions', { params });
  return response.data.questions;
};

export const getSiteLeaderboard = async (params?: {
  date_from?: string;
  date_to?: string;
  sort_by?: 'compliance_rate' | 'quality_score' | 'enrollment_rate';
  limit?: number;
  country?: string;
}): Promise<SiteLeaderboardEntry[]> => {
  const response = await api.get<{ sites: SiteLeaderboardEntry[] }>('/analytics/sites/leaderboard', { params });
  return response.data.sites;
};

export const getGeographicSummary = async (params?: {
  date_from?: string;
  date_to?: string;
  protocol?: string;
}): Promise<GeographicSummary[]> => {
  const response = await api.get<{ countries: GeographicSummary[] }>('/analytics/geographic', { params });
  return response.data.countries;
};

// ===== WARMUP API =====

export interface HealthStatus {
  status: string;
  service?: string;
  message?: string;
  version?: string;
}

export interface WarmupStatus {
  status: 'warm' | 'warming' | 'cold';
  message: string;
  database?: string;
  analytics?: string;
}

/**
 * Check if backend is healthy (no database required)
 */
export const checkHealth = async (): Promise<HealthStatus> => {
  const response = await axios.get<HealthStatus>(`${API_ROOT_URL}/health`, {
    timeout: 5000 // 5 second timeout for health check
  });
  return response.data;
};

/**
 * Warmup the backend (initialize database connections)
 */
export const warmupBackend = async (): Promise<WarmupStatus> => {
  const response = await axios.get<WarmupStatus>(`${API_ROOT_URL}/warmup`, {
    timeout: 30000 // 30 second timeout for warmup
  });
  return response.data;
};

/**
 * Check if backend is warm and ready
 */
export const isBackendWarm = async (): Promise<boolean> => {
  try {
    const status = await warmupBackend();
    return status.status === 'warm';
  } catch (err) {
    const error = err as Error;
    console.error('Warmup check failed:', error);
    return false;
  }
};

export default api;
