# Market Pulse Frontend Specification

## 1. Purpose

Define a public dashboard frontend for visualizing consultant request data from the local SQLite snapshot in a clear, decision-oriented way.

The dashboard should:
- use real data exported from `db/marketpulse.sqlite3`
- present a richer market intelligence dashboard, not only four basic charts
- make demand, rates, brokers, geography, urgency, and data quality easy to understand at a glance
- show immediately useful insights that can be derived from the existing request data
- avoid decorative controls, fake values, placeholder UI, or hardcoded analytics
- work well on desktop and mobile

This is a hackathon version. The scope is presentation and frontend analytics only. Do not introduce authentication, editing flows, backend APIs, or advanced recommendation/alerting features.

There is no login or authenticated area.

## 2. Data Source

The dashboard must use the SQLite database described in `AGENTS.md` as its source of truth.

Data flow:
- read from `db/marketpulse.sqlite3`
- export a read-only frontend snapshot from the `requests` table
- serve that snapshot to the Angular app as static JSON

Rules:
- treat the SQLite database as read-only
- do not introduce a backend API only for dashboard reads
- do not show fake, mocked, or hardcoded analytics values
- tolerate missing, null, partially normalized, and inconsistent values
- every number, chart, and card must be computed from the exported snapshot
- if a field is unavailable in the current database, hide the affected view or show a graceful empty state instead of inventing data

Use any available fields that correspond to the extracted request schema. The dashboard should prefer these fields when present:
- `request_id`
- `received_at`
- `primary_role`
- `secondary_roles`
- `technologies`
- `seniority`
- `remote_mode`
- `location_city` / `city` / `location`
- `country`
- `sector`
- `start_date`
- `duration_months`
- `allocation_percent`
- `positions_count`
- `rate_amount`
- `rate_currency`
- `rate_unit`
- `sender_name`
- `sender_organization`
- `sender_domain`
- `overall_confidence`
- `review_status`
- `warnings`

If nested JSON fields are exported, flatten them during snapshot generation or in the frontend adapter before charting.

## 3. Dashboard Variant

Build this as a new separate dashboard view, not as a replacement for the existing simple dashboard unless the app currently has only one route.

Suggested route/name:
- route: `/market-intelligence`
- page title: `Market Intelligence`
- subtitle: `Consultant request demand, rates, brokers, and data quality`

If routing is not currently configured, implement the new dashboard as a separate component that can be swapped into the app shell easily.

## 4. Page Structure

The page should contain:
1. Page header
2. Global time-range control
3. KPI summary strip
4. Auto-generated insight cards
5. Main analytics grid with multiple focused panels
6. Optional request drill-down table at the bottom

Do not include:
- source selector
- reset filter button unless real filters are added and it works
- tab bars without real behavior
- assistant panels
- placeholder buttons
- placeholder cards
- fake workspace chrome

## 5. Global Controls

### 5.1 Time Range Control

Use a stepped control with these options:
- `30 days`
- `3 months`
- `1 year`
- `5 years`
- `10 years`

Meaning:
- the selected step filters requests since that point in time
- all views update from the same selected range
- default to `1 year`

### 5.2 Optional Lightweight Filters

Add real filters only if they are easy to implement from the exported snapshot.

Allowed filters:
- role
- technology
- remote mode
- location/city
- broker organization/domain

Rules:
- filters must update all panels
- filters must only contain values that exist in the selected snapshot
- avoid complex filter drawers; use compact chips or selects
- include an active filter summary only when filters are active

## 6. KPI Summary Strip

Add a compact row of high-level cards directly below the time control.

Cards:
1. `Requests`
   - total number of requests in the selected range
   - delta versus the previous equal-length period when possible
2. `Avg hourly rate`
   - average `rate_amount` for requests where `rate_unit` is hour/hourly and amount exists
   - include currency when consistent; if mixed currencies exist, show `Mixed`
