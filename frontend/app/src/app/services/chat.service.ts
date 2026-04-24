import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ChatRequest, ChatResponse } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';

  ask(message: string, conversationId: string | null = null): Observable<ChatResponse> {
    const payload: ChatRequest = {
      message,
      conversation_id: conversationId
    };

    return this.http.post<ChatResponse>(`${this.apiBaseUrl}/chat`, payload);
  }
}
