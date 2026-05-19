# Power BI Desktop Setup Guide
## Sales Analytics Dashboard with Row-Level Security

---

## Prerequisites
- Power BI Desktop (free download from microsoft.com/en-us/power-bi/desktop)
- The Excel data file: `PowerBI_Data.xlsx`

---

## Step 1 — Import the Data (5 minutes)

1. Open Power BI Desktop → **Get Data** → **Excel Workbook**
2. Browse to `PowerBI_Data.xlsx` and click **Open**
3. In the Navigator, select ALL 4 sheets: **Customers**, **Products**, **Users**, **Sales**
4. Click **Transform Data** (not Load) to open Power Query Editor

---

## Step 2 — Apply Power Query Transformations (3 minutes)

For each table, open the **Advanced Editor** and paste the corresponding query from `M_Queries.pq`:

| Table     | Action                                              |
|-----------|-----------------------------------------------------|
| Sales     | Set date types, add `Days to Ship`, `Is Returned`   |
| Customers | Set date type, add `Full Name`                      |
| Products  | Add `Stock Status`, `Price Range`                   |
| Users     | Set date type, add `Login Email` (lowercase)        |

**Add the DateTable** (New Query → Blank Query, paste DateTable M code)

Click **Close & Apply** when done.

---

## Step 3 — Build the Data Model (2 minutes)

Go to **Model View** (icon on left sidebar).

Create these relationships by dragging columns:

| From (Many)            | To (One)              |
|------------------------|-----------------------|
| Sales[Customer ID]     | Customers[Customer ID]|
| Sales[Product ID]      | Products[Product ID]  |
| Sales[User ID]         | Users[User ID]        |
| Sales[Order Date]      | DateTable[Date]       |

Right-click `DateTable` → **Mark as date table** → select `Date` column.

---

## Step 4 — Add DAX Measures (5 minutes)

In **Report View**, right-click the `Sales` table → **New Measure**.
Paste each measure from `DAX_Measures.dax` one at a time.

**Must-have measures (start with these):**
```
Total Revenue = SUM(Sales[Net Sales])
Total Profit = SUM(Sales[Profit])
Total Orders = COUNTROWS(Sales)
Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0)
Revenue YoY Growth % = DIVIDE([Total Revenue]-[Revenue PY],[Revenue PY],BLANK())
Return Rate % = DIVIDE([Returned Orders], [Total Orders], 0)
Target Achievement % = DIVIDE([Total Revenue], SUM(Users[Sales Target]), 0)
```

---

## Step 5 — Configure Row-Level Security (3 minutes)

### Modeling tab → Manage Roles → Create

**Option A — Static Role per Location (simpler):**
1. Click **+ New Role** → name it `London`
2. Select the `Users` table
3. Enter filter: `[Location] = "London"`
4. Click **Save**
5. Repeat for Hamburg, Lyon, Toronto, etc.

**Option B — Dynamic Role (recommended for Production):**
1. Click **+ New Role** → name it `ByLocation`
2. Select the `Users` table
3. Enter filter: `[Email] = LOWER(USERPRINCIPALNAME())`
4. Click **Save**

### Test the RLS:
- **Modeling** → **View as** → Select `London` role
- Dashboard should now show **45 orders / ~$283K revenue** only
- Headers should reflect London users' data

---

## Step 6 — Build the Visuals (15 minutes)

### Page 1: Executive Summary
| Visual            | Type         | Fields                                    |
|-------------------|--------------|-------------------------------------------|
| Total Revenue     | Card         | [Total Revenue]                           |
| Total Profit      | Card         | [Total Profit]                            |
| Total Orders      | Card         | [Total Orders]                            |
| Profit Margin     | Card         | [Profit Margin %]                         |
| Revenue Trend     | Line Chart   | X=DateTable[Month Name], Y=[Total Revenue]|
| Revenue by Category| Bar Chart   | X=Sales[Category], Y=[Total Revenue]      |
| Channel Mix       | Donut Chart  | Legend=Sales[Sales Channel], Y=[Total Revenue]|
| Order Status      | Donut Chart  | Legend=Sales[Order Status], Y=[Total Orders]|

### Page 2: Sales Performance
| Visual            | Type         | Fields                                    |
|-------------------|--------------|-------------------------------------------|
| Revenue MTD       | Card         | [Revenue MTD]                             |
| Revenue YTD       | Card         | [Revenue YTD]                             |
| YoY Growth        | Card         | [Revenue YoY Growth %]                    |
| Monthly Trend     | Line Chart   | Multiple years comparison                 |
| Revenue by Country| Map / Bar    | Customers[Country], [Total Revenue]       |
| Payment Methods   | Donut        | Sales[Payment Method], [Total Revenue]    |

### Page 3: Product Analysis
| Visual            | Type         | Fields                                    |
|-------------------|--------------|-------------------------------------------|
| Top 10 Products   | Bar Chart    | Products[Product Name], [Total Revenue]   |
| Margin by Category| Bar Chart    | Sales[Category], [Profit Margin %]        |
| Category Scatter  | Scatter      | X=[Total Revenue], Y=[Profit Margin %]    |

### Page 4: Customer Insights
| Visual            | Type         | Fields                                    |
|-------------------|--------------|-------------------------------------------|
| Active Customers  | Card         | [Active Customers]                        |
| By Segment        | Donut Chart  | Customers[Segment], [Total Revenue]       |
| By Country        | Bar Chart    | Customers[Country], [Total Orders]        |

### Page 5: Team Performance
| Visual            | Type         | Fields                                    |
|-------------------|--------------|-------------------------------------------|
| Target Achievement| Gauge        | [Target Achievement %]                    |
| Revenue vs Target | Clustered Bar| Users[Name], [Total Revenue], [Total Target]|
| Rep Table         | Matrix       | Users[Name,Location,Role], all measures   |

---

## Step 7 — Add Slicers (Filters)

Add slicers to each page:
- **DateTable[Year]** — single select dropdown
- **DateTable[Quarter]** — single select
- **Sales[Category]** — multi-select list
- **Sales[Sales Channel]** — multi-select
- **Sales[Order Status]** — multi-select

Sync slicers across pages: **View → Sync Slicers**

---

## Step 8 — Publish & Assign RLS Users

1. **File → Publish → Publish to Power BI**
2. In Power BI Service: go to the **Dataset → Security**
3. Add users to each role:
   - London role: `hannah.martin@yourcompany.com`, `robert.brown@yourcompany.com`, `lisa.taylor@yourcompany.com`
   - Hamburg role: `noah.white@yourcompany.com`, `patricia.davis@yourcompany.com`
   - etc.

---

## Summary: What Business Users See

| User Location | Orders Visible | Revenue Visible | Access Level          |
|---------------|----------------|-----------------|----------------------|
| London        | 45             | $283,661        | London orders only    |
| Hamburg       | ~35            | ~$220K          | Hamburg orders only   |
| Lyon          | ~30            | ~$190K          | Lyon orders only      |
| Admin         | 500            | $2,608,396      | All data              |

---

## Key KPIs Summary (All Data)

| KPI                    | Value          |
|------------------------|----------------|
| Total Revenue          | $2,608,396     |
| Total Profit           | $1,107,683     |
| Profit Margin          | 42.5%          |
| Total Orders           | 500            |
| Average Order Value    | $5,217         |
| Return Rate            | 19.0%          |
| Top Category           | Electronics    |
| Top Channel            | Wholesale      |
| Revenue Growth (2025)  | +11.5% vs 2024 |
