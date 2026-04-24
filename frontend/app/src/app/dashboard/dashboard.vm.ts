import { ConsultingRequest } from '../models/consulting-request.model';

export type TimeRange = '24H' | '7D' | '30D' | '90D';
export type ViewId = 'volume' | 'roles' | 'remote' | 'quality';

export interface DashboardFilters {
  timeRange: TimeRange;
  sourceKind: string;
}

export interface KpiMetric {
  label: string;
  value: string;
  hint: string;
}

export interface DataPoint {
  label: string;
  value: number;
  hint: string;
}

export interface ViewSummary {
  id: ViewId;
  title: string;
  subtitle: string;
  hero: string;
  delta: string;
}

export interface DashboardVm {
  updatedAt: string;
  totalRequests: number;
  availableSourceKinds: string[];
  kpis: KpiMetric[];
  volume: {
    summary: ViewSummary;
    points: DataPoint[];
  };
  roles: {
    summary: ViewSummary;
    items: DataPoint[];
  };
  remote: {
    summary: ViewSummary;
    items: DataPoint[];
  };
  quality: {
    summary: ViewSummary;
    items: DataPoint[];
    averageConfidence: number;
  };
}

const timeRangeMs: Record<TimeRange, number> = {
  '24H': 24 * 60 * 60 * 1000,
  '7D': 7 * 24 * 60 * 60 * 1000,
  '30D': 30 * 24 * 60 * 60 * 1000,
  '90D': 90 * 24 * 60 * 60 * 1000
};

function sameDayLabel(iso: string | null): string {
  if (!iso) {
    return 'Unknown';
  }

  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric'
  }).format(new Date(iso));
}

function average(values: number[]): number {
  if (!values.length) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function percent(part: number, total: number): string {
  if (!total) {
    return '0%';
  }

  return `${Math.round((part / total) * 100)}%`;
}

function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatCurrencySek(value: number): string {
  return new Intl.NumberFormat('en-SE', {
    style: 'currency',
    currency: 'SEK',
    maximumFractionDigits: 0
  }).format(value);
}

function toCountPoints(counter: Map<string, number>, total: number): DataPoint[] {
  return Array.from(counter.entries())
    .sort((left, right) => right[1] - left[1])
    .map(([label, value]) => ({
      label,
      value,
      hint: `${percent(value, total)} of filtered requests`
    }));
}

export function filterRequests(requests: ConsultingRequest[], filters: DashboardFilters, now = new Date()): ConsultingRequest[] {
  const startTime = now.getTime() - timeRangeMs[filters.timeRange];

  return requests.filter((item) => {
    const receivedAt = item.source.received_at ? new Date(item.source.received_at).getTime() : 0;
    const inTimeRange = receivedAt >= startTime;
    const sourceMatches = filters.sourceKind === 'all' || item.source.kind === filters.sourceKind;

    return inTimeRange && sourceMatches;
  });
}

export function buildDashboardVm(requests: ConsultingRequest[], filters: DashboardFilters, now = new Date()): DashboardVm {
  const filtered = filterRequests(requests, filters, now);
  const safeRequests = filtered.length ? filtered : requests;
  const allSourceKinds = Array.from(new Set(requests.map((item) => item.source.kind))).sort();

  const volumeByDay = new Map<string, number>();
  for (const item of safeRequests) {
    const label = sameDayLabel(item.source.received_at);
    volumeByDay.set(label, (volumeByDay.get(label) ?? 0) + 1);
  }

  const volumePoints = Array.from(volumeByDay.entries()).map(([label, value]) => ({
    label,
    value,
    hint: `${value} requests received`
  }));

  const roleCounts = new Map<string, number>();
  const remoteCounts = new Map<string, number>();
  const qualityCounts = new Map<string, number>();
  const rateValues: number[] = [];
  const confidenceValues: number[] = [];

  for (const item of safeRequests) {
    const role = item.demand.primary_role.normalized ?? 'Unknown';
    const remoteMode = item.demand.remote_mode.normalized ?? 'unknown';
    const status = item.quality.review_status;

    roleCounts.set(role, (roleCounts.get(role) ?? 0) + 1);
    remoteCounts.set(remoteMode, (remoteCounts.get(remoteMode) ?? 0) + 1);
    qualityCounts.set(status, (qualityCounts.get(status) ?? 0) + 1);
    confidenceValues.push(item.quality.overall_confidence);

    if (item.demand.commercial.rate_amount) {
      rateValues.push(item.demand.commercial.rate_amount);
    }
  }

  const rolePoints = toCountPoints(roleCounts, safeRequests.length).slice(0, 5);
  const remotePoints = toCountPoints(remoteCounts, safeRequests.length);
  const qualityPoints = toCountPoints(qualityCounts, safeRequests.length);
  const avgConfidence = average(confidenceValues);
  const avgRate = average(rateValues);
  const topRole = rolePoints[0];
  const topRemote = remotePoints[0];
  const reviewNeeded = (qualityCounts.get('needs_review') ?? 0) + (qualityCounts.get('failed') ?? 0);

  return {
    updatedAt: new Intl.DateTimeFormat('en', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(now),
    totalRequests: safeRequests.length,
    availableSourceKinds: ['all', ...allSourceKinds],
    kpis: [
      {
        label: 'Filtered requests',
        value: String(safeRequests.length),
        hint: `${filters.timeRange} window`
      },
      {
        label: 'Average confidence',
        value: formatConfidence(avgConfidence),
        hint: 'Across extraction quality'
      },
      {
        label: 'Average rate',
        value: avgRate ? formatCurrencySek(avgRate) : 'N/A',
        hint: 'Hourly rate, where present'
      },
      {
        label: 'Needs review',
        value: String(reviewNeeded),
        hint: 'Requests that need human attention'
      }
    ],
    volume: {
      summary: {
        id: 'volume',
        title: 'Request volume',
        subtitle: 'Incoming consulting requests over time',
        hero: `${safeRequests.length} requests`,
        delta: volumePoints.length ? `${volumePoints[volumePoints.length - 1]?.label} latest point` : 'No volume data'
      },
      points: volumePoints
    },
    roles: {
      summary: {
        id: 'roles',
        title: 'Role distribution',
        subtitle: 'Most requested primary roles',
        hero: topRole ? topRole.label : 'No role data',
        delta: topRole ? `${topRole.value} matching requests` : 'No role data'
      },
      items: rolePoints
    },
    remote: {
      summary: {
        id: 'remote',
        title: 'Remote mode mix',
        subtitle: 'How assignments expect people to work',
        hero: topRemote ? topRemote.label : 'No remote data',
        delta: topRemote ? topRemote.hint : 'No remote data'
      },
      items: remotePoints
    },
    quality: {
      summary: {
        id: 'quality',
        title: 'Extraction quality',
        subtitle: 'Confidence and review readiness',
        hero: formatConfidence(avgConfidence),
        delta: `${reviewNeeded} requests need review`
      },
      items: qualityPoints,
      averageConfidence: avgConfidence
    }
  };
}
