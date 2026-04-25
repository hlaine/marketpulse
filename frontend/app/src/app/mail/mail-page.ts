import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { MailboxEmail } from '../models/demo-mail.model';
import { DemoMailService } from '../services/demo-mail.service';

@Component({
  selector: 'app-mail-page',
  imports: [CommonModule, RouterLink],
  templateUrl: './mail-page.html',
  styleUrl: './mail-page.css'
})
export class MailPageComponent {
  private readonly demoMailService = inject(DemoMailService);

  protected readonly emails = this.demoMailService.emails;
  protected readonly selectedEmailId = this.demoMailService.selectedEmailId;
  protected readonly loadingRefresh = this.demoMailService.loadingRefresh;
  protected readonly forwardingEmailId = this.demoMailService.forwardingEmailId;
  protected readonly refreshError = this.demoMailService.refreshError;
  protected readonly selectedEmail = this.demoMailService.selectedEmail;

  protected refreshInbox(): void {
    this.demoMailService.refreshInbox();
  }

  protected selectEmail(emailId: string): void {
    this.demoMailService.selectEmail(emailId);
  }

  protected forwardSelectedEmail(): void {
    this.demoMailService.forwardSelectedEmail();
  }

  protected statusLabel(item: MailboxEmail): string {
    if (item.status === 'analyzing') {
      return 'Analyseras';
    }
    if (item.status === 'analyzed') {
      return 'Analyserad';
    }
    if (item.status === 'error') {
      return 'Fel';
    }
    return 'Ny';
  }

  protected senderName(value: string | null): string {
    if (!value) {
      return 'Okänd avsändare';
    }
    return value.split('<')[0].trim() || value;
  }

  protected formatDate(value: string | null): string {
    if (!value) {
      return 'Okänt datum';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat('sv-SE', {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(date);
  }
}
