import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';

import { ChatMessage } from '../models/chat.model';
import { ChatService } from '../services/chat.service';

@Component({
  selector: 'app-chat-page',
  imports: [CommonModule, RouterLink],
  templateUrl: './chat-page.html',
  styleUrl: './chat-page.css'
})
export class ChatPageComponent {
  private readonly chatService = inject(ChatService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly draft = signal('hur många förfrågningar om .net utvecklare inkom under 2025?');
  protected readonly loading = signal(false);
  protected readonly messages = signal<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Ställ en fråga om den lokala konsultdatabasen.'
    }
  ]);

  protected updateDraft(value: string): void {
    this.draft.set(value);
  }

  protected sendMessage(): void {
    const message = this.draft().trim();
    if (!message || this.loading()) {
      return;
    }

    this.messages.update((current) => [...current, { role: 'user', content: message }]);
    this.draft.set('');
    this.loading.set(true);

    this.chatService
      .ask(message)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response) => {
          this.messages.update((current) => [
            ...current,
            {
              role: 'assistant',
              content: response.answer,
              sql: response.sql,
              rows: response.rows,
              warnings: response.warnings
            }
          ]);
          this.loading.set(false);
        },
        error: () => {
          this.messages.update((current) => [
            ...current,
            {
              role: 'assistant',
              content: 'Jag kunde inte hämta ett svar från backend just nu.',
              error: true
            }
          ]);
          this.loading.set(false);
        }
      });
  }

  protected handleKeydown(event: KeyboardEvent): void {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
