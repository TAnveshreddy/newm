#!/usr/bin/env python3
"""
make_healthcare_dataset.py
--------------------------
Generate a small, self-contained *healthcare* semantic model so the chatbot's
report picker has a second report to switch to — and to demonstrate that the
generic ("model-agnostic") profile works on a completely different schema.

Writes:
  datasets/healthcare/encounters.csv, patients.csv, providers.csv
  datasets/healthcare/semantic_model.json   (profile: "generic")

Synthetic data only — no real patient information.  Standard library only.
"""
from __future__ import annotations

import csv
import json
import os
import random
from datetime import date, timedelta

random.seed(20260916)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "datasets", "healthcare")
os.makedirs(OUT, exist_ok=True)

DEPARTMENTS = ["Cardiology", "Orthopedics", "Oncology", "Neurology", "Pediatrics",
               "Emergency", "General Surgery", "Maternity"]
DIAGNOSES = {
    "Cardiology": ["Heart Failure", "Arrhythmia", "Chest Pain"],
    "Orthopedics": ["Hip Fracture", "Knee Replacement", "Back Pain"],
    "Oncology": ["Breast Cancer", "Lung Cancer", "Lymphoma"],
    "Neurology": ["Stroke", "Seizure", "Migraine"],
    "Pediatrics": ["Asthma", "Infection", "Fever"],
    "Emergency": ["Trauma", "Sepsis", "Overdose"],
    "General Surgery": ["Appendicitis", "Hernia", "Gallstones"],
    "Maternity": ["Delivery", "Prenatal Care", "C-Section"],
}
ENCOUNTER_TYPES = ["Inpatient", "Outpatient", "Emergency", "Day Surgery"]
DISCHARGE = ["Home", "Home Health", "Transferred", "Rehab", "Expired"]
SPECIALTIES = ["Cardiologist", "Surgeon", "Oncologist", "Neurologist",
               "Pediatrician", "ER Physician", "General Practitioner", "OB-GYN"]
GENDERS = ["Female", "Male"]
AGE_GROUPS = ["0-17", "18-34", "35-49", "50-64", "65-79", "80+"]
CITIES = ["Boston", "Austin", "Denver", "Seattle", "Chicago", "Miami", "Phoenix", "Atlanta"]
STATES = {"Boston": "MA", "Austin": "TX", "Denver": "CO", "Seattle": "WA",
          "Chicago": "IL", "Miami": "FL", "Phoenix": "AZ", "Atlanta": "GA"}
INSURERS = ["Medicare", "Medicaid", "BlueCross", "Aetna", "UnitedHealth", "Self-Pay"]
FIRST = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
         "David", "Elizabeth", "Maria", "Wei", "Aisha", "Carlos", "Priya", "Noah"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Chen", "Patel", "Kim", "Nguyen", "Khan", "Lopez"]


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


# ---- Providers ----
providers = []
for i in range(1, 26):
    dept = random.choice(DEPARTMENTS)
    providers.append([
        f"PRV-{i:03d}", f"Dr. {random.choice(FIRST)} {random.choice(LAST)}",
        SPECIALTIES[DEPARTMENTS.index(dept)], dept,
    ])
write_csv("providers.csv", ["Provider ID", "Provider Name", "Specialty", "Department"], providers)

# ---- Patients ----
patients = []
for i in range(1, 121):
    city = random.choice(CITIES)
    patients.append([
        f"PT-{i:04d}", random.choice(FIRST), random.choice(LAST),
        random.choice(GENDERS), random.choice(AGE_GROUPS), city, STATES[city],
        random.choice(INSURERS),
    ])
write_csv("patients.csv",
          ["Patient ID", "First Name", "Last Name", "Gender", "Age Group", "City", "State", "Insurance"],
          patients)

