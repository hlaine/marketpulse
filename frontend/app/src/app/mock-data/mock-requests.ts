import { ConsultingRequest } from '../models/consulting-request.model';

function request(partial: any): ConsultingRequest {
  return {
    schema_version: '1.0',
    request_id: partial.request_id,
    source: {
      kind: 'email',
      source_ref: `mock://${partial.request_id}`,
      received_at: '2026-04-20T08:00:00Z',
      sender_name: 'Unknown',
      sender_organization: 'Unknown',
      sender_domain: null,
      origin_url: null,
      content_types: ['text/html'],
      ...partial.source
    },
    content: {
      title: 'Consulting request',
      language: 'en',
      parts: [
        {
          part_id: 'body',
          kind: 'message',
          mime_type: 'text/html',
          text_excerpt: 'Mock consulting request used for dashboard previews.'
        }
      ],
      ...partial.content
    },
    demand: {
      primary_role: {
        raw: 'Backend Engineer',
        normalized: 'Backend Engineer',
        confidence: 0.9,
        evidence: []
      },
      secondary_roles: [],
      seniority: {
        raw: 'senior',
        normalized: 'senior',
        confidence: 0.88,
        evidence: []
      },
      technologies: [],
      certifications: [],
      languages: [],
      sector: {
        raw: 'private',
        normalized: 'private',
        confidence: 0.75,
        evidence: []
      },
      location: {
        raw: 'Stockholm / hybrid',
        city: 'Stockholm',
        country: 'Sweden',
        confidence: 0.82,
        evidence: []
      },
      remote_mode: {
        raw: 'hybrid',
        normalized: 'hybrid',
        confidence: 0.9,
        evidence: []
      },
      commercial: {
        start_date: '2026-05-01T00:00:00Z',
        start_date_raw: '2026-05-01',
        duration_raw: '6 months',
        duration_months: 6,
        allocation_percent: 100,
        positions_count: 1,
        rate_amount: 980,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.8,
        evidence: []
      },
      summary: {
        text: 'Request for a senior backend consultant.',
        confidence: 0.84
      },
      ...partial.demand
    },
    quality: {
      overall_confidence: 0.84,
      review_status: 'ok',
      warnings: [],
      ...partial.quality
    },
    processing: {
      processed_at: '2026-04-24T10:15:00Z',
      extractor_model: 'gpt-5.4',
      prompt_version: 'consulting_request_v1',
      ...partial.processing
    }
  };
}

