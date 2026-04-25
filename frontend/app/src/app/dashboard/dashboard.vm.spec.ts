import { RequestRecord } from '../models/request-record.model';
import { buildDashboardVm } from './dashboard.vm';

describe('buildDashboardVm', () => {
  const requests: RequestRecord[] = [
    {
      request_id: '1',
      received_at: '2025-12-28T10:00:00Z',
      source_kind: 'email',
      sender_organization: 'Konsult Partners',
      sender_domain: 'konsult.example',
      primary_role: 'Backend Engineer',
      seniority: 'Senior',
      sector: 'fintech',
      location_city: 'Stockholm',
      remote_mode: 'hybrid',
      rate_amount: 950,
      rate_currency: 'SEK',
      rate_unit: 'hour',
      duration_months: 6,
      review_status: 'ok',
      overall_confidence: 0.94
    },
    {
      request_id: '2',
      received_at: '2025-12-20T10:00:00Z',
      source_kind: 'email',
      sender_organization: 'Konsult Partners',
      sender_domain: 'konsult.example',
      primary_role: 'Backend Engineer',
      seniority: 'Senior',
      sector: 'fintech',
      location_city: 'Stockholm',
      remote_mode: 'remote',
      rate_amount: 1000,
      rate_currency: 'SEK',
      rate_unit: 'hour',
      duration_months: 3,
      review_status: 'partial',
      overall_confidence: 0.91
    },
    {
      request_id: '3',
      received_at: '2025-07-01T10:00:00Z',
      source_kind: 'email',
      sender_organization: 'ByteForce',
      sender_domain: 'byteforce.example',
      primary_role: 'Software Engineer',
      seniority: 'Senior',
      sector: 'gaming',
      location_city: 'Malmö',
      remote_mode: 'on-site',
      rate_amount: 850,
      rate_currency: 'SEK',
      rate_unit: 'hour',
      duration_months: 12,
      review_status: 'ok',
      overall_confidence: 0.89
    }
  ];

  it('filters the selected range and builds KPI values', () => {
    const vm = buildDashboardVm(requests, { timeRange: '30D' }, 'Ögonblicksbild');

    expect(vm.totalRequests).toBe(2);
    expect(vm.hasResults).toBe(true);
    expect(vm.kpis[0].label).toBe('Förfrågningar');
    expect(vm.kpis[0].value).toBe('2');
    expect(vm.kpis.some((card) => card.label === 'Vanligaste roll' && card.value === 'Backend Engineer')).toBe(true);
  });

  it('builds rate, broker, and quality views from current data', () => {
    const vm = buildDashboardVm(requests, { timeRange: '1Y' }, 'Ögonblicksbild');

    expect(vm.rateByRole.length).toBe(1);
    expect(vm.rateByRole[0].label).toBe('Backend Engineer');
    expect(vm.brokers[0].label).toBe('Konsult Partners');
    expect(vm.dataQuality.reviewNeeded).toBe(1);
    expect(vm.locations[0].label).toBe('Stockholm');
  });
});
