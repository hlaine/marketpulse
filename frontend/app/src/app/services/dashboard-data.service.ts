import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { RequestSnapshot } from '../models/request-record.model';

@Injectable({
  providedIn: 'root'
})
export class DashboardDataService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';

  getSnapshot(): Observable<RequestSnapshot> {
    return this.http
      .get<RequestSnapshot>(`${this.apiBaseUrl}/analytics/snapshot`)
      .pipe(catchError(() => this.http.get<RequestSnapshot>('data/requests.json')));
  }
}
