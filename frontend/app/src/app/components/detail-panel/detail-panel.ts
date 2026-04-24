import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';

import { DashboardVm, ViewId } from '../../dashboard/dashboard.vm';

@Component({
  selector: 'app-detail-panel',
  imports: [CommonModule],
  templateUrl: './detail-panel.html',
  styleUrl: './detail-panel.css'
})
export class DetailPanelComponent {
  readonly vm = input.required<DashboardVm>();
  readonly activeView = input.required<ViewId>();

  protected detailItems(): Array<{ label: string; value: number; hint: string }> {
    const data = this.vm();
    const view = this.activeView();

    switch (view) {
      case 'roles':
        return data.roles.items;
      case 'remote':
        return data.remote.items;
      case 'quality':
        return data.quality.items;
      case 'volume':
      default:
        return data.volume.points;
    }
  }

  protected title(): string {
    const data = this.vm();
    const view = this.activeView();

    switch (view) {
      case 'roles':
        return data.roles.summary.title;
      case 'remote':
        return data.remote.summary.title;
      case 'quality':
        return data.quality.summary.title;
      case 'volume':
      default:
        return data.volume.summary.title;
    }
  }

  protected summary(): string {
    const data = this.vm();
    const view = this.activeView();

    switch (view) {
      case 'roles':
        return 'Use this view to compare which consultant profiles are currently dominating the incoming flow.';
      case 'remote':
        return 'Use this view to understand how delivery expectations are shifting between onsite, hybrid, and remote work.';
      case 'quality':
        return 'Use this view to spot records that need manual review before they are used as decision support.';
      case 'volume':
      default:
        return 'Use this view to scan incoming request tempo and see where the current time window is most active.';
    }
  }
}
