# Infrastructure

Infrastructure-as-code for the Power BI AI Chatbot, matching **Phase 1 –
Create the Azure Resources** of the implementation guide.

## What `bicep/main.bicep` provisions

| Resource | Purpose |
| --- | --- |
| Log Analytics + Application Insights | Telemetry, exceptions, performance, traces |
| Key Vault (RBAC, purge protection) | Secrets/certificates that can't use managed identity |
| Azure OpenAI + model deployment | LLM for intent/plan generation |
| App Service Plan + App Service (Linux, Node 20) | Backend API, system-assigned managed identity |
| Static Web App | Frontend hosting + CI deploy |
| Role assignments | Backend MI → *Key Vault Secrets User* and *Cognitive Services OpenAI User* |

The backend is provisioned with **managed identity** and RBAC grants, so it can
reach Azure OpenAI and Key Vault **without any keys in app settings** (Phase 11 /
Phase 12). `httpsOnly`, `minTlsVersion 1.2`, and `ftpsState: Disabled` enforce
the transport-security requirements.

## Deploy (dev)

```bash
az group create -n rg-pbichat-dev -l eastus

az deployment group create \
  -g rg-pbichat-dev \
  -f bicep/main.bicep \
  -p namePrefix=pbichat environmentName=dev \
     allowedOrigins=https://<your-static-web>.azurestaticapps.net
```

Repeat with `environmentName=test` / `prod` (separate resource groups) to keep
DEV/TEST/PROD isolated (Phase 12). `prod` selects a `P1v3` plan SKU.

## Not created here (production hardening)

These are provisioned/configured separately to keep the core template portable:

- **Azure Front Door + WAF + custom domain + TLS** — production entry point,
  routing and caching (Phase 1 step 7 / §24).
- **Private networking / VNet integration and private endpoints** for Key Vault
  and Azure OpenAI, if your policy requires no public network access.
- **Entra ID app registrations** (frontend SPA + backend API) — see
  `docs/SECURITY.md`; these are identity config, not resources in this template.
- **Power BI workspace/dataset permissions** — grant the backend identity (or
  the delegated flow) least-privilege access to the semantic model.

## Terraform

An equivalent Terraform module can live alongside `bicep/` under
`infra/terraform/` if that is your organization's standard; the resource set and
role assignments are identical.
