import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { RequestSnapshot } from '../models/request-record.model';

@Injectable({
  providedIn: 'root'
})
export class DashboardDataService {
  private readonly http = inject(HttpClient);

  getSnapshot(): Observable<RequestSnapshot> {
    return this.http.get<RequestSnapshot>('data/requests.json');
  }
}
