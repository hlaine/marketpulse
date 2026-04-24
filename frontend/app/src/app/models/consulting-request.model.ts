export interface Evidence {
  snippet: string;
  source_part: string;
}

export interface NormalizedValue {
  raw: string | null;
  normalized: string | null;
  confidence: number;
  evidence: Evidence[];
}

export interface TechnologyValue extends NormalizedValue {
  category: 'language' | 'framework' | 'cloud' | 'database' | 'tool' | 'platform' | 'other';
  importance: 'required' | 'preferred' | 'mentioned' | null;
}

export interface LanguageValue extends NormalizedValue {
  proficiency: 'basic' | 'professional' | 'fluent' | 'native' | null;
  importance: 'required' | 'preferred' | 'mentioned' | null;
}

export interface CommercialDetails {
  start_date: string | null;
  start_date_raw: string | null;
  duration_raw: string | null;
  duration_months: number | null;
  allocation_percent: number | null;
  positions_count: number | null;
  rate_amount: number | null;
  rate_currency: string | null;
  rate_unit: 'hour' | 'day' | 'month' | null;
  confidence: number;
  evidence: Evidence[];
}

export interface ConsultingRequest {
  schema_version: string;
  request_id: string;
  source: {
    kind: 'email' | 'web_page' | 'document' | 'portal_posting' | 'chat_message' | 'manual_note' | 'other';
    source_ref: string;
    received_at: string | null;
    sender_name: string | null;
    sender_organization: string | null;
    sender_domain: string | null;
    origin_url: string | null;
    content_types: string[];
  };
  content: {
    title: string | null;
    language: string | null;
    parts: Array<{
      part_id: string;
      kind: 'title' | 'message' | 'document' | 'attachment' | 'web_page' | 'metadata' | 'other';
      mime_type: string | null;
      text_excerpt: string | null;
    }>;
  };
  demand: {
    primary_role: NormalizedValue;
    secondary_roles: NormalizedValue[];
    seniority: NormalizedValue;
    technologies: TechnologyValue[];
    certifications: Array<NormalizedValue & { importance: 'required' | 'preferred' | 'mentioned' | null }>;
    languages: LanguageValue[];
    sector: NormalizedValue;
    location: {
      raw: string | null;
      city: string | null;
      country: string | null;
      confidence: number;
      evidence: Evidence[];
    };
    remote_mode: NormalizedValue;
    commercial: CommercialDetails;
    summary: {
      text: string;
      confidence: number;
    };
  };
  quality: {
    overall_confidence: number;
    review_status: 'ok' | 'partial' | 'needs_review' | 'failed';
    warnings: string[];
  };
  processing: {
    processed_at: string;
    extractor_model: string;
    prompt_version: string;
  };
}