3. `Median hourly rate`
   - median hourly rate for valid hourly rates
4. `Remote + hybrid share`
   - percentage of requests where `remote_mode` is remote or hybrid
5. `Median lead time`
   - median days between `received_at` and `start_date`
   - hide if start dates are mostly missing
6. `Top role`
   - most common normalized role and its share

KPI cards should be small, readable, and data-dense. Use one primary number, one short label, and an optional small comparison line.

## 7. Auto-Generated Insight Cards

Add a row of 3-5 compact insight cards. These should be deterministic, data-backed summaries, not AI-generated text.

Possible insight cards:
- `Fastest growing role`: role with largest positive request-count change versus previous equal-length period
- `Highest average rate`: role with the highest average hourly rate, requiring at least 2 valid rate observations if possible
- `Most remote-friendly role`: role with the highest remote + hybrid share, requiring at least 2 requests if possible
- `Most active broker`: sender organization/domain with the most requests
- `Most urgent demand`: role with the shortest median lead time

Rules:
- hide an insight if there is not enough data
- never fabricate trend language when previous-period data is unavailable
- keep each card to 1-2 short lines
- examples of good copy:
  - `Backend Engineer leads demand: 28% of requests`
  - `.NET has the highest avg rate: 950 SEK/h`
  - `Konsult Partners sent 7 requests`

## 8. Analytics Views

The dashboard should contain the following views. Use responsive cards in a grid. Prioritize clarity over decorative chart density.

### 8.1 Demand Trend

Purpose:
Show request volume over time and make spikes easy to see.

Data:
- count requests by received date bucket
- bucket size should adapt to selected range:
  - 30 days: daily
  - 3 months: weekly
  - 1 year: monthly or weekly, whichever looks cleaner
  - 5/10 years: monthly or quarterly

Visual:
- line chart or area chart
- add a subtle moving average line when there are enough points
- x-axis should show a small number of readable date ticks
- y-axis should start at 0
- no labels inside the chart area except optional hover tooltip

Panel extras:
- show total requests and previous-period delta in the panel header
- optionally annotate the highest spike in a restrained way

### 8.2 Role Demand Ranking

Purpose:
Show which roles dominate demand.

Data:
- group by normalized primary role
- sort descending by request count
- show top 8 roles, group the rest as `Other` if needed

Visual:
- horizontal bar chart, not a donut
- each row shows role name, count, and percentage share
- truncate long role names but keep tooltip/full title on hover if practical

Why:
Horizontal bars are easier to compare than pie slices and should replace the old role distribution donut in the new dashboard.

### 8.3 Roles and Remote Mix

Purpose:
Show total requests by role and how much of each role is remote or hybrid.

Data:
- group by normalized primary role
- count total requests
- count remote + hybrid requests, where `remote_mode` is `remote`, `hybrid`, `remote_or_hybrid`, or equivalent normalized values
- show top 6-8 roles by total count

Visual:
- combined vertical bar chart
- background/full bar = total requests
- overlapping foreground bar = remote + hybrid subset
- include a compact legend: `Total`, `Remote + hybrid`
- show role labels below bars, truncated safely
- show values in tooltip; avoid cluttered labels above every bar on small screens

### 8.4 Technology Demand

Purpose:
Show the technologies and skill keywords that appear most often.

Data:
- extract normalized technologies from available technology fields
- count each technology across requests
- if importance is available, distinguish required vs preferred
- show top 10 technologies

Visual:
- horizontal bar chart or compact tag cloud with numeric counts
- prefer horizontal bars if counts vary significantly
- include required/preferred split only if the data exists and can be shown cleanly

Fallback:
- if technology data is unavailable, hide this panel or show `No technology data available in this snapshot`.

### 8.5 Rate Intelligence

Purpose:
Show how hourly rates are moving and which roles command higher rates.

This section should contain two related charts in one large card or two sibling cards.

#### 8.5.1 Hourly Rate Trend

