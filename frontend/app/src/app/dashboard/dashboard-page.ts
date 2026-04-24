import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';

import { DetailPanelComponent } from '../components/detail-panel/detail-panel';
import { FilterBarComponent } from '../components/filter-bar/filter-bar';
import { StatCardComponent } from '../components/stat-card/stat-card';
import { RequestRecord, RequestSnapshot } from '../models/request-record.model';
import { DashboardDataService } from '../services/dashboard-data.service';
import { buildDashboardVm, DashboardFilters, DataPoint, TimeRange, ViewId } from './dashboard.vm';

@Component({
  selector: 'app-dashboard-page',
  imports: [CommonModule, FilterBarComponent, StatCardComponent, DetailPanelComponent],
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
    timeRange: '1Y',
    sourceKind: 'all'
  });
  protected readonly activeView = signal<ViewId>('volume');

  protected readonly vm = computed(() => buildDashboardVm(
    this.requests(),
    this.filters(),
    this.snapshot()?.snapshot_note ?? 'Local SQLite snapshot for frontend analytics.'
  ));
  protected readonly heroRequest = computed(() => this.requests()[this.requests().length - 1] ?? null);

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
    this.filters.update((current) => ({ ...current, timeRange }));
  }

  protected setSourceKind(sourceKind: string): void {
    this.filters.update((current) => ({ ...current, sourceKind }));
  }

  protected resetFilters(): void {
    this.filters.set({
      timeRange: '1Y',
      sourceKind: 'all'
    });
    this.activeView.set('volume');
  }

  protected selectView(viewId: ViewId): void {
    this.activeView.set(viewId);
  }

  protected chartPoints(points: DataPoint[]): string {
    if (!points.length) {
      return '';
    }

    const max = Math.max(...points.map((point) => point.value), 1);

    return points
      .map((point, index) => {
        const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
        const y = 100 - (point.value / max) * 100;

        return `${x},${y}`;
      })
      .join(' ');
  }

  protected maxPointValue(points: DataPoint[]): number {
    return Math.max(...points.map((point) => point.value), 1);
  }

  protected totalFromPoints(points: DataPoint[]): number {
    return points.reduce((sum, point) => sum + point.value, 0);
  }
}
