import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { DemoEmail, DocumentUploadResponse } from '../models/demo-mail.model';
import { DemoMailService } from './demo-mail.service';

const EMAIL: DemoEmail = {
  id: 'demo-123',
  date: '2026-04-25T10:00:00Z',
  subject: 'Ny förfrågan: Backend Engineer',
  from: 'Viktor Olsson <viktor.olsson@byteforce.se>',
  to: 'inbox@dummy.se',
  cc: '',
  body: '<html><body><p>Hej</p></body></html>'
};

const UPLOAD_RESPONSE: DocumentUploadResponse = {
  request_id: 'req-demo',
  stored: true,
  warnings: [],
  record: {
    request_id: 'req-demo',
    demand: {
      primary_role: {
        raw: 'Backend Engineer',
        normalized: 'Backend Engineer'
      },
      seniority: {
        raw: 'Senior',
        normalized: 'senior'
      },
      technologies: [
        {
          raw: 'Java',
          normalized: 'Java',
          category: 'language'
        },
        {
          raw: 'AWS',
          normalized: 'AWS',
          category: 'cloud'
        }
      ],
      location: {
        city: 'Stockholm',
        raw: 'Stockholm / hybrid'
      },
      remote_mode: {
        raw: 'Stockholm / hybrid',
        normalized: 'hybrid'
      },
      commercial: {
        duration_months: 6,
        rate_amount: 950,
        rate_currency: 'SEK',
        rate_unit: 'hour'
      },
      summary: {
        text: 'Request for a Backend Engineer.'
      }
    },
    quality: {
      overall_confidence: 0.91,
      review_status: 'ok',
      warnings: []
    }
  }
};

describe('DemoMailService', () => {
  let service: DemoMailService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(DemoMailService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('requests a generated demo email', () => {
    service.generateEmail().subscribe();

    const request = http.expectOne('http://127.0.0.1:8000/demo/emails');
    expect(request.request.method).toBe('POST');
    expect(request.request.body.seed).toMatch(/^mail-refresh-/);
    request.flush({ email: EMAIL, generated_by: 'fallback', warnings: [] });
  });

  it('uses a new seed for each generated demo email request', () => {
    service.generateEmail().subscribe();
    service.generateEmail().subscribe();

    const requests = http.match('http://127.0.0.1:8000/demo/emails');
    expect(requests.length).toBe(2);
    expect(requests[0].request.body.seed).toMatch(/^mail-refresh-/);
    expect(requests[1].request.body.seed).toMatch(/^mail-refresh-/);
    expect(requests[0].request.body.seed).not.toBe(requests[1].request.body.seed);
    requests.forEach((request) => request.flush({ email: EMAIL, generated_by: 'fallback', warnings: [] }));
  });

  it('forwards an email as a JSON upload to the documents endpoint', () => {
    service.forwardToAnalysis(EMAIL).subscribe();

    const request = http.expectOne('http://127.0.0.1:8000/documents');
    const body = request.request.body as FormData;

    expect(request.request.method).toBe('POST');
    expect(body.get('title')).toBe(EMAIL.subject);
    expect(body.get('received_at')).toBe(EMAIL.date);
    expect(body.get('source_ref')).toBe(`demo-mail://${EMAIL.id}`);
    expect(body.get('file')).toBeTruthy();
    request.flush(UPLOAD_RESPONSE);
  });

  it('keeps generated inbox state in the service', () => {
    service.refreshInbox();

    const request = http.expectOne('http://127.0.0.1:8000/demo/emails');
    request.flush({ email: EMAIL, generated_by: 'fallback', warnings: ['fallback used'] });

    expect(service.emails().length).toBe(1);
    expect(service.emails()[0].email).toEqual(EMAIL);
    expect(service.emails()[0].status).toBe('new');
    expect(service.emails()[0].generationWarnings).toEqual(['fallback used']);
    expect(service.selectedEmailId()).toBe(EMAIL.id);
    expect(service.selectedEmail()?.email.id).toBe(EMAIL.id);
    expect(service.loadingRefresh()).toBe(false);
  });

  it('stores the selected email id independently of the component lifecycle', () => {
    service.emails.set([
      {
        email: EMAIL,
        status: 'new',
        generatedBy: 'fallback',
        generationWarnings: [],
        analysis: null,
        requestId: null,
        error: null
      }
    ]);

    service.selectEmail(EMAIL.id);

    expect(service.selectedEmailId()).toBe(EMAIL.id);
    expect(service.selectedEmail()?.email).toEqual(EMAIL);
  });

  it('marks the selected email as analyzed after forwarding succeeds', () => {
    service.refreshInbox();
    http.expectOne('http://127.0.0.1:8000/demo/emails').flush({
      email: EMAIL,
      generated_by: 'fallback',
      warnings: []
    });

    service.forwardSelectedEmail();

    const request = http.expectOne('http://127.0.0.1:8000/documents');
    expect(service.forwardingEmailId()).toBe(EMAIL.id);
    expect(service.emails()[0].status).toBe('analyzing');
    request.flush(UPLOAD_RESPONSE);

    expect(service.forwardingEmailId()).toBeNull();
    expect(service.emails()[0].status).toBe('analyzed');
    expect(service.emails()[0].requestId).toBe('req-demo');
    expect(service.emails()[0].analysis).toContain('Analysen är sparad i databasen som req-demo.');
    expect(service.emails()[0].analysis).toContain('Backend Engineer');
  });

  it('marks the selected email as error when forwarding fails', () => {
    service.refreshInbox();
    http.expectOne('http://127.0.0.1:8000/demo/emails').flush({
      email: EMAIL,
      generated_by: 'fallback',
      warnings: []
    });

    service.forwardSelectedEmail();

    const request = http.expectOne('http://127.0.0.1:8000/documents');
    request.flush('backend unavailable', { status: 502, statusText: 'Bad Gateway' });

    expect(service.forwardingEmailId()).toBeNull();
    expect(service.emails()[0].status).toBe('error');
    expect(service.emails()[0].error).toContain('Analysen misslyckades');
  });
});