# ---- Encounters (fact) ----
start = date(2022, 1, 1)
span = (date(2025, 12, 31) - start).days
encounters = []
for i in range(1, 651):
    prov = random.choice(providers)
    dept = prov[3]
    diag = random.choice(DIAGNOSES[dept])
    etype = random.choice(ENCOUNTER_TYPES)
    los = max(0, int(random.gauss(4, 3))) if etype == "Inpatient" else random.choice([0, 0, 1])
    charges = round(random.uniform(1500, 60000) * (1 + los * 0.15), 2)
    cost = round(charges * random.uniform(0.45, 0.75), 2)
    reimb = round(charges * random.uniform(0.55, 0.92), 2)
    readmit = "Yes" if random.random() < 0.12 else "No"
    disch = random.choices(DISCHARGE, weights=[55, 15, 10, 15, 5])[0]
    admit = start + timedelta(days=random.randint(0, span))
    encounters.append([
        f"ENC-{i:05d}", admit.isoformat(), random.choice(patients)[0], prov[0],
        dept, diag, etype, los, charges, cost, reimb, readmit, disch,
    ])
write_csv("encounters.csv",
          ["Encounter ID", "Admit Date", "Patient ID", "Provider ID", "Department",
           "Diagnosis", "Encounter Type", "Length of Stay", "Total Charges", "Total Cost",
           "Reimbursement", "Readmitted", "Discharge Status"],
          encounters)


# ---- semantic_model.json (generic profile) ----
def cols(*specs):
    return [{"name": n, "dataType": t, "sourceColumn": n, "summarizeBy": "none"} for n, t in specs]


