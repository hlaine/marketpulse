import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';

import { FilterBarComponent } from '../components/filter-bar/filter-bar';
import { RequestRecord, RequestSnapshot } from '../models/request-record.model';
import { DashboardDataService } from '../services/dashboard-data.service';
import { buildDashboardVm, DashboardFilters, DataPoint, PieSlice, RoleRemotePoint, TimeRange } from './dashboard.vm';

@Component({
  selector: 'app-dashboard-page',
  imports: [CommonModule, FilterBarComponent],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.css'
})
export class DashboardPageComponent implements OnInit {
  private readonly dataService = inject(DashboardDataService);

  protected readonly requests = signal<RequestRecord[]>([]);
  protected readonly snapshot = signal<RequestSnapshot | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly filters = signal<DashboardFilters>({
    timeRange: '1Y'
  });

  protected readonly vm = computed(() => buildDashboardVm(
    this.requests(),
    this.filters(),
    this.snapshot()?.snapshot_note ?? 'Local SQLite snapshot for frontend analytics.'
  ));

  ngOnInit(): void {
    this.dataService.getSnapshot().subscribe({
      next: (snapshot) => {
        this.snapshot.set(snapshot);
        this.requests.set(snapshot.requests);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Could not load the local SQLite snapshot for the dashboard.');
        this.loading.set(false);
      }
    });
  }

  protected setTimeRange(timeRange: TimeRange): void {
    this.filters.set({ timeRange });
  }

  protected linePoints(points: DataPoint[]): string {
    if (!points.length) {
      return '';
    }

    const max = Math.max(...points.map((point) => point.value), 1);
    const minX = 2;
    const maxX = 98;
    const topY = 10;
    const bottomY = 90;

    return points
      .map((point, index) => {
        const x = points.length === 1 ? 50 : minX + (index / (points.length - 1)) * (maxX - minX);
        const y = bottomY - (point.value / max) * (bottomY - topY);

        return `${x},${y}`;
      })
      .join(' ');
  }

  protected maxPointValue(points: DataPoint[]): number {
    return Math.max(...points.map((point) => point.value), 1);
  }

  protected axisTicks(points: DataPoint[], steps = 4): number[] {
    const max = this.maxPointValue(points);
    return Array.from({ length: steps + 1 }, (_, index) => Math.round((max / steps) * (steps - index)));
  }

  protected xAxisLabels(points: DataPoint[], count = 6): DataPoint[] {
    if (points.length <= count) {
      return points;
    }

    const step = (points.length - 1) / (count - 1);

    return Array.from({ length: count }, (_, index) => points[Math.round(index * step)]).filter(
      (point, index, items) => index === items.findIndex((item) => item.label === point.label)
    );
  }

  protected barHeight(value: number, max: number): number {
    return max ? 12 + (value / max) * 68 : 12;
  }

  protected maxTotal(points: RoleRemotePoint[]): number {
    return Math.max(...points.map((point) => point.total), 1);
  }

  protected formatRateTick(value: number): string {
    return `${value}`;
  }

  protected pieSegments(slices: PieSlice[]): Array<PieSlice & { dash: string; rotateOffset: number }> {
    let offset = 0;

    return slices.map((slice) => {
      const dash = `${slice.percent} ${100 - slice.percent}`;
      const rotateOffset = offset;
      offset += slice.percent;
      return { ...slice, dash, rotateOffset };
    });
  }
}
