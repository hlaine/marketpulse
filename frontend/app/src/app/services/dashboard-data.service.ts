import { Injectable } from '@angular/core';

import { MOCK_CONSULTING_REQUESTS } from '../mock-data/mock-requests';
import { ConsultingRequest } from '../models/consulting-request.model';

@Injectable({
  providedIn: 'root'
})
export class DashboardDataService {
  getRequests(): ConsultingRequest[] {
    return MOCK_CONSULTING_REQUESTS;
  }
}
