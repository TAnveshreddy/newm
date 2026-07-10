# 🏫 Carmel Convent School — School Management App

**Village Palakurthy, Telangana, India · Academic Year 2026–27**

A complete, self-contained school management web app in a **single HTML file**.
No server, no database, no installation — just open `index.html` in any modern
browser (Chrome, Edge, Firefox). All data is stored in the browser's
localStorage and can be exported/imported as CSV or JSON.

## 🚀 How to run

1. Download / clone this folder.
2. Double-click **`index.html`** (or right-click → Open with → your browser).
3. Sign in with one of the demo accounts below.

## 🔐 Demo logins (3 roles)

| Role | User ID | Password | Access |
|------|---------|----------|--------|
| 🎓 Student | `CCS1001` … `CCS1025` | `student123` | Sees **only their own** attendance, report card, fees, bus details |
| 👩‍🏫 Staff | `STF01` … `STF10` | `staff123` | Staff directory (salary hidden), own profile, exam schedule, notices |
| 🛡️ Admin | `admin` | `admin123` | **Full access** — add / edit / delete everything, import & export data |

## ✨ Features

- **Dashboard** — role-specific stats, class-strength chart, attendance trend, pending fee balances
- **Students register** — search, filter by class, add / edit / delete, CSV export
- **Attendance** — mark P / A / L per class per day (admin); students see their own day-by-day record and split chart
- **Exam schedule** — FA-1, FA-2, SA-1 time tables per class; admin can add/edit/delete entries
- **Marks & Reports** — spreadsheet-style marks entry per exam/class; printable **progress report card** with grades (A1–E)
- **Tuition fees** — fee structure per class/term (editable), payment receipts, paid / partial / due status per student
- **Bus & transport** — routes with driver & stops, per-term bus fees, bus fee receipts
- **Staff details** — directory with designation, qualification, contact; salary visible to admin only
- **Notices** — announcements targeted to everyone / students / staff
- **Import / Export (admin)**
  - CSV import for students, staff, attendance, marks, tuition & bus payments (append/update or replace, with validation and blank templates)
  - CSV export of every register
  - Full **JSON backup & restore**
  - One-click reset to sample data

## 📥 CSV import formats

Header row is required. Download a blank template from **Import / Export** page.

| Data | Columns |
|------|---------|
| Students | `id,name,cls,sec,roll,gender,dob,guardian,phone,village,busRoute` |
| Staff | `id,name,designation,subject,qualification,phone,email,joined,salary` |
| Attendance | `date,studentId,status` (status = P / A / L) |
| Marks | `studentId,exam,subject,marks,max` |
| Tuition payments | `receiptNo,studentId,term,amount,date,mode` |
| Bus payments | `receiptNo,studentId,term,amount,date,mode` |

Ready-made example files are in [`sample-import/`](sample-import/).

## 📊 Sample data included

- 25 students (Classes 6–10, Section A) with guardians, villages and bus routes
- 10 staff members (Principal → Lab Assistant) with salaries
- Full attendance from school reopening (12 June 2026) to date
- FA-1 marks for all students in 6 subjects + FA-2 / SA-1 schedules
- Tuition fee structure, payment receipts and dues
- 3 bus routes with drivers, stops and transport fee receipts
- School notices

> **Note:** This is a demo/starter app. Data lives in the browser that opened the
> file — use the JSON backup to move data between computers. Passwords are stored
> in plain text in localStorage, so do not use it for real confidential records
> without adding a proper backend.