Data:
- include only requests with valid `rate_amount` and hourly `rate_unit`
- bucket by time using the same adaptive logic as demand trend
- calculate average and median rate per bucket when enough data exists

Visual:
- clean line chart
- default line should be median when there are enough points; otherwise average
- y-axis should use rate values and currency/unit labels such as `SEK/h`
- show gaps instead of connecting across long periods with no data if practical

#### 8.5.2 Rate by Role

Data:
- group valid hourly rates by role
- calculate median, min, max, and count
- show only roles with at least 2 valid rate observations when possible

Visual:
- horizontal bar chart of median hourly rate by role
- include min-max whisker or small range marker if easy; otherwise show median only
- tooltip should show median, min, max, and sample count

### 8.6 Location and Remote View

Purpose:
Show where demand is located and how location relates to remote mode.

Data:
- group by city/location when available
- group unknown/missing as `Unknown`
- count remote modes per location

Visual options:
- for hackathon simplicity, use a ranked horizontal bar chart by city
- optionally use stacked segments for onsite, hybrid, remote if available
- do not implement a map unless it is already easy in the codebase

Panel extras:
- show top city and its request share

### 8.7 Urgency and Assignment Shape

Purpose:
Show when clients need consultants and what kind of assignments they ask for.

Data:
- lead time = days between `received_at` and `start_date`
- duration = `duration_months`
- allocation = `allocation_percent`
- positions = `positions_count`

Views in this card:
- `Lead time`: histogram or grouped bars with buckets such as `0-7d`, `8-14d`, `15-30d`, `31-60d`, `60d+`
- `Duration`: compact distribution by months, e.g. `0-3`, `4-6`, `7-12`, `12+`
- `Positions`: small metric showing total requested positions and average positions per request when available

Rules:
- hide unavailable subviews independently
- do not show empty mini charts just to fill space

### 8.8 Broker Intelligence

Purpose:
Show which brokers send the most requests and what they specialize in.

Data:
- group by `sender_organization` when available; otherwise use `sender_domain`
- count requests by broker
- calculate average hourly rate by broker when valid rate data exists
- identify top role per broker

Visual:
- table-like ranked list or horizontal bars
- columns/fields:
  - broker
  - requests
  - top role
  - avg hourly rate
  - remote + hybrid share

Rules:
- show top 8 brokers
- truncate long organization names safely
- do not show personal sender names as the main grouping unless organization/domain is missing

### 8.9 Data Quality

Purpose:
Make extraction reliability visible without overwhelming the main dashboard.

Data:
- `overall_confidence`
- `review_status`
- warnings
- missing key fields such as role, rate, remote mode, location, start date

Visual:
- compact quality card
- show average confidence
- show count of requests needing review or with warnings
- show top missing fields as small rows or chips

Rules:
- this should be a smaller supporting card
- use it to build trust, not as the visual focus

### 8.10 Request Drill-Down Table

Purpose:
Allow users to inspect the underlying requests behind the dashboard.

Placement:
- bottom of the page

Columns:
- received date
- role
- technologies
- location
- remote mode
- rate
- start date
- duration
- broker
- confidence/review status

Rules:
- use real rows only
- sort newest first by default
- apply the same global time range and filters as the charts
- keep the table compact and horizontally scrollable on mobile
- truncate long text with accessible full value on hover/title if practical

## 9. Layout Guidance

Desktop layout:
- header and controls full width
- KPI strip full width
- insight cards full width
- main grid with 12-column behavior if available
- suggested card sizes:
  - Demand Trend: wide, 2 columns
  - Role Demand Ranking: medium
  - Roles and Remote Mix: medium
  - Rate Intelligence: wide
  - Technology Demand: medium
  - Location and Remote: medium
  - Urgency and Assignment Shape: medium
  - Broker Intelligence: wide or medium-wide
  - Data Quality: small/medium
  - Request Drill-Down Table: full width

