import { CommonModule } from '@angular/common';
import { Component, input, output } from '@angular/core';

import { TimeRange } from '../../dashboard/dashboard.vm';

@Component({
  selector: 'app-filter-bar',
  imports: [CommonModule],
  templateUrl: './filter-bar.html',
  styleUrl: './filter-bar.css'
})
export class FilterBarComponent {
  readonly activeTimeRange = input<TimeRange>('30D');
  readonly activeSourceKind = input('all');
  readonly sourceKinds = input<string[]>([]);

  readonly timeRangeChange = output<TimeRange>();
  readonly sourceKindChange = output<string>();
  readonly reset = output<void>();

  protected readonly timeRanges: TimeRange[] = ['24H', '7D', '30D', '90D'];
}
