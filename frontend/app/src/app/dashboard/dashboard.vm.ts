import { RequestRecord } from '../models/request-record.model';

export type TimeRange = '30D' | '3M' | '1Y' | '5Y' | '10Y';

export interface DashboardFilters {
  timeRange: TimeRange;
}

export interface DataPoint {
  label: string;
  value: number;
}

export interface RoleRemotePoint {
  label: string;
  total: number;
  remoteHybrid: number;
}

export interface PieSlice {
  label: string;
  value: number;
  percent: number;
}

export interface DashboardVm {
  updatedAt: string;
  snapshotNote: string;
  totalRequests: number;
  volumePoints: DataPoint[];
  ratePoints: DataPoint[];
  roleRemotePoints: RoleRemotePoint[];
  roleDistribution: PieSlice[];
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

function topRoleMap(records: RequestRecord[]): Map<string, number> {
  const counter = new Map<string, number>();

  for (const item of records) {
    const role = item.primary_role?.trim() || 'Unknown';
    counter.set(role, (counter.get(role) ?? 0) + 1);
  }

  return new Map(
    Array.from(counter.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
  );
}

export function filterRequests(requests: RequestRecord[], filters: DashboardFilters, now = effectiveNow(requests)): RequestRecord[] {
  const startTime = now.getTime() - timeRangeMs[filters.timeRange];

  return requests.filter((item) => parseDate(item.received_at) >= startTime);
}

export function buildDashboardVm(
  requests: RequestRecord[],
  filters: DashboardFilters,
  snapshotNote = 'Local SQLite snapshot for frontend analytics.',
  now = effectiveNow(requests)
): DashboardVm {
  const filtered = filterRequests(requests, filters, now);
  const safeRequests = filtered.length ? filtered : requests;

  const volumeByDay = new Map<string, number>();
  const ratesByDay = new Map<string, number[]>();
  const roleCounts = topRoleMap(safeRequests);
  const roleRemoteCounts = new Map<string, { total: number; remoteHybrid: number }>();

  for (const item of safeRequests) {
    const dayLabel = sameDayLabel(item.received_at);
    volumeByDay.set(dayLabel, (volumeByDay.get(dayLabel) ?? 0) + 1);

    if (item.rate_amount) {
      const bucket = ratesByDay.get(dayLabel) ?? [];
      bucket.push(item.rate_amount);
      ratesByDay.set(dayLabel, bucket);
    }

    const role = item.primary_role?.trim() || 'Unknown';
    if (roleCounts.has(role)) {
      const remoteMode = normalizeRemoteMode(item.remote_mode);
      const entry = roleRemoteCounts.get(role) ?? { total: 0, remoteHybrid: 0 };
      entry.total += 1;
      if (remoteMode === 'remote' || remoteMode === 'hybrid') {
        entry.remoteHybrid += 1;
      }
      roleRemoteCounts.set(role, entry);
    }
  }

  const volumePoints = Array.from(volumeByDay.entries()).map(([label, value]) => ({ label, value }));
  const ratePoints = Array.from(ratesByDay.entries()).map(([label, values]) => ({
    label,
    value: Math.round(average(values))
  }));

  const roleRemotePoints: RoleRemotePoint[] = Array.from(roleCounts.entries()).map(([label, total]) => ({
    label,
    total,
    remoteHybrid: roleRemoteCounts.get(label)?.remoteHybrid ?? 0
  }));

  const totalRoles = roleRemotePoints.reduce((sum, item) => sum + item.total, 0);
  const roleDistribution: PieSlice[] = roleRemotePoints.map((item) => ({
    label: item.label,
    value: item.total,
    percent: totalRoles ? (item.total / totalRoles) * 100 : 0
  }));

  return {
    updatedAt: new Intl.DateTimeFormat('en', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(now),
    snapshotNote,
    totalRequests: safeRequests.length,
    volumePoints,
    ratePoints,
    roleRemotePoints,
    roleDistribution
  };
}
