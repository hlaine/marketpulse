export interface RequestRecord {
  request_id: string;
  received_at: string | null;
  source_kind: string | null;
  sender_organization: string | null;
  sender_domain: string | null;
  primary_role: string | null;
  seniority: string | null;
  sector: string | null;
  location_city: string | null;
  remote_mode: string | null;
  rate_amount: number | null;
  rate_currency: string | null;
  rate_unit: string | null;
  duration_months: number | null;
  review_status: string | null;
  overall_confidence: number | null;
}

export interface RequestSnapshot {
  generated_at: string;
  database_path: string;
  snapshot_note: string;
  row_count: number;
  requests: RequestRecord[];
}