Mobile layout:
- single-column layout
- KPI cards wrap into two columns where possible, otherwise one column
- charts must stay inside cards
- avoid tiny unreadable axis labels
- table may scroll horizontally inside its container

## 10. UX Principles

- Show only real, data-backed content.
- Prefer clear rankings, medians, percentages, and deltas over decorative visuals.
- Use concise panel headers that answer a business question.
- Put the most important number in the card header when possible.
- Avoid long explanatory text inside cards.
- Keep charts visually clean with limited gridlines and readable labels.
- Keep all content inside panel boundaries.
- Truncate or constrain long labels so they do not overflow outside components.
- Use tooltips for details, not permanent clutter.
- Empty states should explain what is missing in one short sentence.

## 11. Visual Direction

The design should feel:
- calm
- modern
- light
- soft
- restrained
- analytical

Recommended visual treatment:
- soft card backgrounds
- subtle borders
- small uppercase section labels only when helpful
- consistent spacing between cards
- strong typographic hierarchy for numbers and headings
- semantic color use where possible:
  - positive growth / high value: green
  - negative growth / decline: red or muted warning color
  - neutral totals: blue/purple
  - remote/hybrid subset: teal or another consistent accent

Avoid:
- noisy decorations
- oversized shadows
- fake workspace chrome
- text-heavy panels
- action buttons without real behavior
- excessive colors in a single chart

## 12. Data Handling Rules

### 12.1 Normalization

Normalize display values before grouping:
- trim whitespace
- collapse empty strings, nulls, and unknown variants to `Unknown`
- normalize remote mode variants into `Remote`, `Hybrid`, `Onsite`, `Unknown`
- normalize role names only with safe string cleanup unless an existing normalized field is available
- normalize currency/unit labels for display

### 12.2 Previous-Period Comparison

For deltas:
- compare the selected range to the immediately preceding equal-length range
- example: selected 30 days compares with the 30 days before that
- if the previous period has zero values, show `New activity` or hide percentage delta instead of dividing by zero

### 12.3 Rate Calculations

Rate analytics must:
- include only numeric `rate_amount`
- include only hourly rates when `rate_unit` is hour/hourly or equivalent
- keep currencies separate if mixed currencies are present
- show currency in labels when known
- avoid averaging across different currencies unless clearly marked as mixed and no better option exists

### 12.4 Minimum Sample Sizes

Use minimum sample sizes to avoid misleading insights:
- role rate comparisons: prefer at least 2 rate observations per role
- broker rate comparisons: prefer at least 2 rate observations per broker
- trend cards: require at least one current-period and one previous-period observation
- if sample size is low, show `n=1` in tooltip or hide the comparison

## 13. States

The frontend must support:
- loading state
- error state
- empty-data handling when a filtered range has no matching requests
- empty-panel handling when a specific field is unavailable
- low-sample handling for rate and trend views

Empty examples:
- `No requests in this time range.`
- `No hourly rate data available.`
- `No technology data available in this snapshot.`

## 14. Acceptance Criteria

The dashboard is correct when:
- it is implemented as a new separate market intelligence dashboard or clearly separable component
- all views are based on real SQLite-exported data
- no mock values, dummy UI, or placeholder cards remain
- the time range updates all KPI cards, insight cards, charts, and the drill-down table
- KPI cards show requests, rates, remote share, lead time, and top role where data exists
- auto-generated insight cards are deterministic and data-backed
- demand trend shows request volume over time with sensible date buckets
- role demand is shown as a readable ranked horizontal bar chart
- roles and remote mix are shown in one combined total/subset chart
- technology demand is shown when technology data exists
- rate intelligence includes hourly rate trend and rate by role when rate data exists
- location/remote, urgency/duration, broker, and data-quality views are present when data exists
- empty or missing data is handled gracefully without fake replacements
- content does not overflow outside component borders
- the page remains readable on desktop and mobile
