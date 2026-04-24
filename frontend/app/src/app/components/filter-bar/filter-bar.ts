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
  readonly activeTimeRange = input<TimeRange>('1Y');
  readonly timeRangeChange = output<TimeRange>();

  protected readonly timeRanges: Array<{ value: TimeRange; label: string }> = [
    { value: '30D', label: '30 days' },
    { value: '3M', label: '3 months' },
    { value: '1Y', label: '1 year' },
    { value: '5Y', label: '5 years' },
    { value: '10Y', label: '10 years' }
  ];

  protected selectedIndex(): number {
    return this.timeRanges.findIndex((item) => item.value === this.activeTimeRange());
  }

  protected onSliderChange(rawValue: string): void {
    const index = Number(rawValue);
    const selected = this.timeRanges[index];

    if (selected) {
      this.timeRangeChange.emit(selected.value);
    }
  }
}
