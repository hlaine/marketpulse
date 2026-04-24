# Market Pulse Frontend Specification

## 1. Purpose

Define the frontend requirements for a public dashboard that visualizes market-related statistics in a simple, clean, and interactive way.

The dashboard should:
- present four core statistic views on a single overview page
- allow users to interact with the views to inspect trends and details
- feel lightweight, modern, and trustworthy
- avoid unnecessary complexity or decorative UI that distracts from the data

There is no login or authenticated area in the first version. The frontend is public and should work well for first-time visitors.

## 2. Product Goal

Help a user quickly understand the current state of the tracked market signals, how they are changing over time, and where notable changes or anomalies appear.

The product should support fast scanning first, then deeper exploration through lightweight interaction.

## 3. Target User

The primary user is a person who wants a fast overview of key market statistics without needing training or onboarding.

Typical user needs:
- understand the overall situation in a few seconds
- compare current values with recent history
- spot major movements or anomalies
- inspect one view in more detail without leaving the page

## 4. Scope

Included in this version:
- one public dashboard overview page
- four statistics views on the overview
- interactive filtering and view interaction
- responsive layout for desktop and mobile
- empty, loading, and error states
- data loaded from the local SQLite snapshot under `db/marketpulse.sqlite3`

Not included in this version:
- login or user accounts
- saved preferences
- admin tooling
- editing or data entry
- multi-page drill-down flows

## 5. Core UX Principles

- Keep the interface calm, clear, and data-first.
- Make the overview understandable within a few seconds.
- Prefer one obvious action path over many secondary controls.
- Keep interactions lightweight and reversible.
- Show detail on demand instead of showing everything at once.
- Preserve consistency across all statistic views.

## 6. Information Architecture

Version 1 contains a single route:

- `/` Dashboard Overview

The overview page contains:
- page header
- global filter bar
- four statistic views in a responsive grid
- contextual detail area or expandable detail state for the selected view

## 7. Page Structure

### 7.1 Header

The page header should include:
- product name: `Market Pulse`
- short subtitle describing the dashboard purpose
- last updated timestamp

Example subtitle:
`Public dashboard for tracking key market signals and recent changes.`

### 7.2 Global Filter Bar

The filter bar should be placed directly under the header and remain easy to access.

Initial controls:
- time range selector
- category or segment selector
- reset filters action

Suggested default time range options:
- `24H`
- `7D`
- `30D`
- `90D`

Behavior:
- changes update all four statistic views
- active filters should be visibly clear
- reset returns the dashboard to its default state

### 7.3 Main Content Grid

The overview page should show four statistic views in a two-by-two grid on desktop.

Desktop layout:
- row 1: view 1 and view 2
- row 2: view 3 and view 4

Tablet layout:
- two columns if space allows

Mobile layout:
- one column stacked vertically

### 7.4 Detail Area

When a user interacts with a statistic view, the page should reveal more detail without forcing navigation away from the overview.

Preferred behavior:
- clicking or tapping a view marks it as active
- an inline detail panel appears below the grid or directly below the active card on mobile
- the detail panel shows a richer breakdown related to the selected view

Alternative acceptable behavior:
- the selected card expands in place

## 8. Data Source

The dashboard must use the SQLite database described in `AGENTS.md` as its source of truth.

Version 1 data flow:
- read from `db/marketpulse.sqlite3`
- export a read-only frontend snapshot from the `requests` table
- serve that snapshot to the Angular app as static JSON

Rules:
- treat the SQLite database as read-only from the frontend workflow
- do not require a live backend API for version 1
- clearly communicate that the dashboard visualizes a local snapshot
- tolerate partially normalized values in fields such as `remote_mode`, `sector`, or `primary_role`

The frontend should primarily rely on these database columns:
- `request_id`
- `received_at`
- `source_kind`
- `sender_organization`
- `primary_role`
- `seniority`
- `sector`
- `location_city`
- `remote_mode`
- `rate_amount`
- `rate_currency`
- `rate_unit`
- `duration_months`
- `review_status`
- `overall_confidence`

## 9. Statistic Views

The dashboard overview must contain exactly four top-level statistic views.

Each view should follow a shared structure:
- title
- short supporting description
- primary value or key summary
- compact visualization
- trend indicator or comparison
- interaction affordance

### 9.1 View 1: Volume Trend

Purpose:
Show total activity volume over time.

Content:
- primary metric for current total volume in the selected time range
- line chart showing volume trend across time
- comparison against previous equivalent period

Interactions:
- hover or tap a point to show exact values
- selecting a date region updates the detail area

### 9.2 View 2: Role Distribution

Purpose:
Show which primary consultant roles dominate the incoming request flow.

Content:
- top requested roles from `primary_role`
- ranked list or horizontal bars
- percentage share of filtered requests

Interactions:
- hover or tap a role to show exact counts
- clicking a role updates the detail area

### 9.3 View 3: Remote Mode Mix

Purpose:
Show how assignments are distributed across `onsite`, `hybrid`, `remote`, and unknown values.

Content:
- normalized remote-mode distribution
- segmented chart or comparable compact breakdown
- share of filtered requests per mode

Interactions:
- clicking a mode highlights it in the detail area
- hovering or tapping reveals exact values

