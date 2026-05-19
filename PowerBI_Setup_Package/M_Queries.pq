// ============================================================
// POWER QUERY M SCRIPTS - Sales Analytics Data Model
// Copy each query into Power BI Desktop > Transform Data
// ============================================================

// ============================================================
// TABLE 1: Sales (Fact Table)
// ============================================================
let
    Source = Excel.Workbook(File.Contents("PowerBI_Data.xlsx"), null, true),
    Sales_Sheet = Source{[Item="Sales",Kind="Sheet"]}[Data],
    PromoteHeaders = Table.PromoteHeaders(Sales_Sheet, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders, {
        {"Order ID",       type text},
        {"Order Date",     type date},
        {"Year",           Int64.Type},
        {"Month",          Int64.Type},
        {"Quarter",        type text},
        {"Customer ID",    type text},
        {"Product ID",     type text},
        {"User ID",        type text},
        {"Category",       type text},
        {"Quantity",       Int64.Type},
        {"Unit Price",     type number},
        {"Unit Cost",      type number},
        {"Gross Sales",    type number},
        {"Discount %",     type number},
        {"Discount Amount",type number},
        {"Net Sales",      type number},
        {"Total Cost",     type number},
        {"Profit",         type number},
        {"Profit Margin %",type number},
        {"Sales Channel",  type text},
        {"Order Status",   type text},
        {"Ship Date",      type date},
        {"Payment Method", type text}
    }),
    AddShipDays = Table.AddColumn(ChangeTypes, "Days to Ship",
        each Duration.Days([Ship Date] - [Order Date]), Int64.Type),
    AddIsReturned = Table.AddColumn(AddShipDays, "Is Returned",
        each if [Order Status] = "Returned" then 1 else 0, Int64.Type),
    AddIsCompleted = Table.AddColumn(AddIsReturned, "Is Completed",
        each if [Order Status] = "Completed" then 1 else 0, Int64.Type),
    RenameColumns = Table.RenameColumns(AddIsCompleted, {
        {"Profit Margin %", "Profit Margin Pct"},
        {"Discount %", "Discount Pct"}
    })
in
    RenameColumns


// ============================================================
// TABLE 2: Customers (Dimension)
// ============================================================
let
    Source = Excel.Workbook(File.Contents("PowerBI_Data.xlsx"), null, true),
    Cust_Sheet = Source{[Item="Customers",Kind="Sheet"]}[Data],
    PromoteHeaders = Table.PromoteHeaders(Cust_Sheet, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders, {
        {"Customer ID",        type text},
        {"First Name",         type text},
        {"Last Name",          type text},
        {"Email",              type text},
        {"Phone",              type text},
        {"Address",            type text},
        {"City",               type text},
        {"Country",            type text},
        {"Postal Code",        type text},
        {"Segment",            type text},
        {"Registration Date",  type date},
        {"Credit Limit",       type number}
    }),
    AddFullName = Table.AddColumn(ChangeTypes, "Full Name",
        each [First Name] & " " & [Last Name], type text),
    AddCustomerAge = Table.AddColumn(AddFullName, "Customer Tenure (Days)",
        each Duration.Days(Date.From(DateTime.LocalNow()) - [Registration Date]), Int64.Type)
in
    AddCustomerAge


// ============================================================
// TABLE 3: Products (Dimension)
// ============================================================
let
    Source = Excel.Workbook(File.Contents("PowerBI_Data.xlsx"), null, true),
    Prod_Sheet = Source{[Item="Products",Kind="Sheet"]}[Data],
    PromoteHeaders = Table.PromoteHeaders(Prod_Sheet, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders, {
        {"Product ID",      type text},
        {"Product Name",    type text},
        {"Category",        type text},
        {"Sub Category",    type text},
        {"Brand",           type text},
        {"Unit Cost",       type number},
        {"Unit Price",      type number},
        {"Profit Margin %", type number},
        {"Stock Quantity",  Int64.Type},
        {"Reorder Level",   Int64.Type},
        {"Supplier",        type text},
        {"Weight (kg)",     type number},
        {"Rating",          type number}
    }),
    AddStockStatus = Table.AddColumn(ChangeTypes, "Stock Status",
        each if [Stock Quantity] <= [Reorder Level] then "Reorder Required"
             else if [Stock Quantity] <= [Reorder Level] * 2 then "Low Stock"
             else "Adequate", type text),
    AddPriceRange = Table.AddColumn(AddStockStatus, "Price Range",
        each if [Unit Price] < 100 then "Budget"
             else if [Unit Price] < 500 then "Mid-Range"
             else "Premium", type text)