model = {
    "name": "HospitalAnalytics",
    "description": "Hospital encounters, charges, length of stay and outcomes.",
    "profile": "generic",
    "factTable": "Encounters",
    "dateColumn": "Admit Date",
    "tables": [
        {"name": "Encounters", "rowCount": len(encounters), "columns": cols(
            ("Encounter ID", "string"), ("Admit Date", "dateTime"), ("Patient ID", "string"),
            ("Provider ID", "string"), ("Department", "string"), ("Diagnosis", "string"),
            ("Encounter Type", "string"), ("Length of Stay", "int64"), ("Total Charges", "double"),
            ("Total Cost", "double"), ("Reimbursement", "double"), ("Readmitted", "string"),
            ("Discharge Status", "string"))},
        {"name": "Patients", "rowCount": len(patients), "columns": cols(
            ("Patient ID", "string"), ("First Name", "string"), ("Last Name", "string"),
            ("Gender", "string"), ("Age Group", "string"), ("City", "string"),
            ("State", "string"), ("Insurance", "string"))},
        {"name": "Providers", "rowCount": len(providers), "columns": cols(
            ("Provider ID", "string"), ("Provider Name", "string"),
            ("Specialty", "string"), ("Department", "string"))},
    ],
    "relationships": [
        {"name": "Enc_Patients", "fromTable": "Encounters", "fromColumn": "Patient ID",
         "toTable": "Patients", "toColumn": "Patient ID", "crossFilteringBehavior": "oneDirection"},
        {"name": "Enc_Providers", "fromTable": "Encounters", "fromColumn": "Provider ID",
         "toTable": "Providers", "toColumn": "Provider ID", "crossFilteringBehavior": "oneDirection"},
    ],
    "measureSpecs": [
        {"name": "Total Encounters", "kind": "count", "column": "*", "format": "int",
         "dax": "COUNTROWS(Encounters)", "definition": "Number of encounters (visits/admissions)."},
        {"name": "Total Charges", "kind": "sum", "column": "Total Charges", "format": "currency",
         "dax": "SUM(Encounters[Total Charges])", "definition": "Total billed charges."},
        {"name": "Total Cost", "kind": "sum", "column": "Total Cost", "format": "currency",
         "dax": "SUM(Encounters[Total Cost])", "definition": "Total cost of care."},
        {"name": "Total Reimbursement", "kind": "sum", "column": "Reimbursement", "format": "currency",
         "dax": "SUM(Encounters[Reimbursement])", "definition": "Total amount reimbursed by payers."},
        {"name": "Total Patients", "kind": "distinct", "column": "Patient ID", "format": "int",
         "dax": "DISTINCTCOUNT(Encounters[Patient ID])", "definition": "Distinct patients seen."},
        {"name": "Avg Length of Stay", "kind": "avg", "column": "Length of Stay", "format": "number",
         "dax": "AVERAGE(Encounters[Length of Stay])", "definition": "Average length of stay in days."},
        {"name": "Readmissions", "kind": "count_where", "where": ["Readmitted", "Yes"], "format": "int",
         "dax": "CALCULATE(COUNTROWS(Encounters), Encounters[Readmitted]=\"Yes\")",
         "definition": "Encounters flagged as a readmission."},
        {"name": "Readmission Rate %", "kind": "ratio_m", "numerator": "Readmissions",
         "denominator": "Total Encounters", "format": "percent",
         "dax": "DIVIDE([Readmissions], [Total Encounters])",
         "definition": "Readmissions as a share of all encounters."},
        {"name": "Avg Charge per Encounter", "kind": "ratio_m", "numerator": "Total Charges",
         "denominator": "Total Encounters", "format": "currency",
         "dax": "DIVIDE([Total Charges], [Total Encounters])",
         "definition": "Average charges per encounter."},
        {"name": "Net Margin", "kind": "sum", "column": "Reimbursement", "format": "currency",
         "dax": "SUM(Encounters[Reimbursement]) - SUM(Encounters[Total Cost])",
         "definition": "Reimbursement minus cost (approx.)."},
        {"name": "Charges YoY %", "kind": "derived", "base": "Total Charges",
         "time_intelligence": "yoy", "format": "percent",
         "dax": "Year-over-year growth of Total Charges.",
         "definition": "Year-over-year growth of Total Charges."},
        {"name": "Encounters YoY %", "kind": "derived", "base": "Total Encounters",
         "time_intelligence": "yoy", "format": "percent",
         "dax": "Year-over-year growth of Total Encounters.",
         "definition": "Year-over-year growth of encounter volume."},
    ],
    "dimensions": [
        {"name": "Department", "table": "Encounters", "column": "Department"},
        {"name": "Diagnosis", "table": "Encounters", "column": "Diagnosis"},
        {"name": "Encounter Type", "table": "Encounters", "column": "Encounter Type"},
        {"name": "Discharge Status", "table": "Encounters", "column": "Discharge Status"},
        {"name": "Readmitted", "table": "Encounters", "column": "Readmitted"},
        {"name": "Provider", "table": "Providers", "column": "Provider Name"},
        {"name": "Specialty", "table": "Providers", "column": "Specialty"},
        {"name": "Gender", "table": "Patients", "column": "Gender"},
        {"name": "Age Group", "table": "Patients", "column": "Age Group"},
        {"name": "City", "table": "Patients", "column": "City"},
        {"name": "State", "table": "Patients", "column": "State"},
        {"name": "Insurance", "table": "Patients", "column": "Insurance"},
        {"name": "Year", "table": "Encounters", "column": "Admit Date", "isTime": True, "grain": "year"},
        {"name": "Quarter", "table": "Encounters", "column": "Admit Date", "isTime": True, "grain": "quarter"},
        {"name": "Month", "table": "Encounters", "column": "Admit Date", "isTime": True, "grain": "month"},
    ],
    "synonyms": {
        "Total Charges": ["charges", "billing", "billed", "revenue", "sales", "charge amount"],
        "Total Reimbursement": ["reimbursement", "paid", "collected", "payments"],
        "Total Cost": ["cost", "costs", "cost of care"],
        "Total Encounters": ["encounters", "visits", "admissions", "cases", "volume"],
        "Total Patients": ["patients", "unique patients", "distinct patients"],
        "Avg Length of Stay": ["length of stay", "los", "average stay", "avg los"],
        "Readmission Rate %": ["readmission rate", "readmit rate", "readmissions rate"],
        "Readmissions": ["readmissions", "readmits"],
        "Avg Charge per Encounter": ["average charge", "charge per encounter", "avg charge"],
        "Department": ["department", "dept", "service line"],
        "Diagnosis": ["diagnosis", "condition", "dx", "diagnoses"],
        "Provider": ["provider", "doctor", "physician", "providers"],
        "Specialty": ["specialty", "speciality"],
        "Insurance": ["insurance", "payer", "plan"],
        "Gender": ["gender", "sex"],
        "City": ["city", "cities"],
        "State": ["state", "states"],
        "Age Group": ["age group", "age", "age band"],
        "Encounter Type": ["encounter type", "visit type", "type of visit"],
    },
}

with open(os.path.join(OUT, "semantic_model.json"), "w", encoding="utf-8") as fh:
    json.dump(model, fh, indent=2)

print(f"Wrote healthcare dataset to {OUT}")
print(f"  encounters={len(encounters)} patients={len(patients)} providers={len(providers)}")
print(f"  measures={len(model['measureSpecs'])} dimensions={len(model['dimensions'])}")
