# MLOps on Databricks (AWS) — End-to-End Implementation Guide

---

## Overview

This guide walks through designing and implementing a production-grade MLOps solution on Databricks running on AWS. It covers ML pipelines, MLflow tracking, Model Registry, and automated deployment workflows.

**Stack:** Databricks (AWS) · MLflow · Delta Lake · AWS S3 · Databricks Workflows · Python

---

## Phase 1 — Infrastructure Setup (Days 1–2)

### 1.1 Databricks Workspace on AWS

```
AWS Console → Databricks → Create Workspace
  Region        : us-east-1 (or preferred)
  Storage       : S3 bucket  s3://your-company-mlops/
  IAM Role      : DatabricksRole (attach AmazonS3FullAccess + EC2 policies)
```

**Cluster Configuration (create two clusters):**

| Cluster | Purpose | Node Type | Min/Max Workers |
|---------|---------|-----------|-----------------|
| `ml-training-cluster` | Model training | `i3.xlarge` | 2 / 8 |
| `ml-serving-cluster` | Inference / serving | `m5.large` | 1 / 4 |

Enable **autoscaling** and **auto-termination (30 min)** on both.

### 1.2 Configure MLflow Tracking Server

Databricks includes a managed MLflow server — enable it:

```python
# In any Databricks notebook
import mlflow
mlflow.set_tracking_uri("databricks")          # points to managed MLflow
mlflow.set_experiment("/mlops/experiments/v1") # creates experiment in UI
```

Set S3 as the artifact store in `mlflow.properties` (cluster init script):

```bash
MLFLOW_ARTIFACT_ROOT=s3://your-company-mlops/mlflow-artifacts/
```

---

## Phase 2 — ML Pipeline Build (Days 3–7)

### 2.1 Project Folder Structure

```
/Repos/mlops-project/
  ├── notebooks/
  │   ├── 01_data_ingestion.py
  │   ├── 02_feature_engineering.py
  │   ├── 03_model_training.py
  │   ├── 04_model_evaluation.py
  │   └── 05_model_registration.py
  ├── src/
  │   ├── features.py
  │   ├── train.py
  │   └── monitor.py
  └── configs/
      └── pipeline_config.yml
```

### 2.2 Step-by-Step Pipeline Notebooks

**Notebook 01 — Data Ingestion**
```python
# Read raw data from S3 into Delta Lake
df = spark.read.format("csv").option("header", True)\
          .load("s3://your-company-mlops/raw-data/")
df.write.format("delta").mode("overwrite")\
  .save("/mnt/delta/bronze/raw_data")
```

**Notebook 02 — Feature Engineering**
```python
from pyspark.sql.functions import col, when
df = spark.read.format("delta").load("/mnt/delta/bronze/raw_data")
df_features = df.withColumn("feature_scaled", col("value") / 100)\
                .dropna()
df_features.write.format("delta").mode("overwrite")\
           .save("/mnt/delta/silver/features")
```

**Notebook 03 — Model Training with MLflow**
```python
import mlflow, mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

mlflow.set_experiment("/mlops/experiments/v1")

with mlflow.start_run(run_name="rf_training_run") as run:
    # Log parameters
    params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
    mlflow.log_params(params)

    # Train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    # Log metrics
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("f1_score", f1)

    # Log model artifact
    mlflow.sklearn.log_model(model, artifact_path="model",
                             registered_model_name="fraud-detection-model")
    print(f"Run ID: {run.info.run_id} | Accuracy: {accuracy:.4f}")
```

**Notebook 04 — Model Evaluation & Promotion**
```python
from mlflow.tracking import MlflowClient
client = MlflowClient()

# Get latest model version
latest = client.get_latest_versions("fraud-detection-model", stages=["None"])
version = latest[0].version

# Promote to Staging if accuracy > threshold
run = client.get_run(latest[0].run_id)
if float(run.data.metrics["accuracy"]) > 0.90:
    client.transition_model_version_stage(
        name="fraud-detection-model",
        version=version,
        stage="Staging"
    )
    print(f"Model v{version} promoted to Staging")
```

---

## Phase 3 — Model Registry & Deployment (Days 8–10)

### 3.1 Model Registry Workflow

```
None → Staging → Production → Archived
         ↑            ↑
   (auto via CI)  (manual approval or automated gate)
```

**Promote to Production:**
```python
client.transition_model_version_stage(
    name="fraud-detection-model",
    version=version,
    stage="Production",
    archive_existing_versions=True   # auto-archives old production version
)
```