export const MOCK_CONSULTING_REQUESTS: ConsultingRequest[] = [
  request({
    request_id: 'req-001',
    source: {
      kind: 'email',
      source_ref: 'email-export://0004',
      received_at: '2026-04-15T09:30:00Z',
      sender_name: 'Johan Bergstrom',
      sender_organization: 'Konsult Partners',
      sender_domain: 'konsultpartners.se',
      origin_url: null,
      content_types: ['text/html']
    },
    content: {
      title: 'New Request: .NET Developer',
      language: 'en',
      parts: [
        {
          part_id: 'body',
          kind: 'message',
          mime_type: 'text/html',
          text_excerpt: 'They are looking for a .NET Developer in Malmo for a 6 month assignment.'
        }
      ]
    },
    demand: {
      primary_role: { raw: '.NET Developer', normalized: '.NET Developer', confidence: 0.92, evidence: [] },
      secondary_roles: [],
      seniority: { raw: null, normalized: 'unknown', confidence: 0.35, evidence: [] },
      technologies: [
        {
          raw: '.NET',
          normalized: '.NET',
          category: 'framework',
          importance: 'required',
          confidence: 0.9,
          evidence: []
        }
      ],
      certifications: [],
      languages: [],
      sector: { raw: 'e-commerce', normalized: 'private', confidence: 0.75, evidence: [] },
      location: { raw: 'Malmo (on-site)', city: 'Malmo', country: 'Sweden', confidence: 0.9, evidence: [] },
      remote_mode: { raw: 'on-site', normalized: 'onsite', confidence: 0.9, evidence: [] },
      commercial: {
        start_date: '2026-05-01T00:00:00Z',
        start_date_raw: '2026-05-01',
        duration_raw: '6 months',
        duration_months: 6,
        allocation_percent: null,
        positions_count: 1,
        rate_amount: 950,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.8,
        evidence: []
      },
      summary: {
        text: 'Request for a .NET Developer in Malmo for a 6 month assignment.',
        confidence: 0.85
      }
    },
    quality: { overall_confidence: 0.84, review_status: 'ok', warnings: [] }
  }),
  request({
    request_id: 'req-002',
    source: {
      kind: 'portal_posting',
      received_at: '2026-04-16T11:15:00Z',
      sender_name: null,
      sender_organization: 'Northwind Public Tech',
      sender_domain: 'northwind.se',
      origin_url: 'https://example.com/public/req-002',
      content_types: ['text/html']
    },
    content: { title: 'Backend Engineer for public sector modernization', language: 'en', parts: [] },
    demand: {
      primary_role: { raw: 'Backend Engineer', normalized: 'Backend Engineer', confidence: 0.89, evidence: [] },
      secondary_roles: [{ raw: 'API Developer', normalized: 'API Developer', confidence: 0.66, evidence: [] }],
      seniority: { raw: 'Senior', normalized: 'senior', confidence: 0.83, evidence: [] },
      technologies: [
        { raw: 'Java', normalized: 'Java', category: 'language', importance: 'required', confidence: 0.88, evidence: [] },
        { raw: 'Spring Boot', normalized: 'Spring Boot', category: 'framework', importance: 'required', confidence: 0.87, evidence: [] }
      ],
      certifications: [],
      languages: [{ raw: 'Swedish', normalized: 'Swedish', proficiency: 'professional', importance: 'required', confidence: 0.9, evidence: [] }],
      sector: { raw: 'public sector', normalized: 'public', confidence: 0.94, evidence: [] },
      location: { raw: 'Stockholm / hybrid', city: 'Stockholm', country: 'Sweden', confidence: 0.84, evidence: [] },
      remote_mode: { raw: 'hybrid', normalized: 'hybrid', confidence: 0.93, evidence: [] },
      commercial: {
        start_date: '2026-05-06T00:00:00Z',
        start_date_raw: 'ASAP',
        duration_raw: '12 months',
        duration_months: 12,
        allocation_percent: 100,
        positions_count: 2,
        rate_amount: 1080,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.81,
        evidence: []
      },
      summary: { text: 'Senior backend assignment for a public sector platform rebuild.', confidence: 0.82 }
    },
    quality: { overall_confidence: 0.78, review_status: 'partial', warnings: ['Start date interpreted from ASAP.'] }
  }),
  request({
    request_id: 'req-003',
    source: {
      kind: 'web_page',
      received_at: '2026-04-17T08:45:00Z',
      sender_name: null,
      sender_organization: 'Blue Harbor Commerce',
      sender_domain: 'blueharbor.com',
      origin_url: 'https://blueharbor.com/jobs/data-platform',
      content_types: ['text/html']
    },
    content: { title: 'Data Engineer needed for commerce analytics', language: 'en', parts: [] },
    demand: {
      primary_role: { raw: 'Data Engineer', normalized: 'Data Engineer', confidence: 0.91, evidence: [] },
      secondary_roles: [],
      seniority: { raw: 'Mid-Senior', normalized: 'senior', confidence: 0.7, evidence: [] },
      technologies: [
        { raw: 'Python', normalized: 'Python', category: 'language', importance: 'required', confidence: 0.92, evidence: [] },
        { raw: 'Snowflake', normalized: 'Snowflake', category: 'database', importance: 'preferred', confidence: 0.72, evidence: [] }
      ],
      certifications: [],
      languages: [{ raw: 'English', normalized: 'English', proficiency: 'fluent', importance: 'required', confidence: 0.82, evidence: [] }],
      sector: { raw: 'commerce', normalized: 'private', confidence: 0.8, evidence: [] },
      location: { raw: 'Remote in Sweden', city: null, country: 'Sweden', confidence: 0.77, evidence: [] },
      remote_mode: { raw: 'remote', normalized: 'remote', confidence: 0.92, evidence: [] },
      commercial: {
        start_date: '2026-05-15T00:00:00Z',
        start_date_raw: 'Mid May',
        duration_raw: '9 months',
        duration_months: 9,
        allocation_percent: 100,
        positions_count: 1,
        rate_amount: 1025,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.78,
        evidence: []
      },
      summary: { text: 'Remote data engineering assignment focused on analytics pipelines.', confidence: 0.86 }
    },
    quality: { overall_confidence: 0.9, review_status: 'ok', warnings: [] }
  }),
  request({
    request_id: 'req-004',
    source: {
      kind: 'email',
      received_at: '2026-04-18T13:20:00Z',
      sender_name: 'Sara Lind',
      sender_organization: 'Talent Stream',
      sender_domain: 'talentstream.se',
      origin_url: null,
      content_types: ['text/html', 'application/pdf']
    },
    demand: {
      primary_role: { raw: 'Solution Architect', normalized: 'Solution Architect', confidence: 0.88, evidence: [] },
      secondary_roles: [{ raw: 'Cloud Architect', normalized: 'Cloud Architect', confidence: 0.75, evidence: [] }],
      seniority: { raw: 'Lead', normalized: 'lead', confidence: 0.86, evidence: [] },
      technologies: [
        { raw: 'Azure', normalized: 'Azure', category: 'cloud', importance: 'required', confidence: 0.91, evidence: [] }
      ],
      certifications: [{ raw: 'AZ-104', normalized: 'AZ-104', importance: 'preferred', confidence: 0.72, evidence: [] }],
      languages: [],
      sector: { raw: 'insurance', normalized: 'private', confidence: 0.66, evidence: [] },
      location: { raw: 'Gothenburg / hybrid', city: 'Gothenburg', country: 'Sweden', confidence: 0.83, evidence: [] },
      remote_mode: { raw: 'hybrid', normalized: 'hybrid', confidence: 0.89, evidence: [] },
      commercial: {
        start_date: null,
        start_date_raw: 'Q2',
        duration_raw: 'Long term',
        duration_months: null,
        allocation_percent: 60,
        positions_count: 1,
        rate_amount: 1300,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.61,
        evidence: []
      },
      summary: { text: 'Architecture request for an Azure-heavy insurance initiative.', confidence: 0.77 }
    },
    quality: { overall_confidence: 0.71, review_status: 'needs_review', warnings: ['Duration is described only as long term.'] }
  }),
  request({
    request_id: 'req-005',
    source: {
      kind: 'document',
      received_at: '2026-04-19T07:55:00Z',
      sender_name: null,
      sender_organization: 'Public Digital Agency',
      sender_domain: 'digagency.se',
      origin_url: null,
      content_types: ['application/pdf']
    },
    demand: {
      primary_role: { raw: 'Frontend Engineer', normalized: 'Frontend Engineer', confidence: 0.79, evidence: [] },
      secondary_roles: [],
      seniority: { raw: 'Senior', normalized: 'senior', confidence: 0.82, evidence: [] },
      technologies: [
        { raw: 'Angular', normalized: 'Angular', category: 'framework', importance: 'required', confidence: 0.95, evidence: [] },
        { raw: 'TypeScript', normalized: 'TypeScript', category: 'language', importance: 'required', confidence: 0.9, evidence: [] }
      ],
      certifications: [],
      languages: [{ raw: 'Swedish', normalized: 'Swedish', proficiency: 'fluent', importance: 'required', confidence: 0.93, evidence: [] }],
      sector: { raw: 'public', normalized: 'public', confidence: 0.92, evidence: [] },
      location: { raw: 'Uppsala / onsite', city: 'Uppsala', country: 'Sweden', confidence: 0.86, evidence: [] },
      remote_mode: { raw: 'onsite', normalized: 'onsite', confidence: 0.93, evidence: [] },
      commercial: {
        start_date: '2026-05-10T00:00:00Z',
        start_date_raw: '2026-05-10',
        duration_raw: '4 months',
        duration_months: 4,
        allocation_percent: 100,
        positions_count: 1,
        rate_amount: 920,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.88,
        evidence: []
      },
      summary: { text: 'Public sector frontend role focused on Angular delivery.', confidence: 0.83 }
    },
    quality: { overall_confidence: 0.81, review_status: 'ok', warnings: [] }
  }),
  request({
    request_id: 'req-006',
    source: {
      kind: 'email',
      received_at: '2026-04-20T10:10:00Z',
      sender_name: 'Mikael Persson',
      sender_organization: 'Nordic Build',
      sender_domain: 'nordicbuild.se',
      origin_url: null,
      content_types: ['text/plain']
    },
    demand: {
      primary_role: { raw: 'DevOps Engineer', normalized: 'DevOps Engineer', confidence: 0.9, evidence: [] },
      secondary_roles: [],
      seniority: { raw: 'Senior', normalized: 'senior', confidence: 0.9, evidence: [] },
      technologies: [
        { raw: 'AWS', normalized: 'AWS', category: 'cloud', importance: 'required', confidence: 0.92, evidence: [] },
        { raw: 'Terraform', normalized: 'Terraform', category: 'tool', importance: 'required', confidence: 0.87, evidence: [] }
      ],
      certifications: [],
      languages: [],
      sector: { raw: 'construction tech', normalized: 'private', confidence: 0.62, evidence: [] },
      location: { raw: 'Remote / Stockholm visits', city: 'Stockholm', country: 'Sweden', confidence: 0.71, evidence: [] },
      remote_mode: { raw: 'remote', normalized: 'remote', confidence: 0.8, evidence: [] },
      commercial: {
        start_date: '2026-05-03T00:00:00Z',
        start_date_raw: 'Start in early May',
        duration_raw: '8 months',
        duration_months: 8,
        allocation_percent: 80,
        positions_count: 1,
        rate_amount: 1100,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.83,
        evidence: []
      },
      summary: { text: 'Remote DevOps request with AWS and Terraform requirements.', confidence: 0.85 }
    },
    quality: { overall_confidence: 0.87, review_status: 'ok', warnings: [] }
  }),
  request({
    request_id: 'req-007',
    source: {
      kind: 'chat_message',
      received_at: '2026-04-21T14:05:00Z',
      sender_name: 'Account Team',
      sender_organization: 'FastConsult',
      sender_domain: 'fastconsult.se',
      origin_url: null,
      content_types: ['text/plain']
    },
    demand: {
      primary_role: { raw: 'QA Engineer', normalized: 'QA Engineer', confidence: 0.72, evidence: [] },
      secondary_roles: [{ raw: 'Test Lead', normalized: 'Test Lead', confidence: 0.55, evidence: [] }],
      seniority: { raw: 'Mid', normalized: 'mid', confidence: 0.74, evidence: [] },
      technologies: [
        { raw: 'Playwright', normalized: 'Playwright', category: 'tool', importance: 'required', confidence: 0.82, evidence: [] }
      ],
      certifications: [],
      languages: [],
      sector: { raw: null, normalized: 'unknown', confidence: 0.28, evidence: [] },
      location: { raw: 'Hybrid', city: null, country: 'Sweden', confidence: 0.45, evidence: [] },
      remote_mode: { raw: 'hybrid', normalized: 'hybrid', confidence: 0.71, evidence: [] },
      commercial: {
        start_date: null,
        start_date_raw: 'Soon',
        duration_raw: null,
        duration_months: null,
        allocation_percent: 50,
        positions_count: 2,
        rate_amount: null,
        rate_currency: null,
        rate_unit: null,
        confidence: 0.48,
        evidence: []
      },
      summary: { text: 'Testing-focused request with partial details still missing.', confidence: 0.66 }
    },
    quality: {
      overall_confidence: 0.63,
      review_status: 'needs_review',
      warnings: ['Commercial details are incomplete.', 'Sector could not be determined confidently.']
    }
  }),
  request({
    request_id: 'req-008',
    source: {
      kind: 'manual_note',
      received_at: '2026-04-22T08:25:00Z',
      sender_name: 'Sales team',
      sender_organization: 'Market Pulse',
      sender_domain: 'marketpulse.local',
      origin_url: null,
      content_types: ['text/markdown']
    },
    demand: {
      primary_role: { raw: 'Product Analyst', normalized: 'Product Analyst', confidence: 0.8, evidence: [] },
      secondary_roles: [],
      seniority: { raw: 'Mid', normalized: 'mid', confidence: 0.78, evidence: [] },
      technologies: [{ raw: 'Power BI', normalized: 'Power BI', category: 'tool', importance: 'mentioned', confidence: 0.68, evidence: [] }],
      certifications: [],
      languages: [{ raw: 'English', normalized: 'English', proficiency: 'professional', importance: 'required', confidence: 0.81, evidence: [] }],
      sector: { raw: 'retail', normalized: 'private', confidence: 0.69, evidence: [] },
      location: { raw: 'Stockholm', city: 'Stockholm', country: 'Sweden', confidence: 0.9, evidence: [] },
      remote_mode: { raw: 'hybrid', normalized: 'hybrid', confidence: 0.76, evidence: [] },
      commercial: {
        start_date: '2026-05-20T00:00:00Z',
        start_date_raw: '2026-05-20',
        duration_raw: '3 months',
        duration_months: 3,
        allocation_percent: 60,
        positions_count: 1,
        rate_amount: 850,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.76,
        evidence: []
      },
      summary: { text: 'Analyst request centered on product and KPI reporting.', confidence: 0.74 }
    },
    quality: { overall_confidence: 0.76, review_status: 'partial', warnings: ['Request comes from a manual note and should be cross-checked.'] }
  }),
  request({
    request_id: 'req-009',
    source: {
      kind: 'email',
      received_at: '2026-04-23T12:40:00Z',
      sender_name: 'Emma Holm',
      sender_organization: 'Digital Works',
      sender_domain: 'digitalworks.se',
      origin_url: null,
      content_types: ['text/html']
    },
    demand: {
      primary_role: { raw: 'Backend Engineer', normalized: 'Backend Engineer', confidence: 0.94, evidence: [] },
      secondary_roles: [],
      seniority: { raw: 'Lead', normalized: 'lead', confidence: 0.82, evidence: [] },
      technologies: [
        { raw: 'Node.js', normalized: 'Node.js', category: 'language', importance: 'required', confidence: 0.89, evidence: [] },
        { raw: 'PostgreSQL', normalized: 'PostgreSQL', category: 'database', importance: 'required', confidence: 0.84, evidence: [] }
      ],
      certifications: [],
      languages: [],
      sector: { raw: 'fintech', normalized: 'private', confidence: 0.73, evidence: [] },
      location: { raw: 'Stockholm / hybrid', city: 'Stockholm', country: 'Sweden', confidence: 0.81, evidence: [] },
      remote_mode: { raw: 'hybrid', normalized: 'hybrid', confidence: 0.87, evidence: [] },
      commercial: {
        start_date: '2026-05-12T00:00:00Z',
        start_date_raw: 'May',
        duration_raw: '6 months',
        duration_months: 6,
        allocation_percent: 100,
        positions_count: 1,
        rate_amount: 1150,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.8,
        evidence: []
      },
      summary: { text: 'Backend leadership role for a fintech platform team.', confidence: 0.88 }
    },
    quality: { overall_confidence: 0.91, review_status: 'ok', warnings: [] }
  }),
  request({
    request_id: 'req-010',
    source: {
      kind: 'portal_posting',
      received_at: '2026-04-24T09:05:00Z',
      sender_name: null,
      sender_organization: 'Civic Systems',
      sender_domain: 'civicsystems.se',
      origin_url: 'https://portal.example.com/opportunity/010',
      content_types: ['text/html']
    },
    demand: {
      primary_role: { raw: 'Data Engineer', normalized: 'Data Engineer', confidence: 0.83, evidence: [] },
      secondary_roles: [],
      seniority: { raw: 'Senior', normalized: 'senior', confidence: 0.84, evidence: [] },
      technologies: [
        { raw: 'Azure Data Factory', normalized: 'Azure Data Factory', category: 'tool', importance: 'required', confidence: 0.79, evidence: [] },
        { raw: 'SQL', normalized: 'SQL', category: 'language', importance: 'required', confidence: 0.91, evidence: [] }
      ],
      certifications: [],
      languages: [{ raw: 'Swedish', normalized: 'Swedish', proficiency: 'professional', importance: 'required', confidence: 0.9, evidence: [] }],
      sector: { raw: 'public sector', normalized: 'public', confidence: 0.88, evidence: [] },
      location: { raw: 'Remote with Stockholm meetings', city: 'Stockholm', country: 'Sweden', confidence: 0.7, evidence: [] },
      remote_mode: { raw: 'remote', normalized: 'remote', confidence: 0.86, evidence: [] },
      commercial: {
        start_date: '2026-06-01T00:00:00Z',
        start_date_raw: 'June',
        duration_raw: '10 months',
        duration_months: 10,
        allocation_percent: 100,
        positions_count: 3,
        rate_amount: 1050,
        rate_currency: 'SEK',
        rate_unit: 'hour',
        confidence: 0.79,
        evidence: []
      },
      summary: { text: 'Public data platform assignment with multiple consultant openings.', confidence: 0.81 }
    },
    quality: { overall_confidence: 0.79, review_status: 'partial', warnings: ['Exact start date inferred from month-only wording.'] }
  })
];
