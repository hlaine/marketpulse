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

## 8. Statistic Views

The dashboard overview must contain exactly four top-level statistic views.

Each view should follow a shared structure:
- title
- short supporting description
- primary value or key summary
- compact visualization
- trend indicator or comparison
- interaction affordance

### 8.1 View 1: Volume Trend

Purpose:
Show total activity volume over time.

Content:
- primary metric for current total volume in the selected time range
- line chart showing volume trend across time
- comparison against previous equivalent period

Interactions:
- hover or tap a point to show exact values
- selecting a date region updates the detail area

### 8.2 View 2: Sentiment Distribution

Purpose:
Show the distribution of positive, neutral, and negative sentiment.

Content:
- high-level sentiment summary
- segmented bar, donut chart, or stacked chart
- percentage split for each sentiment group

Interactions:
- hover or tap a segment to show exact percentages and counts
- clicking a segment filters the detail area to that sentiment

### 8.3 View 3: Top Categories

Purpose:
Show which categories, themes, or topics currently dominate.

Content:
- ranked list or horizontal bar chart of top categories
- share of total volume per category
- change indicator versus previous period

Interactions:
- clicking a category highlights it across the detail area
- hovering or tapping reveals exact values

### 8.4 View 4: Notable Change or Alert View

Purpose:
Surface the most significant recent movement or anomaly.

Content:
- strongest upward or downward change
- small trend chart or comparison indicator
- short explanation label such as `Largest increase` or `Sharpest drop`

Interactions:
- clicking the view opens a detail panel with the time window, affected category, and comparative numbers

## 9. Interaction Model

### 9.1 Shared View Interactions

All four views should support:
- hover states on desktop
- tap states on mobile
- clear selected state
- keyboard focus state
- accessible tooltip or details behavior

### 9.2 Selection Behavior

Only one view should be active at a time.

When a new view is selected:
- the active highlight moves to the selected view
- the detail area updates
- the previous selection is cleared

### 9.3 Detail Behavior

The detail area should display:
- selected view title
- current filter context
- a more detailed chart, breakdown, or explanation
- a short textual summary of what the selected data means

The detail area should never feel like a separate page. It should feel like an extension of the overview.

## 10. Look and Feel

### 10.1 Visual Direction

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

### 10.2 Color

Use a restrained color system:
- neutral page background
- white or very light card surfaces
- one primary accent color
- semantic colors for positive, neutral, and negative states

Color usage should reinforce meaning, not add decoration.

### 10.3 Typography

Typography should prioritize clarity and hierarchy.

Use:
- strong page title
- concise section and card titles
- highly legible number styling for KPI values
- muted secondary text for descriptions and timestamps

### 10.4 Spacing and Density

The dashboard should feel spacious but efficient.

Requirements:
- consistent spacing scale
- clear grouping within cards
- enough breathing room around charts and labels
- avoid cramped mobile layouts

## 11. Component Requirements

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

## 12. States

### 12.1 Loading State

Before data loads:
- show the page header and filter bar shell
- show loading placeholders for all four statistic views
- avoid layout shifting where possible

### 12.2 Empty State

If filters return no data:
- show a clear message
- explain that no data matched the current filters
- offer a reset filters action

### 12.3 Error State

If data fails to load:
- show a clear non-technical message
- show a retry action
- keep the overall layout stable

## 13. Responsiveness

### 13.1 Desktop

Target experience:
- two-by-two overview grid
- persistent visual hierarchy
- detail area below the main grid

### 13.2 Tablet

Target experience:
- two columns when readable
- filter bar may wrap to multiple lines

### 13.3 Mobile

Target experience:
- stacked cards
- filters remain usable without crowding
- detail state appears inline under the selected card or below the list
- charts remain readable at smaller widths

## 14. Accessibility

The dashboard must:
- support keyboard navigation
- use semantic headings
- provide visible focus styles
- avoid relying on color alone for meaning
- provide readable labels for charts, controls, and summaries
- ensure sufficient contrast

If a chart cannot fully communicate via visuals alone, provide a supporting textual summary.

## 15. Content and Data Requirements

The frontend should assume that each statistic view can receive:
- current value
- previous comparison value
- time-series data or grouped data
- optional labels and categories
- timestamp metadata

The UI should tolerate:
- partial data
- delayed data
- zero-value data

## 16. Performance Expectations

- The first screen should feel fast and lightweight.
- Avoid unnecessary animation and heavy rendering work.
- Load only what is needed for the dashboard overview.
- Keep interactions responsive when filters change.

## 17. Suggested Technical Direction

Framework:
- Angular

Architecture direction:
- single dashboard page container
- small presentational components for each view
- explicit mapping from API data into view models
- minimal state complexity

Do not introduce:
- authentication scaffolding
- unnecessary global state infrastructure
- generic dashboard builders or plugin systems

## 18. Acceptance Criteria

The dashboard is complete for version 1 when:
- a public user can open the overview page without logging in
- the page displays four statistic views
- each view communicates one distinct market statistic clearly
- the user can interact with the views and see additional detail
- global filters update the views consistently
- desktop and mobile layouts are usable
- loading, empty, and error states are implemented
- the visual design feels clean, lean, and coherent

## 19. Open Decisions

These items should be confirmed during implementation if backend constraints require it:
- exact source and shape of the data
- exact chart library
- exact category names and business terminology
- exact anomaly logic for the notable change view

## 20. Example User Experience Summary

When the user opens the dashboard, they immediately see four statistics views that explain the current market picture. They can change the time range, inspect a chart point, click a category or sentiment segment, and open more detail for one selected view without leaving the page. The interface stays clean and focused throughout.