### 3.2 Real-Time Serving (Databricks Model Serving)

```python
# Enable serving endpoint via Databricks REST API
import requests, json

token = dbutils.secrets.get(scope="mlops", key="databricks-token")
host  = "https://<your-workspace>.azuredatabricks.net"

payload = {
    "name": "fraud-detection-endpoint",
    "config": {
        "served_models": [{
            "model_name": "fraud-detection-model",
            "model_version": version,
            "workload_size": "Small",
            "scale_to_zero_enabled": True
        }]
    }
}
requests.post(f"{host}/api/2.0/serving-endpoints",
              headers={"Authorization": f"Bearer {token}"},
              json=payload)
```

**Invoke the endpoint:**
```python
response = requests.post(
    f"{host}/serving-endpoints/fraud-detection-endpoint/invocations",
    headers={"Authorization": f"Bearer {token}"},
    json={"dataframe_records": [{"feature1": 1.2, "feature2": 0.8}]}
)
print(response.json())
```

---

## Phase 4 — Automated Workflows & Monitoring (Days 11–14)

### 4.1 Databricks Workflow (Scheduled Pipeline)

In the Databricks UI: **Workflows → Create Job**

```
Job Name: mlops-daily-pipeline
Schedule: 0 2 * * *   (daily at 2 AM UTC)

Tasks (in order):
  Task 1: data_ingestion       → notebook: /notebooks/01_data_ingestion
  Task 2: feature_engineering  → notebook: /notebooks/02_feature_engineering  (depends on Task 1)
  Task 3: model_training       → notebook: /notebooks/03_model_training       (depends on Task 2)
  Task 4: model_evaluation     → notebook: /notebooks/04_model_evaluation     (depends on Task 3)

Notifications: email on failure → team@company.com
Cluster: ml-training-cluster
```

### 4.2 Model Drift Monitoring

```python
# monitor.py — run as a weekly Workflow task
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

reference = spark.read.format("delta").load("/mnt/delta/silver/features")\
                 .toPandas()
current   = spark.read.format("delta").load("/mnt/delta/gold/new_data")\
                 .toPandas()

report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=reference, current_data=current)

drift_detected = report.as_dict()["metrics"][0]["result"]["dataset_drift"]
if drift_detected:
    mlflow.log_metric("drift_detected", 1)
    # Trigger retraining via Databricks Jobs REST API
    requests.post(f"{host}/api/2.1/jobs/run-now",
                  headers={"Authorization": f"Bearer {token}"},
                  json={"job_id": YOUR_TRAINING_JOB_ID})
```

---

## Phase 5 — CI/CD Integration (Optional, Days 15–16)

```
GitHub Push → GitHub Actions → Run Tests → Databricks Repos Sync → Trigger Job

# .github/workflows/mlops_cicd.yml (key steps)
- name: Sync to Databricks Repos
  run: |
    curl -X POST https://<workspace>/api/2.0/repos/<repo-id>/update \
      -H "Authorization: Bearer $DATABRICKS_TOKEN" \
      -d '{"branch": "main"}'

- name: Trigger Training Pipeline
  run: |
    curl -X POST https://<workspace>/api/2.1/jobs/run-now \
      -H "Authorization: Bearer $DATABRICKS_TOKEN" \
      -d '{"job_id": YOUR_JOB_ID}'
```

---

## Quick Reference Checklist

| Phase | Task | Done |
|-------|------|------|
| 1 | Databricks workspace + S3 bucket created | ☐ |
| 1 | IAM roles configured | ☐ |
| 2 | Delta Lake tables created (bronze/silver/gold) | ☐ |
| 2 | MLflow experiment tracking working | ☐ |
| 3 | Model registered in Model Registry | ☐ |
| 3 | Serving endpoint live | ☐ |
| 4 | Automated Workflow job scheduled | ☐ |
| 4 | Drift monitoring notebook added | ☐ |
| 5 | CI/CD pipeline connected (optional) | ☐ |

---

## Key Concepts Summary

- **Delta Lake** — versioned, ACID-compliant data storage on S3 (bronze → silver → gold layers)
- **MLflow Tracking** — logs parameters, metrics, and artifacts for every run
- **Model Registry** — central store for model versions with stage gates (Staging → Production)
- **Databricks Workflows** — DAG-based job scheduler for automating the full pipeline
- **Model Serving** — REST endpoint auto-scaling to zero when idle (cost efficient)
- **Drift Monitoring** — Evidently library detects statistical shifts and triggers retraining

---

*Total implementation time: ~2–3 weeks for a production-ready setup*
