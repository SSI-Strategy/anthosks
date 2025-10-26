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
    sentiment: string;  // Positive, Negative, Neutral, Unknown
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