### 9.4 View 4: Extraction Quality

Purpose:
Show whether the extracted requests are reliable enough for decision support.

Content:
- average `overall_confidence`
- counts by `review_status`
- compact summary of records that need review

Interactions:
- clicking the view opens a detail panel with review-status breakdown and confidence context

## 10. Interaction Model

### 10.1 Shared View Interactions

All four views should support:
- hover states on desktop
- tap states on mobile
- clear selected state
- keyboard focus state
- accessible tooltip or details behavior

### 10.2 Selection Behavior

Only one view should be active at a time.

When a new view is selected:
- the active highlight moves to the selected view
- the detail area updates
- the previous selection is cleared

### 10.3 Detail Behavior

The detail area should display:
- selected view title
- current filter context
- a more detailed chart, breakdown, or explanation
- a short textual summary of what the selected data means

The detail area should never feel like a separate page. It should feel like an extension of the overview.

## 11. Look and Feel

### 11.1 Visual Direction

The design should feel:
- clean
- modern
- calm
- credible
- operational rather than promotional

Avoid:
- excessive gradients
- decorative glassmorphism
- overly dark styling by default
- heavy shadows
- noisy card chrome

### 11.2 Color

Use a restrained color system:
- neutral page background
- white or very light card surfaces
- one primary accent color
- semantic colors for positive, neutral, and negative states

Color usage should reinforce meaning, not add decoration.

### 11.3 Typography

Typography should prioritize clarity and hierarchy.

Use:
- strong page title
- concise section and card titles
- highly legible number styling for KPI values
- muted secondary text for descriptions and timestamps

### 11.4 Spacing and Density

The dashboard should feel spacious but efficient.

Requirements:
- consistent spacing scale
- clear grouping within cards
- enough breathing room around charts and labels
- avoid cramped mobile layouts

## 12. Component Requirements

The frontend should include, at minimum, these reusable UI components:
- page header
- filter bar
- statistic card shell
- chart wrapper
- tooltip or data-hover presentation
- detail panel
- empty state
- error state
- loading skeleton or loading placeholder

## 13. States

### 13.1 Loading State

Before data loads:
- show the page header and filter bar shell
- show loading placeholders for all four statistic views
- avoid layout shifting where possible

### 13.2 Empty State

If filters return no data:
- show a clear message
- explain that no data matched the current filters
- offer a reset filters action

### 13.3 Error State

If data fails to load:
- show a clear non-technical message
- show a retry action
- keep the overall layout stable

## 14. Responsiveness

### 14.1 Desktop

Target experience:
- two-by-two overview grid
- persistent visual hierarchy
- detail area below the main grid

### 14.2 Tablet

Target experience:
- two columns when readable
- filter bar may wrap to multiple lines

### 14.3 Mobile

Target experience:
- stacked cards
- filters remain usable without crowding
- detail state appears inline under the selected card or below the list
- charts remain readable at smaller widths

## 15. Accessibility

The dashboard must:
- support keyboard navigation
- use semantic headings
- provide visible focus styles
- avoid relying on color alone for meaning
- provide readable labels for charts, controls, and summaries
- ensure sufficient contrast

If a chart cannot fully communicate via visuals alone, provide a supporting textual summary.

## 16. Content and Data Requirements

The frontend should assume that each statistic view can receive:
- current aggregated values from the SQLite snapshot
- grouped counts by date, role, remote mode, or review status
- optional missing or blank values
- snapshot metadata such as export timestamp and row count

The UI should tolerate:
- partial data
- delayed data
- zero-value data

## 17. Performance Expectations

- The first screen should feel fast and lightweight.
- Avoid unnecessary animation and heavy rendering work.
- Load only what is needed for the dashboard overview.
- Keep interactions responsive when filters change.

## 18. Suggested Technical Direction

Framework:
- Angular

Architecture direction:
- single dashboard page container
- small presentational components for each view
- explicit mapping from exported SQLite snapshot data into view models
- minimal state complexity

Do not introduce:
- authentication scaffolding
- unnecessary global state infrastructure
- generic dashboard builders or plugin systems
- direct browser access to SQLite without a compelling reason
- a backend API solely to support version 1 dashboard reads

## 19. Acceptance Criteria

The dashboard is complete for version 1 when:
- a public user can open the overview page without logging in
- the dashboard data originates from `db/marketpulse.sqlite3`
- the page displays four statistic views
- each view communicates one distinct market statistic clearly
- the user can interact with the views and see additional detail
- global filters update the views consistently
- desktop and mobile layouts are usable
- loading, empty, and error states are implemented
- the visual design feels clean, lean, and coherent

## 20. Open Decisions

These items should be confirmed during implementation if backend constraints require it:
- whether the snapshot export should run automatically on every frontend start/build
- whether additional SQLite views should be exported for richer drill-down
- exact chart library if the current lightweight implementation becomes too limited

## 21. Example User Experience Summary

When the user opens the dashboard, they immediately see four statistics views that explain the current market picture from the local SQLite snapshot. They can change the time range, inspect request volume, compare dominant roles, review remote-mode distribution, and understand extraction quality without leaving the page. The interface stays clean and focused throughout.
