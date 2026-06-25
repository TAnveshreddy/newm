# Power BI Report and Dashboard Testing Guidelines

## Table of Contents

1. [Overview](#overview)
2. [Testing Objectives](#testing-objectives)
3. [Types of Testing](#types-of-testing)
4. [Pre-Testing Checklist](#pre-testing-checklist)
5. [Data Validation Testing](#data-validation-testing)
6. [Visual and UI Testing](#visual-and-ui-testing)
7. [Functional Testing](#functional-testing)
8. [Performance Testing](#performance-testing)
9. [Security and Access Testing](#security-and-access-testing)
10. [Cross-Platform and Compatibility Testing](#cross-platform-and-compatibility-testing)
11. [Regression Testing](#regression-testing)
12. [User Acceptance Testing (UAT)](#user-acceptance-testing-uat)
13. [Defect Management](#defect-management)
14. [Test Reporting](#test-reporting)
15. [Best Practices](#best-practices)
16. [Appendix: Test Case Templates](#appendix-test-case-templates)

---

## 1. Overview

This document provides comprehensive guidelines for testing Power BI reports and dashboards across the full development lifecycle — from initial data validation to production sign-off. These guidelines apply to:

- Power BI Desktop reports (.pbix)
- Power BI Service dashboards and workspaces
- Paginated reports (SSRS-style)
- Embedded Power BI reports
- Power BI apps distributed to end users

Testing Power BI assets ensures data accuracy, consistent visual rendering, correct business logic, acceptable performance, and appropriate security controls.

---

## 2. Testing Objectives

| Objective | Description |
|---|---|
| **Data Accuracy** | Verify that numbers, aggregations, and calculations match source systems |
| **Business Logic Validation** | Ensure DAX measures and KPIs reflect correct business rules |
| **Visual Correctness** | Confirm charts, tables, and maps render as designed |
| **Functional Integrity** | Validate filters, slicers, drill-throughs, and bookmarks work correctly |
| **Performance** | Ensure reports load within acceptable time thresholds |
| **Security** | Confirm Row-Level Security (RLS) and workspace permissions are enforced |
| **Usability** | Validate that the report is navigable and intuitive for end users |
| **Compatibility** | Ensure consistent behavior across browsers, devices, and screen sizes |

---

## 3. Types of Testing

### 3.1 Unit Testing
Testing individual DAX measures, calculated columns, and data model relationships in isolation before the full report is assembled.

### 3.2 Integration Testing
Validating that the data model correctly integrates data from multiple sources (SQL Server, SharePoint, Excel, APIs, etc.) and that relationships produce expected join results.

### 3.3 System Testing
End-to-end validation of the complete report — visuals, filters, navigation, security, and data accuracy — as a whole system.

### 3.4 Regression Testing
Re-running a defined set of test cases after any change (new data source, DAX update, visual change) to ensure existing functionality is not broken.

### 3.5 User Acceptance Testing (UAT)
Structured testing by business stakeholders to validate the report meets requirements before go-live.

### 3.6 Performance Testing
Measuring report load time, query execution time, and visual rendering speed under expected and peak load conditions.

### 3.7 Security Testing
Verifying that RLS roles restrict data correctly and that users cannot access data beyond their authorization.

---

## 4. Pre-Testing Checklist

Before beginning formal testing, confirm the following:

### Environment Readiness
- [ ] Power BI Desktop version matches the agreed development version
- [ ] The report has been published to the correct Power BI Service workspace (Dev/Test/Prod)
- [ ] Test and production data sources are clearly identified and separated
- [ ] A data refresh has been completed with test data
- [ ] Test user accounts with appropriate RLS roles are created and available
- [ ] Access to the source database/warehouse is available for data comparison

### Documentation Readiness
- [ ] Business requirements document (BRD) or functional specification is available
- [ ] Data dictionary and field-level definitions are documented
- [ ] DAX measure definitions are documented
- [ ] RLS role definitions are documented
- [ ] Sample expected outputs or golden reports are available for comparison

### Tooling Readiness
- [ ] Test management tool is set up (Azure DevOps, JIRA, Excel)
- [ ] SQL or query tool is available for source data validation
- [ ] Screenshots / screen recording tool is available
- [ ] Browser testing environments are configured

---

## 5. Data Validation Testing

Data validation is the most critical area of Power BI testing. Every reported figure must be traceable back to the source system.

### 5.1 Source-to-Report Reconciliation

For each key metric in the report:

1. **Identify the source query** — locate the underlying table or view in the data warehouse or source system.
2. **Run the source query** — execute the SQL or source query to produce the expected value.
3. **Compare with the report** — apply matching filters in the report and compare the result.
4. **Document variance** — if values differ, record the delta and investigate.

**Example Test Case:**

| Field | Source SQL Result | Report Value | Pass/Fail | Notes |
|---|---|---|---|---|
| Total Sales (Jan 2025) | $4,250,300 | $4,250,300 | Pass | — |
| Total Units Sold (Q1) | 18,450 | 18,450 | Pass | — |
| Gross Margin % | 34.2% | 34.5% | Fail | Rounding or formula discrepancy |

### 5.2 DAX Measure Validation

For each DAX measure:

- Test with **no filters** applied (grand total check)
- Test with **single filter** applied (e.g., one region, one product)
- Test with **multiple filters** applied (e.g., region + time period)
- Test with **all filter values** to catch aggregation edge cases
- Validate against the equivalent SQL aggregation

**DAX Test Checklist:**

- [ ] CALCULATE overrides are producing correct context transitions
- [ ] Time intelligence functions (YTD, MTD, SAMEPERIODLASTYEAR) return correct values
- [ ] DIVIDE handles zero-denominator cases (no blank/error shown to users)
- [ ] Measures using USERELATIONSHIP activate the correct inactive relationship
- [ ] ALL / ALLEXCEPT functions are not unintentionally removing required filters

### 5.3 Date and Time Validation

- [ ] Date table covers the full range of data (no gaps at start or end)
- [ ] Year, Quarter, Month, Week hierarchies are correct
- [ ] Fiscal year periods match business calendar if applicable
- [ ] Time intelligence measures use the correct date table column
- [ ] Time zones are handled correctly (UTC vs. local time)

### 5.4 Null and Blank Handling

- [ ] Null values in source data display as intended (blank cell, "N/A", or zero)
- [ ] Calculations involving nulls do not produce unexpected totals
- [ ] Filters on null/blank values work correctly
- [ ] Visual totals and subtotals handle blanks without inflating counts

### 5.5 Data Refresh Validation

- [ ] Scheduled refresh completes without errors
- [ ] Refresh history shows success in Power BI Service
- [ ] Report data matches the latest refresh timestamp
- [ ] Incremental refresh (if configured) correctly loads only new/changed records
- [ ] Failures trigger email notifications to the correct distribution list

---

## 6. Visual and UI Testing

### 6.1 Chart and Visual Validation

For each visual in the report:

| Check | Description |
|---|---|
| **Correct visual type** | The visual type is appropriate for the data being shown |
| **Axis labels** | X and Y axis labels are correctly named and formatted |
| **Legend** | Legend items are labeled correctly and match colors used |
| **Data labels** | Data labels show correctly formatted values where enabled |
| **Tooltips** | Tooltip content is accurate and formatted correctly |
| **Sorting** | Default sort order is correct (e.g., descending by value, ascending by date) |
| **Color coding** | Conditional formatting and color rules match the design spec |
| **Truncation** | Long labels are not cut off in a misleading way |

### 6.2 Table and Matrix Validation

- [ ] Column headers match the agreed naming conventions
- [ ] Row and column subtotals and grand totals are correct
- [ ] Conditional formatting (data bars, color scales, icons) applies correctly
- [ ] Column widths are adequate for the data displayed
- [ ] Pagination or scrolling behavior is correct for large datasets
- [ ] Drill-down within matrix rows/columns functions correctly

### 6.3 Card and KPI Visual Validation

- [ ] KPI target values are correctly sourced
- [ ] KPI trend direction (up/down arrow) is logically correct
- [ ] Card formatting (decimal places, currency symbol, abbreviations like K/M) is correct
- [ ] Card values update correctly when slicers are applied

### 6.4 Map Visual Validation

- [ ] Geographic data (countries, states, cities) resolves to the correct location
- [ ] No locations are misplotted due to ambiguous names (e.g., "Portland, OR" vs. "Portland, ME")
- [ ] Bubble size or color intensity scales correctly to the underlying data value
- [ ] Zoom level and default map view are appropriate

### 6.5 Layout and Design Consistency

- [ ] Report theme (fonts, colors, logo) is consistent across all pages
- [ ] Page titles and section headers are present and correctly named
- [ ] Visual spacing and alignment follow the design specification
- [ ] No overlapping visuals on any page
- [ ] Report pages are ordered logically (summary → detail)
- [ ] Page navigation buttons work correctly

---

## 7. Functional Testing

### 7.1 Slicer and Filter Testing

For each slicer and filter panel:

- [ ] All expected values appear in the slicer/filter dropdown
- [ ] Multi-select mode works correctly (AND / OR behavior as designed)
- [ ] Single-select mode prevents multiple selections
- [ ] Slicers sync correctly across report pages (if sync is configured)
- [ ] Clearing a slicer returns visuals to their unfiltered state
- [ ] Default filter values (pre-applied on report open) are correct
- [ ] "Select All" and "Deselect All" options behave correctly
- [ ] Search within a slicer returns correct results for large lists
- [ ] Date range slicers restrict start/end correctly

### 7.2 Cross-Filter and Cross-Highlight Testing

- [ ] Clicking a data point in one visual correctly filters or highlights other visuals
- [ ] Cross-filtering behavior is intentional (not filtering visuals that should be independent)
- [ ] Edit interactions are configured correctly between visuals (filter / highlight / none)
- [ ] Clearing a cross-filter selection restores all visuals

### 7.3 Drill-Through Testing

- [ ] Right-clicking a data point shows the correct drill-through pages in the context menu
- [ ] Drill-through carries the correct filter context to the destination page
- [ ] The "Back" button on the drill-through page returns the user to the correct source page
- [ ] Drill-through pages show only data relevant to the selected context
- [ ] Drill-through is restricted to authorized users where required

### 7.4 Drill-Down Testing

- [ ] Hierarchy drill-down works for all levels (e.g., Year → Quarter → Month → Day)
- [ ] "Drill up" returns to the correct parent level
- [ ] "Show next level" expands all members of the current level
- [ ] Drill-down in one visual does not unintentionally filter other visuals

### 7.5 Bookmark Testing

- [ ] Each bookmark captures the correct visual state (filters, sort order, visible visuals)
- [ ] Navigation buttons linked to bookmarks activate the correct state
- [ ] Bookmarks restore correctly after page navigation and return
- [ ] Report-level vs. page-level bookmark scope is correct

### 7.6 Tooltip Page Testing

- [ ] Custom tooltip pages appear when hovering over the correct visual
- [ ] Tooltip content reflects the correct data context of the hovered data point
- [ ] Tooltip layout and formatting match the design specification
- [ ] Default tooltips appear for visuals without a custom tooltip page

### 7.7 Button and Navigation Testing

- [ ] All navigation buttons link to the correct report pages or external URLs
- [ ] Conditional visibility rules for buttons work correctly
- [ ] Action buttons (e.g., drill-through, bookmark, Q&A) trigger the correct action
- [ ] Hover states and visual feedback on buttons are correct

---

## 8. Performance Testing

### 8.1 Load Time Benchmarks

Define acceptable thresholds based on report complexity:

| Report Type | Target Load Time | Maximum Acceptable |
|---|---|---|
| Simple dashboard (< 5 visuals) | < 3 seconds | 5 seconds |
| Standard report (5–15 visuals) | < 5 seconds | 10 seconds |
| Complex report (15+ visuals, large model) | < 10 seconds | 20 seconds |
| Paginated report | < 8 seconds | 15 seconds |

### 8.2 Performance Analyzer

Use Power BI Desktop's built-in Performance Analyzer:

1. Open **View → Performance Analyzer** in Power BI Desktop.
2. Start recording and interact with the report (apply filters, navigate pages).
3. Review results for each visual:
   - **DAX Query** time — time spent querying the data model
   - **Visual display** time — time spent rendering the visual
   - **Other** — overhead time
4. Flag any visual with a DAX query time exceeding 1 second for optimization.
5. Export results and include in the test report.

### 8.3 Query Performance Checks

- [ ] No single DAX measure takes longer than 2 seconds under typical filter context
- [ ] Complex measures using FILTER or row-context iteration are reviewed for optimization
- [ ] DirectQuery reports meet response time SLAs (if applicable)
- [ ] Import mode datasets do not exceed memory limits on the Power BI Premium/Pro capacity
- [ ] Aggregations are configured for large fact tables where applicable

### 8.4 Concurrent User Testing

For widely distributed reports:

- [ ] Test report load with multiple concurrent users (simulate using Power BI capacity metrics)
- [ ] Monitor Premium capacity CPU and memory utilization during peak simulated load
- [ ] Verify that report throttling or degradation does not occur within expected user count
- [ ] Check scheduled refresh does not conflict with peak usage windows

---

## 9. Security and Access Testing

### 9.1 Row-Level Security (RLS) Testing

RLS must be tested for every defined role before go-live.

**For each RLS role:**

1. Log in as a test user assigned to the role.
2. Open the report and verify only permitted data is visible.
3. Check every visual and every page for unauthorized data exposure.
4. Verify totals and aggregates only reflect permitted data.
5. Test edge cases: users assigned to multiple roles, users with no role assignment.

**RLS Test Matrix Example:**

| Role | User | Expected Region | Report Shows | Pass/Fail |
|---|---|---|---|---|
| Region_North | user_north@company.com | North only | North only | Pass |
| Region_South | user_south@company.com | South only | South only | Pass |
| National_Manager | manager@company.com | All regions | All regions | Pass |
| No Role | new_user@company.com | No data | No data / error | Pass |

### 9.2 Workspace and App Permission Testing

- [ ] Only authorized users can access the Power BI workspace
- [ ] Viewer role users cannot edit, publish, or modify the report
- [ ] Contributor role users can edit but not change workspace settings
- [ ] Admin role is restricted to named individuals
- [ ] Power BI App permissions match the intended audience
- [ ] External sharing (if enabled) is restricted to approved domains

### 9.3 Data Source Credential Testing

- [ ] Data source credentials are stored as service account credentials (not personal)
- [ ] Credentials are not embedded in the .pbix file
- [ ] Data gateway (if used) is configured with the correct service account
- [ ] Connection strings do not expose sensitive parameters

### 9.4 Sensitive Data Handling

- [ ] PII fields (names, emails, SSNs) are masked or excluded where not required
- [ ] Sensitive financial data is accessible only to authorized roles
- [ ] Export to Excel/CSV is disabled for reports containing sensitive data where required
- [ ] Print and screenshot restrictions are configured if applicable

---

## 10. Cross-Platform and Compatibility Testing

### 10.1 Browser Compatibility

Test in all browsers used by the target audience:

| Browser | Version | Pass/Fail | Notes |
|---|---|---|---|
| Microsoft Edge (Chromium) | Latest | | |
| Google Chrome | Latest | | |
| Mozilla Firefox | Latest | | |
| Safari | Latest | | |
| Internet Explorer 11 | Legacy (limited support) | | |

**Checks for each browser:**

- [ ] All visuals render correctly
- [ ] Fonts and icons display correctly
- [ ] Slicers, filters, and drill-throughs function correctly
- [ ] No JavaScript console errors
- [ ] Report loads within the performance threshold

### 10.2 Device and Screen Size Testing

| Device | Screen Size | Resolution | Pass/Fail |
|---|---|---|---|
| Desktop (standard) | 1920×1080 | 100% zoom | |
| Desktop (large) | 2560×1440 | 100% zoom | |
| Laptop | 1366×768 | 100% zoom | |
| Tablet (landscape) | 1024×768 | | |
| Tablet (portrait) | 768×1024 | | |
| Mobile (Power BI app) | 375×812 | | |

- [ ] Report layout adapts to smaller screens without critical information being hidden
- [ ] Mobile layout (if configured) renders correctly in the Power BI mobile app
- [ ] Touch interactions (tap, swipe, pinch) work correctly on mobile/tablet

### 10.3 Power BI Mobile App Testing

- [ ] Report is accessible in the Power BI iOS and Android apps
- [ ] Mobile-optimized layout (if created) displays in the app
- [ ] Offline access (if configured) works with cached data
- [ ] Push notifications for data alerts function correctly

---

## 11. Regression Testing

### 11.1 When to Run Regression Tests

Trigger a regression test cycle after:

- Any change to DAX measures or calculated columns
- Any change to data source queries or transformations (Power Query / M)
- Adding, removing, or modifying report visuals
- Changes to RLS roles or rules
- Power BI Desktop or Service platform updates
- Changes to the underlying data model schema
- Data source schema changes (new columns, renamed tables)

### 11.2 Regression Test Scope

Maintain a regression test suite covering:

- [ ] All key DAX measures (total, YTD, prior period comparison)
- [ ] All slicer and filter combinations used in standard workflows
- [ ] All drill-through and navigation paths
- [ ] All RLS roles
- [ ] Report load time benchmarks
- [ ] All cross-filter interactions

### 11.3 Automating Regression Tests

Consider automation for high-frequency or large-scale regression needs:

- **DAX Studio** — export and re-execute DAX queries to compare results
- **Tabular Editor** — run automated best-practice analyzer checks on the data model
- **Power BI REST API** — automate dataset refresh and compare query results programmatically
- **Azure DevOps Pipelines** — trigger test scripts after each deployment to the test workspace

---

## 12. User Acceptance Testing (UAT)

### 12.1 UAT Process

| Step | Activity | Owner |
|---|---|---|
| 1 | Distribute UAT test cases and report access to business stakeholders | QA Lead |
| 2 | Conduct UAT kick-off meeting to explain scope and process | QA Lead / PM |
| 3 | Business users execute test cases and record results | Business Stakeholders |
| 4 | Defects are logged in the agreed defect tracking tool | Business Stakeholders |
| 5 | Development team triages and resolves defects | Developer |
| 6 | Fixed defects are re-tested by business stakeholders | Business Stakeholders |
| 7 | UAT sign-off is obtained from the business owner | Business Owner |

### 12.2 UAT Sign-Off Criteria

UAT is considered passed when:

- [ ] All critical (P1) and high (P2) defects are resolved and re-tested
- [ ] No open defects exceed the agreed severity threshold
- [ ] At least 90% of test cases have passed
- [ ] Business owner has formally signed off in writing
- [ ] Data reconciliation report confirms accuracy within agreed tolerance (e.g., ±0.01%)

### 12.3 UAT Test Case Structure

Each UAT test case should include:

| Field | Description |
|---|---|
| **Test Case ID** | Unique identifier (e.g., UAT-001) |
| **Business Requirement** | Reference to the BRD or user story |
| **Test Scenario** | Plain-language description of what is being tested |
| **Pre-conditions** | Filters, date ranges, or setup required before the test |
| **Test Steps** | Step-by-step instructions |
| **Expected Result** | The value or behavior expected |
| **Actual Result** | What the tester observed |
| **Status** | Pass / Fail / Blocked |
| **Defect ID** | Reference to the logged defect (if failed) |
| **Tester** | Name and date |

---

## 13. Defect Management

### 13.1 Defect Severity Classification

| Severity | Definition | Examples |
|---|---|---|
| **P1 – Critical** | Report is unusable or produces materially incorrect data | Wrong revenue total, RLS exposing unauthorized data, report crashes on load |
| **P2 – High** | Key functionality is broken or significant data discrepancy | Drill-through not working, major visual rendering failure, filter not applying |
| **P3 – Medium** | Non-critical functionality broken or minor data discrepancy | Tooltip showing wrong label, slicer default incorrect, minor formatting issue |
| **P4 – Low** | Cosmetic or minor usability issue | Font size inconsistency, alignment off by pixels, tooltip grammar error |

### 13.2 Defect Lifecycle

```
New → Assigned → In Progress → Fixed → Ready for Retest → Retest Pass → Closed
                                                          → Retest Fail → Reopened → In Progress
```

### 13.3 Defect Report Fields

Each defect should be logged with:

- **Defect ID** — unique identifier
- **Title** — concise description of the defect
- **Severity** — P1 / P2 / P3 / P4
- **Priority** — business priority (may differ from severity)
- **Report / Page** — which report and page the defect was found on
- **Steps to Reproduce** — exact steps to reproduce the issue
- **Expected Result** — what should happen
- **Actual Result** — what actually happened
- **Screenshot / Evidence** — attached screenshot or screen recording
- **Environment** — browser, device, workspace (Dev/Test)
- **Assigned To** — developer responsible for the fix
- **Date Found / Date Fixed** — tracking dates

---

## 14. Test Reporting

### 14.1 Test Summary Report

At the end of each test cycle, produce a Test Summary Report containing:

- **Test Cycle** — name and dates of the test cycle
- **Scope** — reports and features tested
- **Test Execution Summary** — total test cases, passed, failed, blocked, skipped
- **Defect Summary** — total defects by severity, open vs. closed
- **Data Reconciliation Results** — summary of source-to-report comparison
- **Performance Results** — load time measurements vs. targets
- **RLS Test Results** — summary of roles tested
- **UAT Sign-Off Status** — pending / obtained
- **Go/No-Go Recommendation** — tester's recommendation with rationale
- **Open Risks** — any known issues deferred to post-go-live

### 14.2 Test Metrics

Track the following metrics across test cycles:

| Metric | Formula |
|---|---|
| Test Pass Rate | (Passed / Total Executed) × 100 |
| Defect Detection Rate | Defects found in testing / Total defects (including post-go-live) |
| Defect Density | Defects per report page or per DAX measure |
| Test Coverage | Test cases executed / Total test cases planned |
| Mean Time to Fix | Average time from defect raised to defect closed |

---

## 15. Best Practices

### Data Model
- Keep the data model star-schema or snowflake; avoid wide flat tables in the model
- Use a dedicated, marked date table for all time intelligence
- Avoid bi-directional relationships unless absolutely necessary; document the reason when used
- Name measures and columns clearly, using consistent conventions (e.g., `[Total Sales $]`, `[Sales YTD $]`)
- Place all measures in dedicated measure tables, not in fact or dimension tables

### DAX
- Always test measures in DAX Studio before embedding them in a report
- Use variables (`VAR`) in complex measures for readability and to avoid repeated evaluation
- Document the business logic intent in the measure description field (not in comments inside the DAX)
- Avoid using FILTER on a whole table when a simple filter argument will work

### Performance
- Use Import mode over DirectQuery where data volume and refresh frequency allow
- Limit visuals per page to 8–12; use navigation to split dense content across pages
- Avoid high-cardinality columns in slicers (more than ~500 values degrades usability)
- Disable auto date/time if a dedicated date table is in use
- Use aggregations for very large fact tables (> 100M rows)

### Testing Process
- Never test directly in the production workspace; use a dedicated test workspace
- Always use separate test user accounts for RLS testing (never impersonate via "View as Role" alone for sign-off)
- Maintain a test data set that covers boundary conditions, nulls, zeros, and maximum values
- Version-control test cases and test results alongside the .pbix file in source control
- Perform a dry-run of the go-live deployment procedure in the test environment before production release

---

## 16. Appendix: Test Case Templates

### Template A — Data Validation Test Case

```
Test Case ID  : DV-001
Report        : [Report Name]
Page          : [Page Name]
Visual        : [Visual Name / KPI Name]
Requirement   : [BRD Reference]

Filter Context:
  - Date Range   : [e.g., January 2025]
  - Region       : [e.g., North America]
  - Product      : [e.g., All]

Source Validation Query:
  SELECT SUM(SalesAmount) 
  FROM FactSales 
  WHERE SaleDate BETWEEN '2025-01-01' AND '2025-01-31'
    AND Region = 'North America'

Expected Value : [Value from source query]
Actual Value   : [Value shown in report]
Variance       : [Delta / % difference]
Status         : Pass / Fail
Notes          : [Any observations]
Tester         : [Name]
Date           : [Date]
```

### Template B — Functional Test Case

```
Test Case ID  : FT-001
Report        : [Report Name]
Page          : [Page Name]
Feature       : [e.g., Region Slicer Cross-filtering]

Pre-conditions:
  - Open the report with no filters applied
  - Navigate to the [Page Name] page

Test Steps:
  1. Click the "North" value in the Region slicer
  2. Observe the Sales by Product visual
  3. Note the total displayed in the Total Sales card
  4. Clear the slicer selection

Expected Result:
  - Sales by Product visual shows only North region products
  - Total Sales card reflects North region total only
  - Clearing slicer restores all-region values

Actual Result  : [Observed behavior]
Status         : Pass / Fail
Screenshot     : [Attached]
Tester         : [Name]
Date           : [Date]
```

### Template C — RLS Test Case

```
Test Case ID  : RLS-001
Report        : [Report Name]
Role          : [RLS Role Name]
Test User     : [user@company.com]

Expected Data Access:
  - Regions     : [e.g., North only]
  - Business Units: [e.g., Retail only]
  - Date Range  : [No restriction]

Test Steps:
  1. Log into Power BI Service as [user@company.com]
  2. Navigate to [Report Name]
  3. Check the Region slicer — only permitted values should appear
  4. Check every visual on every page for unauthorized data
  5. Verify totals reflect only permitted data

Unauthorized Data Visible? : Yes / No
If Yes, describe           : [Details]
Status                     : Pass / Fail
Tester                     : [Name]
Date                       : [Date]
```

### Template D — Performance Test Case

```
Test Case ID   : PERF-001
Report         : [Report Name]
Page           : [Page Name]
Environment    : [Power BI Service — Test Workspace]

Test Conditions:
  - Browser    : [e.g., Chrome 124]
  - Network    : [e.g., Corporate LAN]
  - User Load  : [e.g., Single user]

Measurement Method:
  - Power BI Performance Analyzer (Desktop)
  - Browser Network tab (Service)

Results:

  Visual Name          | DAX Query (ms) | Visual Display (ms) | Total (ms) | Target (ms) | Pass/Fail
  ---------------------|---------------|---------------------|------------|-------------|----------
  Total Sales Card     |               |                     |            | 1000        |
  Sales by Region Bar  |               |                     |            | 2000        |
  Monthly Trend Line   |               |                     |            | 2000        |
  Full Page Load       |               |                     |            | 5000        |

Notes          : [Observations or bottlenecks identified]
Tester         : [Name]
Date           : [Date]
```

---

*Document Version: 1.0 | Last Updated: June 2026 | Owner: QA / BI Center of Excellence*