in
    AddPriceRange


// ============================================================
// TABLE 4: Users / Sales Reps (Dimension + RLS)
// ============================================================
let
    Source = Excel.Workbook(File.Contents("PowerBI_Data.xlsx"), null, true),
    Users_Sheet = Source{[Item="Users",Kind="Sheet"]}[Data],
    PromoteHeaders = Table.PromoteHeaders(Users_Sheet, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders, {
        {"User ID",      type text},
        {"Name",         type text},
        {"First Name",   type text},
        {"Last Name",    type text},
        {"Email",        type text},
        {"Role",         type text},
        {"Department",   type text},
        {"Country",      type text},
        {"Location",     type text},
        {"Phone",        type text},
        {"Join Date",    type date},
        {"Manager ID",   type text},
        {"Sales Target", type number}
    }),
    AddUserEmail = Table.AddColumn(ChangeTypes, "Login Email",
        each Text.Lower([Email]), type text)
in
    AddUserEmail


// ============================================================
// TABLE 5: DateTable (Auto-generated Date Dimension)
// ============================================================
let
    StartDate = #date(2022, 1, 1),
    EndDate   = #date(2025, 12, 31),
    DayCount  = Duration.Days(EndDate - StartDate) + 1,
    DateList  = List.Dates(StartDate, DayCount, #duration(1,0,0,0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    ChangeType = Table.TransformColumnTypes(DateTable, {{"Date", type date}}),
    AddYear    = Table.AddColumn(ChangeType,    "Year",        each Date.Year([Date]),             Int64.Type),
    AddMonth   = Table.AddColumn(AddYear,       "Month",       each Date.Month([Date]),            Int64.Type),
    AddDay     = Table.AddColumn(AddMonth,      "Day",         each Date.Day([Date]),              Int64.Type),
    AddQtr     = Table.AddColumn(AddDay,        "Quarter",     each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    AddQtrNum  = Table.AddColumn(AddQtr,        "Quarter Num", each Date.QuarterOfYear([Date]),   Int64.Type),
    AddWeek    = Table.AddColumn(AddQtrNum,     "Week Num",    each Date.WeekOfYear([Date]),       Int64.Type),
    AddMonthName=Table.AddColumn(AddWeek,       "Month Name",  each Date.ToText([Date],"MMMM"),   type text),
    AddMonthShort=Table.AddColumn(AddMonthName, "Month Short", each Date.ToText([Date],"MMM"),    type text),
    AddDayName = Table.AddColumn(AddMonthShort, "Day Name",    each Date.ToText([Date],"dddd"),   type text),
    AddYearMonth=Table.AddColumn(AddDayName,    "Year-Month",  each Text.From([Year]) & "-" & Text.PadStart(Text.From([Month]),2,"0"), type text),
    AddYearQtr = Table.AddColumn(AddYearMonth,  "Year-Qtr",   each Text.From([Year]) & " " & [Quarter], type text),
    AddIsWeekend=Table.AddColumn(AddYearQtr,    "Is Weekend",  each Date.DayOfWeek([Date]) >= 5,  type logical),
    AddFY       = Table.AddColumn(AddIsWeekend, "Fiscal Year", each if Date.Month([Date]) >= 4
                                                                     then "FY" & Text.From(Date.Year([Date]))
                                                                     else "FY" & Text.From(Date.Year([Date])-1), type text)
in
    AddFY
