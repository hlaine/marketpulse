export type DemoEmailStatus = 'new' | 'analyzing' | 'analyzed' | 'error';

export interface DemoEmail {
  id: string;
  date: string | null;
  subject: string | null;
  from: string | null;
  to: string | null;
  cc: string | null;
  body: string | null;
}

export interface DemoEmailResponse {
  email: DemoEmail;
  generated_by: 'ai' | 'fallback';
  warnings: string[];
}

export interface DocumentUploadResponse {
  request_id: string;
  stored: boolean;
  record: ConsultingRequestRecord;
  warnings: string[];
}

export interface ConsultingRequestRecord {
  request_id: string;
  demand: {
    primary_role: TaggedValue;
    seniority: TaggedValue;
    technologies: TechnologyValue[];
    location: {
      city: string | null;
      raw: string | null;
    };
    remote_mode: TaggedValue;
    commercial: {
      duration_months: number | null;
      rate_amount: number | null;
      rate_currency: string | null;
      rate_unit: string | null;
    };
    summary: {
      text: string;
    };
  };
  quality: {
    overall_confidence: number | null;
    review_status: string | null;
    warnings: string[];
  };
}

export interface TaggedValue {
  raw: string | null;
  normalized: string | null;
}

export interface TechnologyValue {
  raw: string | null;
  normalized: string | null;
  category: string | null;
}

export interface MailboxEmail {
  email: DemoEmail;
  status: DemoEmailStatus;
  generatedBy: 'ai' | 'fallback';
  generationWarnings: string[];
  analysis: string | null;
  requestId: string | null;
  error: string | null;
}
