# Market Pulse Frontend Specification

## 1. Purpose

Define a public dashboard frontend for visualizing request data from the local SQLite snapshot in a clean, minimal way.

The dashboard should:
- use real data exported from `db/marketpulse.sqlite3`
- present four focused statistical views
- avoid decorative controls or dummy UI
- keep charts visually clean and uncluttered
- work well on desktop and mobile

There is no login or authenticated area in version 1.

## 2. Data Source

The dashboard must use the SQLite database described in `AGENTS.md` as its source of truth.

Version 1 data flow:
- read from `db/marketpulse.sqlite3`
- export a read-only frontend snapshot from the `requests` table
- serve that snapshot to the Angular app as static JSON

Rules:
- treat the SQLite database as read-only
- do not introduce a backend API only for dashboard reads
- do not show fake or hardcoded analytics values
- tolerate partially normalized values in fields such as `primary_role` and `remote_mode`

The dashboard should primarily use these fields:
- `request_id`
- `received_at`
- `primary_role`
- `remote_mode`
- `rate_amount`
- `rate_currency`
- `rate_unit`

## 3. Page Structure

The overview page contains:
- page header
- one time-range slider
- four data panels in a responsive grid

Do not include:
- source selector
- reset filter button
- tab bars without real behavior
- assistant panels
- placeholder buttons
- placeholder cards

## 4. Time Range Control

Use a stepped slider with these options:
- `30 days`
- `3 months`
- `1 year`
- `5 years`
- `10 years`

Meaning:
- the selected step filters requests since that point in time
- all four views update from the same selected range

## 5. Views

The dashboard must contain exactly these four views.

### 5.1 Demand Analytics > Request Volume

Purpose:
Show request volume over time.

Requirements:
- render a simple graph over time
- keep the chart visually clean
- do not add labels inside the chart area that clutter the view
- use only a static time line on the x axis

### 5.2 Manage Insights > Roles and Remote Mix

Purpose:
Show total requests by role and the remote or hybrid share for each role.

Requirements:
- use a single combined staple diagram
- one vertical staple shows total request count per role
- one overlapping staple in another color shows the remote and hybrid subset for the same role
- do not split this into separate role and remote views

### 5.3 Priority Insights > Role Distribution

Purpose:
Show the role split as a compact proportional view.

Requirements:
- use a pie chart
- show only percentages
- do not show request counts in this view

### 5.4 Rate Over Time

Purpose:
Show hourly rate movement over time.

Requirements:
- render a simple curve or graph over time
- use hourly rate data from the database
- keep the chart visually clean
- use only a static time line on the x axis

## 6. UX Principles

- Remove clutter wherever possible.
- Show only real, data-backed content.
- Prefer simple charts over visually busy graphics.
- Do not add labels, controls, or explanatory text that compete with the charts.
- Keep all content inside panel boundaries.
- Truncate or constrain long labels so they do not overflow outside components.

## 7. Visual Direction

The design should feel:
- calm
- modern
- light
- soft
- restrained

Avoid:
- noisy decorations
- oversized shadows
- fake workspace chrome
- text-heavy panels
- action buttons without real behavior

## 8. Responsiveness

Desktop:
- two-column grid when space allows

Mobile:
- single-column layout
- charts and labels must remain contained inside their cards

## 9. States

The frontend must support:
- loading state
- error state
- empty-data handling when a filtered range has no matching points

## 10. Acceptance Criteria

The dashboard is correct when:
- all views are based on real SQLite-exported data
- no mock or dummy UI remains
- the time slider updates all four views
- request volume is shown as a simple time graph
- roles and remote mix are shown in one combined staple chart
- role distribution is shown as a pie chart with percentages only
- hourly rate is shown as a clean graph over time
- content does not overflow outside component borders
- the page remains readable on desktop and mobile
