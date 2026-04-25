import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';

import { RequestSnapshot } from '../models/request-record.model';
import { DashboardDataService } from './dashboard-data.service';

const SNAPSHOT: RequestSnapshot = {
  generated_at: '2026-04-25T10:00:00Z',
  database_path: 'db/marketpulse.sqlite3',
  snapshot_note: 'test snapshot',
  row_count: 0,
  requests: []
};

describe('DashboardDataService', () => {
  let service: DashboardDataService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(DashboardDataService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('loads the live backend snapshot first', () => {
    let result: RequestSnapshot | null = null;

    service.getSnapshot().subscribe((snapshot) => {
      result = snapshot;
    });

    const request = http.expectOne('http://127.0.0.1:8000/analytics/snapshot');
    expect(request.request.method).toBe('GET');
    request.flush(SNAPSHOT);

    expect(result).toEqual(SNAPSHOT);
  });

  it('falls back to the static snapshot when the backend is unavailable', () => {
    let result: RequestSnapshot | null = null;

    service.getSnapshot().subscribe((snapshot) => {
      result = snapshot;
    });

    const liveRequest = http.expectOne('http://127.0.0.1:8000/analytics/snapshot');
    liveRequest.flush('offline', { status: 0, statusText: 'Offline' });

    const fallbackRequest = http.expectOne('data/requests.json');
    expect(fallbackRequest.request.method).toBe('GET');
    fallbackRequest.flush(SNAPSHOT);

    expect(result).toEqual(SNAPSHOT);
  });
});
