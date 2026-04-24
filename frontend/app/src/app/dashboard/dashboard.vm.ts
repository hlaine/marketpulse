import { RequestRecord } from '../models/request-record.model';

export type TimeRange = '30D' | '3M' | '1Y' | '5Y' | '10Y';
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
  snapshotNote: string;
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
  '30D': 30 * 24 * 60 * 60 * 1000,
  '3M': 90 * 24 * 60 * 60 * 1000,
  '1Y': 365 * 24 * 60 * 60 * 1000,
  '5Y': 5 * 365 * 24 * 60 * 60 * 1000,
  '10Y': 10 * 365 * 24 * 60 * 60 * 1000
};

function parseDate(value: string | null): number {
  return value ? new Date(value).getTime() : 0;
}

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

function effectiveNow(requests: RequestRecord[], fallback = new Date()): Date {
  const latest = Math.max(...requests.map((item) => parseDate(item.received_at)), 0);
  return latest ? new Date(latest) : fallback;
}

function normalizeRemoteMode(value: string | null): string {
  const cleaned = (value ?? '').trim().toLowerCase();

  if (!cleaned) {
    return 'unknown';
  }

  if (cleaned === 'on-site' || cleaned === 'onsite') {
    return 'onsite';
  }

  return cleaned;
}

export function filterRequests(requests: RequestRecord[], filters: DashboardFilters, now = effectiveNow(requests)): RequestRecord[] {
  const startTime = now.getTime() - timeRangeMs[filters.timeRange];

  return requests.filter((item) => {
    const receivedAt = parseDate(item.received_at);
    const inTimeRange = receivedAt >= startTime;
    const sourceMatches = filters.sourceKind === 'all' || item.source_kind === filters.sourceKind;

    return inTimeRange && sourceMatches;
  });
}

export function buildDashboardVm(
  requests: RequestRecord[],
  filters: DashboardFilters,
  snapshotNote = 'Local SQLite snapshot for frontend analytics.',
  now = effectiveNow(requests)
): DashboardVm {
  const filtered = filterRequests(requests, filters, now);
  const safeRequests = filtered.length ? filtered : requests;
  const allSourceKinds = Array.from(new Set(requests.map((item) => item.source_kind || 'unknown'))).sort();

  const volumeByDay = new Map<string, number>();
  for (const item of safeRequests) {
    const label = sameDayLabel(item.received_at);
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
    const role = item.primary_role?.trim() || 'Unknown';
    const remoteMode = normalizeRemoteMode(item.remote_mode);
    const status = item.review_status?.trim() || 'unknown';

    roleCounts.set(role, (roleCounts.get(role) ?? 0) + 1);
    remoteCounts.set(remoteMode, (remoteCounts.get(remoteMode) ?? 0) + 1);
    qualityCounts.set(status, (qualityCounts.get(status) ?? 0) + 1);
    confidenceValues.push(item.overall_confidence ?? 0);

    if (item.rate_amount) {
      rateValues.push(item.rate_amount);
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
    snapshotNote,
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
