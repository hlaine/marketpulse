import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { FilterBarComponent } from '../components/filter-bar/filter-bar';
import { RequestRecord, RequestSnapshot } from '../models/request-record.model';
import { DashboardDataService } from '../services/dashboard-data.service';
import {
  buildDashboardVm,
  ChartPoint,
  DashboardFilters,
  DataQualityVm,
  LocationRow,
  RateByRoleRow,
  RoleRankingRow,
  RoleRemotePoint,
  TimeRange
} from './dashboard.vm';

@Component({
  selector: 'app-dashboard-page',
  imports: [CommonModule, RouterLink, FilterBarComponent],
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
    this.snapshot()?.snapshot_note ?? 'Statistik och insikter om konsultförfrågningar från partners och konsultmäklare'
  ));

  ngOnInit(): void {
    this.dataService.getSnapshot().subscribe({
      next: (snapshot) => {
        this.snapshot.set(snapshot);
        this.requests.set(snapshot.requests);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Det gick inte att läsa in den lokala SQLite-snapshoten för dashboarden.');
        this.loading.set(false);
      }
    });
  }

  protected setTimeRange(timeRange: TimeRange): void {
    this.filters.set({ timeRange });
  }

  protected linePath(points: ChartPoint[], startAtZero = true): string {
    const values = points.map((point) => point.value).filter((value): value is number => value !== null);
    if (!values.length) {
      return '';
    }

    const domain = this.yDomain(points, startAtZero);
    let path = '';
    let segmentStarted = false;

    points.forEach((point, index) => {
      if (point.value === null) {
        segmentStarted = false;
        return;
      }

      const x = points.length === 1 ? 50 : 4 + (index / (points.length - 1)) * 92;
      const y = this.valueToY(point.value, domain.min, domain.max);

      if (!segmentStarted) {
        path += `M ${x} ${y}`;
        segmentStarted = true;
      } else {
        path += ` L ${x} ${y}`;
      }
    });

    return path;
  }

  protected xAxisLabels(points: ChartPoint[], count = 6): ChartPoint[] {
    if (points.length <= count) {
      return points;
    }

    const step = (points.length - 1) / (count - 1);
    const labels = Array.from({ length: count }, (_, index) => points[Math.round(index * step)]);

    return labels.filter((point, index, items) => index === items.findIndex((item) => item.label === point.label));
  }

  protected yAxisTicks(points: ChartPoint[], startAtZero = true, steps = 4): number[] {
    const domain = this.yDomain(points, startAtZero);
    const values = Array.from({ length: steps + 1 }, (_, index) => {
      const ratio = 1 - index / steps;
      return domain.min + (domain.max - domain.min) * ratio;
    });

    return values.map((value) => Math.round(value));
  }

  protected kpiToneClass(tone: string | undefined): string {
    return tone ? `kpi-card--${tone}` : 'kpi-card--neutral';
  }

  protected rankingWidth(row: RoleRankingRow, max: number): number {
    return max ? (row.value / max) * 100 : 0;
  }

  protected remoteHeight(value: number, max: number): number {
    return max ? 12 + (value / max) * 74 : 12;
  }

  protected roleMixMax(points: RoleRemotePoint[]): number {
    return Math.max(...points.map((point) => point.total), 1);
  }

  protected rankingMax(rows: RoleRankingRow[]): number {
    return Math.max(...rows.map((row) => row.value), 1);
  }

  protected rateByRoleMax(rows: RateByRoleRow[]): number {
    return Math.max(...rows.map((row) => row.max), 1);
  }

  protected locationMax(rows: LocationRow[]): number {
    return Math.max(...rows.map((row) => row.total), 1);
  }

  protected brokerMax(rows: { requests: number }[]): number {
    return Math.max(...rows.map((row) => row.requests), 1);
  }

  protected rateRangeOffset(row: RateByRoleRow, max: number): number {
    return max ? (row.min / max) * 100 : 0;
  }

  protected rateRangeWidth(row: RateByRoleRow, max: number): number {
    return max ? ((row.max - row.min) / max) * 100 : 0;
  }

  protected rateMedianOffset(row: RateByRoleRow, max: number): number {
    return max ? (row.median / max) * 100 : 0;
  }

  protected locationShare(value: number, total: number): number {
    return total ? (value / total) * 100 : 0;
  }

  protected qualityLabel(quality: DataQualityVm): string {
    if (quality.averageConfidence === null) {
      return 'Konfidens saknas';
    }

    return `${Math.round(quality.averageConfidence * 100)}% genomsnittlig konfidens`;
  }

  private yDomain(points: ChartPoint[], startAtZero: boolean): { min: number; max: number } {
    const values = points.map((point) => point.value).filter((value): value is number => value !== null);
    if (!values.length) {
      return { min: 0, max: 1 };
    }

    const min = Math.min(...values);
    const max = Math.max(...values);

    if (startAtZero) {
      return { min: 0, max: max > 0 ? max * 1.1 : 1 };
    }

    const spread = Math.max(max - min, max * 0.12, 1);
    return {
      min: Math.max(0, min - spread * 0.4),
      max: max + spread * 0.4
    };
  }

  private valueToY(value: number, min: number, max: number): number {
    const top = 10;
    const bottom = 88;
    const domain = Math.max(max - min, 1);
    const normalized = (value - min) / domain;
    return bottom - normalized * (bottom - top);
  }
}
