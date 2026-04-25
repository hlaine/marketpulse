import { RequestRecord } from '../models/request-record.model';

export type TimeRange = '30D' | '3M' | '1Y' | '5Y' | '10Y';

export interface DashboardFilters {
  timeRange: TimeRange;
}

export interface ChartPoint {
  label: string;
  shortLabel: string;
  value: number | null;
}

export interface KpiCard {
  label: string;
  value: string;
  detail?: string;
  tone?: 'neutral' | 'positive' | 'negative';
}

export interface InsightCard {
  label: string;
  text: string;
  detail?: string;
}

export interface RoleRankingRow {
  label: string;
  value: number;
  share: number;
}

export interface RoleRemotePoint {
  label: string;
  total: number;
  remoteHybrid: number;
}

export interface RateByRoleRow {
  label: string;
  median: number;
  min: number;
  max: number;
  count: number;
}

export interface LocationRow {
  label: string;
  total: number;
  remote: number;
  hybrid: number;
  onsite: number;
}

export interface BrokerRow {
  label: string;
  requests: number;
  topRole: string;
  averageRate: number | null;
  remoteShare: number;
}

export interface DataQualityVm {
  averageConfidence: number | null;
  reviewNeeded: number;
  missingFields: Array<{ label: string; count: number }>;
}

export interface RequestRow {
  receivedAt: string;
  role: string;
  location: string;
  remoteMode: string;
  rate: string;
  duration: string;
  broker: string;
  quality: string;
}

export interface DashboardVm {
  updatedAt: string;
  title: string;
  subtitle: string;
  rangeLabel: string;
  totalRequests: number;
  hasResults: boolean;
  kpis: KpiCard[];
  insights: InsightCard[];
  demandTrend: ChartPoint[];
  roleRanking: RoleRankingRow[];
  roleRemoteMix: RoleRemotePoint[];
  rateTrend: ChartPoint[];
  rateByRole: RateByRoleRow[];
  locations: LocationRow[];
  brokers: BrokerRow[];
  dataQuality: DataQualityVm;
  requestRows: RequestRow[];
  rateUnitLabel: string;
}

interface NormalizedRequest {
  receivedAtMs: number;
  receivedAt: string | null;
  role: string;
  remoteMode: 'Distans' | 'Hybrid' | 'På plats' | 'Okänt';
  location: string;
  sector: string;
  broker: string;
  durationMonths: number | null;
  rateAmount: number | null;
  rateCurrency: string;
  rateUnit: string;
  reviewStatus: string;
  overallConfidence: number | null;
}

type BucketSize = 'day' | 'week' | 'month' | 'quarter';

const dayMs = 24 * 60 * 60 * 1000;

const timeRangeMs: Record<TimeRange, number> = {
  '30D': 30 * dayMs,
  '3M': 90 * dayMs,
  '1Y': 365 * dayMs,
  '5Y': 5 * 365 * dayMs,
  '10Y': 10 * 365 * dayMs
};

const timeRangeLabels: Record<TimeRange, string> = {
  '30D': '30 dagar',
  '3M': '3 månader',
  '1Y': '1 år',
  '5Y': '5 år',
  '10Y': '10 år'
};

function parseDate(value: string | null): number {
  return value ? new Date(value).getTime() : 0;
}

