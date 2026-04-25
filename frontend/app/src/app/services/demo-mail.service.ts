import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ConsultingRequestRecord,
  DemoEmail,
  DemoEmailResponse,
  DocumentUploadResponse,
  MailboxEmail
} from '../models/demo-mail.model';

@Injectable({
  providedIn: 'root'
})
export class DemoMailService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';

  readonly emails = signal<MailboxEmail[]>([]);
  readonly selectedEmailId = signal<string | null>(null);
  readonly loadingRefresh = signal(false);
  readonly forwardingEmailId = signal<string | null>(null);
  readonly refreshError = signal<string | null>(null);

  readonly selectedEmail = computed(() => {
    const selectedId = this.selectedEmailId();
    return this.emails().find((item) => item.email.id === selectedId) ?? null;
  });

  generateEmail(): Observable<DemoEmailResponse> {
    return this.http.post<DemoEmailResponse>(`${this.apiBaseUrl}/demo/emails`, {
      seed: this.createRefreshSeed()
    });
  }

  forwardToAnalysis(email: DemoEmail): Observable<DocumentUploadResponse> {
    const formData = new FormData();
    const filename = `${email.id.replace(/[^a-zA-Z0-9._-]/g, '-')}.json`;
    const payload = new Blob([JSON.stringify(email)], { type: 'application/json' });

    formData.append('file', payload, filename);
    formData.append('source_ref', `demo-mail://${email.id}`);

    if (email.subject) {
      formData.append('title', email.subject);
    }
    if (email.date) {
      formData.append('received_at', email.date);
    }

    return this.http.post<DocumentUploadResponse>(`${this.apiBaseUrl}/documents`, formData);
  }

  refreshInbox(): void {
    if (this.loadingRefresh()) {
      return;
    }

    this.loadingRefresh.set(true);
    this.refreshError.set(null);

    this.generateEmail().subscribe({
      next: (response) => {
        const item: MailboxEmail = {
          email: response.email,
          status: 'new',
          generatedBy: response.generated_by,
          generationWarnings: response.warnings ?? [],
          analysis: null,
          requestId: null,
          error: null
        };
        this.emails.update((current) => [item, ...current]);
        this.selectedEmailId.set(item.email.id);
        this.loadingRefresh.set(false);
      },
      error: () => {
        this.refreshError.set('Kunde inte hämta ett demo-mail från backend.');
        this.loadingRefresh.set(false);
      }
    });
  }

  selectEmail(emailId: string): void {
    this.selectedEmailId.set(emailId);
  }

  forwardSelectedEmail(): void {
    const selected = this.selectedEmail();
    if (!selected || selected.status === 'analyzed' || this.forwardingEmailId()) {
      return;
    }

    this.forwardingEmailId.set(selected.email.id);
    this.updateEmail(selected.email.id, {
      status: 'analyzing',
      error: null
    });

    this.forwardToAnalysis(selected.email).subscribe({
      next: (response) => {
        this.updateEmail(selected.email.id, {
          status: 'analyzed',
          analysis: buildAnalysis(response),
          requestId: response.request_id,
          error: null
        });
        this.forwardingEmailId.set(null);
      },
      error: () => {
        this.updateEmail(selected.email.id, {
          status: 'error',
          error: 'Analysen misslyckades. Kontrollera att backend kör och försök igen.'
        });
        this.forwardingEmailId.set(null);
      }
    });
  }

  private updateEmail(emailId: string, patch: Partial<MailboxEmail>): void {
    this.emails.update((current) =>
      current.map((item) => (item.email.id === emailId ? { ...item, ...patch } : item))
    );
  }

  private createRefreshSeed(): string {
    return `mail-refresh-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
}

function buildAnalysis(response: DocumentUploadResponse): string {
  const record = response.record;
  const role = value(record.demand.primary_role) ?? 'okänd roll';
  const seniority = value(record.demand.seniority) ?? 'okänd senioritet';
  const location = buildLocation(record);
  const commercial = buildCommercial(record);
  const technologies = record.demand.technologies
    .map((technology) => technology.normalized || technology.raw)
    .filter(Boolean)
    .join(', ');
  const confidence = record.quality.overall_confidence === null
    ? 'okänd'
    : `${Math.round(record.quality.overall_confidence * 100)}%`;
  const warnings = [...(response.warnings ?? []), ...(record.quality.warnings ?? [])]
    .filter((warning, index, all) => warning && all.indexOf(warning) === index);

  return [
    `Analysen är sparad i databasen som ${response.request_id}.`,
    `Roll: ${role} (${seniority}).`,
    `Plats: ${location}.`,
    `Kommersiellt: ${commercial}.`,
    `Tekniker: ${technologies || 'inga tydliga tekniker hittades'}.`,
    `Konfidens: ${confidence}.`,
    warnings.length ? `Att granska: ${warnings.join(' ')}` : 'Inga varningar från extraktionen.'
  ].join('\n');
}

function value(taggedValue: { normalized: string | null; raw: string | null }): string | null {
  return taggedValue.normalized || taggedValue.raw;
}

function buildLocation(record: ConsultingRequestRecord): string {
  const city = record.demand.location.city || record.demand.location.raw || 'okänd plats';
  const remoteMode = value(record.demand.remote_mode);
  return remoteMode && remoteMode !== 'unknown' ? `${city}, ${remoteMode}` : city;
}

function buildCommercial(record: ConsultingRequestRecord): string {
  const commercial = record.demand.commercial;
  const duration = commercial.duration_months ? `${commercial.duration_months} månader` : 'okänd längd';
  const rate = commercial.rate_amount
    ? `${commercial.rate_amount} ${commercial.rate_currency ?? 'SEK'}/${commercial.rate_unit === 'hour' ? 'h' : commercial.rate_unit ?? 'enhet'}`
    : 'okänd ersättning';
  return `${duration}, ${rate}`;
}