function titleCase(value: string): string {
  return value
    .split(/[\s/_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ');
}

function normalizeText(value: string | null | undefined, fallback = 'Okänt'): string {
  const cleaned = (value ?? '').trim();
  if (!cleaned) {
    return fallback;
  }

  const lowered = cleaned.toLowerCase();
  if (['unknown', 'n/a', 'na', 'none', 'null', 'undefined'].includes(lowered)) {
    return fallback;
  }

  return cleaned.replace(/\s+/g, ' ');
}

function normalizeRole(value: string | null): string {
  return normalizeText(value);
}

function normalizeRemoteMode(value: string | null): 'Distans' | 'Hybrid' | 'På plats' | 'Okänt' {
  const cleaned = normalizeText(value, 'Okänt').toLowerCase();

  if (['remote', 'fully remote'].includes(cleaned)) {
    return 'Distans';
  }

  if (['hybrid', 'remote_or_hybrid', 'remote/hybrid'].includes(cleaned)) {
    return 'Hybrid';
  }

  if (['on-site', 'onsite', 'on site'].includes(cleaned)) {
    return 'På plats';
  }

  return 'Okänt';
}

function normalizeSector(value: string | null): string {
  const sector = normalizeText(value);
  return sector === 'Okänt' ? sector : titleCase(sector);
}

function normalizeBroker(record: RequestRecord): string {
  return normalizeText(record.sender_organization ?? record.sender_domain);
}

function normalizeRateUnit(value: string | null): string {
  const unit = normalizeText(value, '').toLowerCase();
  if (['hour', 'hourly', 'hr', 'h'].includes(unit)) {
    return 'hour';
  }

  return unit || 'unknown';
}

function isHourlyRate(record: NormalizedRequest): boolean {
  return record.rateAmount !== null && record.rateUnit === 'hour';
}

function average(values: number[]): number | null {
  if (!values.length) {
    return null;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values: number[]): number | null {
  if (!values.length) {
    return null;
  }

  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);

  if (sorted.length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2;
  }

  return sorted[middle];
}

function percentage(part: number, total: number): number {
  return total ? (part / total) * 100 : 0;
}

function formatPercent(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

function formatSignedDelta(value: number): string {
  if (value > 0) {
    return `+${value}`;
  }

  return `${value}`;
}

function formatComparison(current: number, previous: number, noun: string): string | undefined {
  if (!previous && !current) {
    return undefined;
  }

  if (!previous && current) {
    return 'Ny aktivitet jämfört med föregående period';
  }

  const diff = current - previous;
  const change = Math.round((diff / previous) * 100);
  return `${formatSignedDelta(change)}% jämfört med föregående ${noun}`;
}

function formatDateLabel(value: string | null): string {
  if (!value) {
    return 'Okänt';
  }

  return new Intl.DateTimeFormat('sv-SE', {
    month: 'short',
    day: 'numeric'
  }).format(new Date(value));
}

function formatDateTimeLabel(timestamp: number): string {
  return new Intl.DateTimeFormat('sv-SE', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(timestamp));
}

function formatMonthLabel(date: Date): string {
  return new Intl.DateTimeFormat('sv-SE', { month: 'short', year: '2-digit' }).format(date);
}

function formatQuarterLabel(date: Date): string {
  const quarter = Math.floor(date.getUTCMonth() / 3) + 1;
  return `Q${quarter} ${String(date.getUTCFullYear()).slice(-2)}`;
}

function bucketSizeForRange(timeRange: TimeRange): BucketSize {
  switch (timeRange) {
    case '30D':
      return 'day';
    case '3M':
      return 'week';
    case '1Y':
      return 'month';
    case '5Y':
    case '10Y':
      return 'quarter';
  }
}

function bucketStart(timestamp: number, bucketSize: BucketSize): Date {
  const date = new Date(timestamp);
  const year = date.getUTCFullYear();
  const month = date.getUTCMonth();
  const day = date.getUTCDate();

  if (bucketSize === 'day') {
    return new Date(Date.UTC(year, month, day));
  }

  if (bucketSize === 'week') {
    const start = new Date(Date.UTC(year, month, day));
    const weekday = start.getUTCDay() || 7;
    start.setUTCDate(start.getUTCDate() - weekday + 1);
    return start;
  }

  if (bucketSize === 'month') {
    return new Date(Date.UTC(year, month, 1));
  }

  const quarterMonth = Math.floor(month / 3) * 3;
  return new Date(Date.UTC(year, quarterMonth, 1));
}

function advanceBucket(date: Date, bucketSize: BucketSize): Date {
  const next = new Date(date.getTime());

  if (bucketSize === 'day') {
    next.setUTCDate(next.getUTCDate() + 1);
    return next;
  }

  if (bucketSize === 'week') {
    next.setUTCDate(next.getUTCDate() + 7);
    return next;
  }

  if (bucketSize === 'month') {
    next.setUTCMonth(next.getUTCMonth() + 1);
    return next;
  }

  next.setUTCMonth(next.getUTCMonth() + 3);
  return next;
}

function bucketLabel(date: Date, bucketSize: BucketSize): ChartPoint {
  if (bucketSize === 'day') {
    const short = new Intl.DateTimeFormat('sv-SE', { month: 'short', day: 'numeric' }).format(date);
    return { label: short, shortLabel: short, value: null };
  }

  if (bucketSize === 'week') {
    const short = new Intl.DateTimeFormat('sv-SE', { month: 'short', day: 'numeric' }).format(date);
    return { label: `Vecka från ${short}`, shortLabel: short, value: null };
  }

  if (bucketSize === 'month') {
    const short = new Intl.DateTimeFormat('sv-SE', { month: 'short' }).format(date);
    return { label: formatMonthLabel(date), shortLabel: short, value: null };
  }

  return { label: formatQuarterLabel(date), shortLabel: formatQuarterLabel(date), value: null };
}

function effectiveNow(records: NormalizedRequest[], fallback = new Date()): Date {
  const latest = Math.max(...records.map((item) => item.receivedAtMs), 0);
  return latest ? new Date(latest) : fallback;
}

function normalizeRequests(requests: RequestRecord[]): NormalizedRequest[] {
  return requests
    .map((record) => ({
      receivedAtMs: parseDate(record.received_at),
      receivedAt: record.received_at,
      role: normalizeRole(record.primary_role),
      remoteMode: normalizeRemoteMode(record.remote_mode),
      location: normalizeText(record.location_city),
      sector: normalizeSector(record.sector),
      broker: normalizeBroker(record),
      durationMonths: record.duration_months,
      rateAmount: typeof record.rate_amount === 'number' ? record.rate_amount : null,
      rateCurrency: normalizeText(record.rate_currency),
      rateUnit: normalizeRateUnit(record.rate_unit),
      reviewStatus: normalizeText(record.review_status),
      overallConfidence: typeof record.overall_confidence === 'number' ? record.overall_confidence : null
    }))
    .filter((record) => record.receivedAtMs > 0)
    .sort((a, b) => b.receivedAtMs - a.receivedAtMs);
}

function filterNormalizedRequests(records: NormalizedRequest[], filters: DashboardFilters, now = effectiveNow(records)): NormalizedRequest[] {
  const startTime = now.getTime() - timeRangeMs[filters.timeRange];

  return records.filter((item) => item.receivedAtMs >= startTime && item.receivedAtMs <= now.getTime());
}

function previousPeriodRequests(records: NormalizedRequest[], filters: DashboardFilters, now = effectiveNow(records)): NormalizedRequest[] {
  const endTime = now.getTime() - timeRangeMs[filters.timeRange];
  const startTime = endTime - timeRangeMs[filters.timeRange];

  return records.filter((item) => item.receivedAtMs >= startTime && item.receivedAtMs < endTime);
}

function toCountMap(values: string[]): Map<string, number> {
  const counter = new Map<string, number>();

  for (const value of values) {
    counter.set(value, (counter.get(value) ?? 0) + 1);
  }

  return counter;
}

function topEntries(counter: Map<string, number>, limit: number): Array<[string, number]> {
  const sorted = Array.from(counter.entries()).sort((a, b) => b[1] - a[1]);
  if (sorted.length <= limit) {
    return sorted;
  }

  const visible = sorted.slice(0, limit - 1);
  const otherCount = sorted.slice(limit - 1).reduce((sum, entry) => sum + entry[1], 0);
  visible.push(['Övrigt', otherCount]);
  return visible;
}

function buildTrendPoints(
  records: NormalizedRequest[],
  filters: DashboardFilters,
  selector: (record: NormalizedRequest) => number | null,
  emptyAsZero: boolean
): ChartPoint[] {
  if (!records.length) {
    return [];
  }

  const bucketSize = bucketSizeForRange(filters.timeRange);
  const now = effectiveNow(records);
  const rangeStart = now.getTime() - timeRangeMs[filters.timeRange];
  const startBucket = bucketStart(rangeStart, bucketSize);
  const endBucket = bucketStart(now.getTime(), bucketSize);
  const buckets = new Map<number, number[]>();

  for (const record of records) {
    const value = selector(record);
    const key = bucketStart(record.receivedAtMs, bucketSize).getTime();
    const list = buckets.get(key) ?? [];
    if (value !== null) {
      list.push(value);
    }
    buckets.set(key, list);
  }

  const points: ChartPoint[] = [];
  for (let cursor = new Date(startBucket.getTime()); cursor.getTime() <= endBucket.getTime(); cursor = advanceBucket(cursor, bucketSize)) {
    const key = cursor.getTime();
    const label = bucketLabel(cursor, bucketSize);
    const values = buckets.get(key) ?? [];

    points.push({
      label: label.label,
      shortLabel: label.shortLabel,
      value: emptyAsZero ? values.length : Math.round(median(values) ?? average(values) ?? 0)
    });

    if (!emptyAsZero && !values.length) {
      points[points.length - 1].value = null;
    }
  }

  return points;
}

function hourlyRates(records: NormalizedRequest[]): NormalizedRequest[] {
  return records.filter(isHourlyRate);
}

function singleCurrencyLabel(records: NormalizedRequest[]): string {
  const currencies = Array.from(new Set(hourlyRates(records).map((record) => record.rateCurrency).filter((value) => value !== 'Okänt')));
  if (!currencies.length) {
    return 'Pris saknas';
  }

  if (currencies.length === 1) {
    return `${currencies[0]}/tim`;
  }

  return 'Blandade valutor';
}

function requestsDelta(current: number, previous: number): KpiCard['tone'] {
  if (current > previous) {
    return 'positive';
  }

  if (current < previous) {
    return 'negative';
  }

  return 'neutral';
}

function buildKpis(current: NormalizedRequest[], previous: NormalizedRequest[]): KpiCard[] {
  const currentRates = hourlyRates(current).map((record) => record.rateAmount as number);
  const previousRates = hourlyRates(previous).map((record) => record.rateAmount as number);
  const currencyLabel = singleCurrencyLabel(current);
  const remoteHybridCount = current.filter((record) => record.remoteMode === 'Distans' || record.remoteMode === 'Hybrid').length;
  const roleCounts = toCountMap(current.map((record) => record.role));
  const [topRole = 'Okänt', topRoleCount = 0] = Array.from(roleCounts.entries()).sort((a, b) => b[1] - a[1])[0] ?? [];
  const averageRate = average(currentRates);
  const medianRateValue = median(currentRates);
  const previousAverage = average(previousRates);

  const cards: KpiCard[] = [
    {
      label: 'Förfrågningar',
      value: `${current.length}`,
      detail: formatComparison(current.length, previous.length, 'period'),
      tone: requestsDelta(current.length, previous.length)
    }
  ];

  if (averageRate !== null) {
    cards.push({
      label: 'Genomsnittligt timpris',
      value: `${Math.round(averageRate)} ${currencyLabel}`,
      detail: previousAverage !== null ? `${formatSignedDelta(Math.round(averageRate - previousAverage))} jämfört med föregående period` : undefined,
      tone: previousAverage !== null && averageRate > previousAverage ? 'positive' : 'neutral'
    });
  }

  if (medianRateValue !== null) {
    cards.push({
      label: 'Median timpris',
      value: `${Math.round(medianRateValue)} ${currencyLabel}`,
      detail: `${currentRates.length} giltiga prisobservationer`
    });
  }

  cards.push({
    label: 'Andel distans + hybrid',
    value: formatPercent(percentage(remoteHybridCount, current.length)),
    detail: `${remoteHybridCount} av ${current.length} förfrågningar`
  });

  if (topRoleCount) {
    cards.push({
      label: 'Vanligaste roll',
      value: topRole,
      detail: `${formatPercent(percentage(topRoleCount, current.length))} av förfrågningarna`
    });
  }

  return cards;
}

function buildInsights(current: NormalizedRequest[], previous: NormalizedRequest[]): InsightCard[] {
  const insights: InsightCard[] = [];
  const currentRoles = toCountMap(current.map((record) => record.role));
  const previousRoles = toCountMap(previous.map((record) => record.role));
  const currentRatesByRole = new Map<string, number[]>();
  const brokers = toCountMap(current.map((record) => record.broker));

  for (const record of hourlyRates(current)) {
    const list = currentRatesByRole.get(record.role) ?? [];
    list.push(record.rateAmount as number);
    currentRatesByRole.set(record.role, list);
  }

  const growthCandidates = Array.from(currentRoles.entries())
    .map(([role, count]) => ({ role, delta: count - (previousRoles.get(role) ?? 0), count }))
    .filter((item) => item.count > 0 && (previousRoles.get(item.role) ?? 0) > 0)
    .sort((a, b) => b.delta - a.delta);

  const growingRole = growthCandidates[0];
  if (growingRole && growingRole.delta > 0) {
    insights.push({
      label: 'Snabbast växande roll',
      text: `${growingRole.role} har ökat med ${growingRole.delta} förfrågningar`,
      detail: 'Jämfört med föregående period med samma längd'
    });
  }

  const highestRateRole = Array.from(currentRatesByRole.entries())
    .filter(([, values]) => values.length >= 2)
    .map(([role, values]) => ({ role, averageRate: average(values) ?? 0, sample: values.length }))
    .sort((a, b) => b.averageRate - a.averageRate)[0];

  if (highestRateRole) {
    insights.push({
      label: 'Högsta snittpris',
      text: `${highestRateRole.role} ligger högst med ${Math.round(highestRateRole.averageRate)} ${singleCurrencyLabel(current)}`,
      detail: `Baserat på ${highestRateRole.sample} förfrågningar`
    });
  }

  const remoteFriendlyRole = Array.from(currentRoles.entries())
    .map(([role, count]) => {
      const remoteFriendly = current.filter((record) => record.role === role && (record.remoteMode === 'Distans' || record.remoteMode === 'Hybrid')).length;
      return {
        role,
        count,
        share: percentage(remoteFriendly, count)
      };
    })
    .filter((item) => item.count >= 2)
    .sort((a, b) => b.share - a.share)[0];

  if (remoteFriendlyRole) {
    insights.push({
      label: 'Mest distansvänliga roll',
      text: `${remoteFriendlyRole.role} har ${formatPercent(remoteFriendlyRole.share)} distans- eller hybridefterfrågan`,
      detail: `${remoteFriendlyRole.count} förfrågningar i intervallet`
    });
  }

  const topBroker = Array.from(brokers.entries()).sort((a, b) => b[1] - a[1])[0];
  if (topBroker) {
    insights.push({
      label: 'Mest aktiv partner',
      text: `${topBroker[0]} skickade ${topBroker[1]} förfrågningar`,
      detail: 'Grupperat på organisation eller avsändardomän'
    });
  }

  const topSector = Array.from(toCountMap(current.map((record) => record.sector)).entries()).sort((a, b) => b[1] - a[1])[0];
  if (topSector && topSector[0] !== 'Okänt') {
    insights.push({
      label: 'Största sektor',
      text: `${topSector[0]} står för ${formatPercent(percentage(topSector[1], current.length))}`,
      detail: `${topSector[1]} förfrågningar i valt intervall`
    });
  }

  return insights.slice(0, 5);
}

function buildRoleRanking(current: NormalizedRequest[]): RoleRankingRow[] {
  const counts = topEntries(toCountMap(current.map((record) => record.role)), 8);

  return counts.map(([label, value]) => ({
    label,
    value,
    share: percentage(value, current.length)
  }));
}

function buildRoleRemoteMix(current: NormalizedRequest[]): RoleRemotePoint[] {
  const roleTotals = topEntries(toCountMap(current.map((record) => record.role)), 8);
  const topRoles = new Set(roleTotals.map(([role]) => role));
  const rows = new Map<string, RoleRemotePoint>();

  for (const record of current) {
      const role = topRoles.has(record.role) ? record.role : 'Övrigt';
    const entry = rows.get(role) ?? { label: role, total: 0, remoteHybrid: 0 };
    entry.total += 1;
    if (record.remoteMode === 'Distans' || record.remoteMode === 'Hybrid') {
      entry.remoteHybrid += 1;
    }
    rows.set(role, entry);
  }

  return Array.from(rows.values()).sort((a, b) => b.total - a.total).slice(0, 8);
}

function buildRateByRole(current: NormalizedRequest[]): RateByRoleRow[] {
  const valuesByRole = new Map<string, number[]>();

  for (const record of hourlyRates(current)) {
    const bucket = valuesByRole.get(record.role) ?? [];
    bucket.push(record.rateAmount as number);
    valuesByRole.set(record.role, bucket);
  }

  const rows = Array.from(valuesByRole.entries())
    .filter(([, values]) => values.length >= 2)
    .map(([label, values]) => ({
      label,
      median: Math.round(median(values) ?? 0),
      min: Math.min(...values),
      max: Math.max(...values),
      count: values.length
    }))
    .sort((a, b) => b.median - a.median);

  return rows.slice(0, 8);
}

function buildLocationRows(current: NormalizedRequest[]): LocationRow[] {
  const rows = new Map<string, LocationRow>();

  for (const record of current) {
    const entry = rows.get(record.location) ?? {
      label: record.location,
      total: 0,
      remote: 0,
      hybrid: 0,
      onsite: 0
    };

    entry.total += 1;
    if (record.remoteMode === 'Distans') {
      entry.remote += 1;
    } else if (record.remoteMode === 'Hybrid') {
      entry.hybrid += 1;
    } else if (record.remoteMode === 'På plats') {
      entry.onsite += 1;
    }

    rows.set(record.location, entry);
  }

  return Array.from(rows.values()).sort((a, b) => b.total - a.total).slice(0, 8);
}

function buildBrokerRows(current: NormalizedRequest[]): BrokerRow[] {
  const groups = new Map<string, NormalizedRequest[]>();

  for (const record of current) {
    const bucket = groups.get(record.broker) ?? [];
    bucket.push(record);
    groups.set(record.broker, bucket);
  }

  return Array.from(groups.entries())
    .map(([label, records]) => {
      const roleCounts = toCountMap(records.map((record) => record.role));
      const topRole = Array.from(roleCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'Okänt';
      const rateValues = hourlyRates(records).map((record) => record.rateAmount as number);
      const remoteHybrid = records.filter((record) => record.remoteMode === 'Distans' || record.remoteMode === 'Hybrid').length;

      return {
        label,
        requests: records.length,
        topRole,
        averageRate: average(rateValues),
        remoteShare: percentage(remoteHybrid, records.length)
      };
    })
    .sort((a, b) => b.requests - a.requests)
    .slice(0, 8);
}

function buildDataQuality(current: NormalizedRequest[]): DataQualityVm {
  const confidenceValues = current.map((record) => record.overallConfidence).filter((value): value is number => value !== null);
  const averageConfidence = average(confidenceValues);
  const reviewNeeded = current.filter((record) => record.reviewStatus !== 'ok').length;
  const missingFields = [
    { label: 'Roll', count: current.filter((record) => record.role === 'Okänt').length },
    { label: 'Distansläge', count: current.filter((record) => record.remoteMode === 'Okänt').length },
    { label: 'Plats', count: current.filter((record) => record.location === 'Okänt').length },
    { label: 'Sektor', count: current.filter((record) => record.sector === 'Okänt').length },
    { label: 'Pris', count: current.filter((record) => !isHourlyRate(record)).length }
  ]
    .filter((row) => row.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, 4);

  return {
    averageConfidence,
    reviewNeeded,
    missingFields
  };
}

function formatRate(record: NormalizedRequest): string {
  if (!isHourlyRate(record)) {
    return 'Okänt';
  }

  return `${Math.round(record.rateAmount as number)} ${record.rateCurrency}/tim`;
}

function formatDuration(value: number | null): string {
  if (typeof value !== 'number') {
    return 'Okänt';
  }

  return `${value} mån`;
}

function formatReviewStatus(value: string): string {
  const cleaned = value.trim().toLowerCase();

  if (!cleaned || cleaned === 'ok') {
    return 'OK';
  }

  if (cleaned === 'partial') {
    return 'Delvis';
  }

  return titleCase(value);
}

function buildRequestRows(current: NormalizedRequest[]): RequestRow[] {
  return current
    .slice()
    .sort((a, b) => b.receivedAtMs - a.receivedAtMs)
    .slice(0, 12)
    .map((record) => ({
      receivedAt: formatDateLabel(record.receivedAt),
      role: record.role,
      location: record.location,
      remoteMode: record.remoteMode,
      rate: formatRate(record),
      duration: formatDuration(record.durationMonths),
      broker: record.broker,
      quality: record.reviewStatus === 'ok'
        ? `${record.overallConfidence !== null ? `${Math.round(record.overallConfidence * 100)}%` : 'OK'}`
        : `${formatReviewStatus(record.reviewStatus)}${record.overallConfidence !== null ? ` · ${Math.round(record.overallConfidence * 100)}%` : ''}`
    }));
}

export function buildDashboardVm(
  requests: RequestRecord[],
  filters: DashboardFilters,
  snapshotNote = 'Statistik och insikter om konsultförfrågningar från partners och konsultmäklare'
): DashboardVm {
  const normalized = normalizeRequests(requests);
  const now = effectiveNow(normalized);
  const current = filterNormalizedRequests(normalized, filters, now);
  const previous = previousPeriodRequests(normalized, filters, now);

  return {
    updatedAt: formatDateTimeLabel(now.getTime()),
    title: 'MarketPulse',
    subtitle: 'Statistik och insikter om konsultförfrågningar från partners och konsultmäklare',
    rangeLabel: timeRangeLabels[filters.timeRange],
    totalRequests: current.length,
    hasResults: current.length > 0,
    kpis: buildKpis(current, previous),
    insights: buildInsights(current, previous),
    demandTrend: buildTrendPoints(current, filters, () => 1, true),
    roleRanking: buildRoleRanking(current),
    roleRemoteMix: buildRoleRemoteMix(current),
    rateTrend: buildTrendPoints(current, filters, (record) => isHourlyRate(record) ? record.rateAmount : null, false),
    rateByRole: buildRateByRole(current),
    locations: buildLocationRows(current),
    brokers: buildBrokerRows(current),
    dataQuality: buildDataQuality(current),
    requestRows: buildRequestRows(current),
    rateUnitLabel: singleCurrencyLabel(current)
  };
}

export function filterRequests(requests: RequestRecord[], filters: DashboardFilters): RequestRecord[] {
  const normalized = normalizeRequests(requests);
  const ids = new Set(filterNormalizedRequests(normalized, filters).map((record) => `${record.receivedAt}-${record.role}-${record.broker}`));

  return requests.filter((record) => ids.has(`${record.received_at}-${normalizeRole(record.primary_role)}-${normalizeBroker(record)}`));
}
