// ---------------------------------------------------------------------------
// Power BI AI Chatbot — core Azure infrastructure (Phase 1).
//
// Provisions: App Service (backend) + plan, Static Web App (frontend),
// Azure OpenAI, Key Vault, Application Insights + Log Analytics.
// The backend uses a system-assigned managed identity and is granted access
// to Key Vault and Azure OpenAI so no keys need to live in app settings.
//
// Front Door / custom domain / WAF are provisioned separately for production
// (see infra/README.md).
// ---------------------------------------------------------------------------

@description('Base name for all resources.')
param namePrefix string = 'pbichat'

@description('Deployment environment: dev | test | prod.')
@allowed(['dev', 'test', 'prod'])
param environmentName string = 'dev'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Approved Azure OpenAI model deployment name.')
param openAiDeploymentName string = 'gpt-4o'

@description('Approved Azure OpenAI model + version.')
param openAiModelName string = 'gpt-4o'
param openAiModelVersion string = '2024-08-06'

@description('Allowed frontend origin(s) for CORS.')
param allowedOrigins string = 'https://${namePrefix}-${environmentName}-web.azurestaticapps.net'

var suffix = '${namePrefix}-${environmentName}'
var appServicePlanSku = environmentName == 'prod' ? 'P1v3' : 'B1'

// --- Monitoring --------------------------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${suffix}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${suffix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// --- Key Vault (RBAC) --------------------------------------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${take(replace(suffix, '-', ''), 20)}'
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
  }
}

// --- Azure OpenAI ------------------------------------------------------------
resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'oai-${suffix}'
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: 'oai-${suffix}'
    publicNetworkAccess: 'Enabled'
  }
}

resource openAiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: openAiDeploymentName
  sku: { name: 'Standard', capacity: 20 }
  properties: {
    model: { format: 'OpenAI', name: openAiModelName, version: openAiModelVersion }
  }
}

// --- Backend App Service -----------------------------------------------------
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'plan-${suffix}'
  location: location
  sku: { name: appServicePlanSku }
  properties: { reserved: true } // Linux
}

resource backend 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-${suffix}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'NODE|20-lts'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      cors: { allowedOrigins: split(allowedOrigins, ',') }
      appSettings: [
        { name: 'NODE_ENV', value: environmentName == 'prod' ? 'production' : environmentName }
        { name: 'MOCK_MODE', value: 'false' }
        { name: 'ALLOWED_ORIGINS', value: allowedOrigins }
        { name: 'AZURE_OPENAI_ENDPOINT', value: openAi.properties.endpoint }
        { name: 'AZURE_OPENAI_DEPLOYMENT_NAME', value: openAiDeploymentName }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
        { name: 'KEY_VAULT_URI', value: keyVault.properties.vaultUri }
      ]
    }
  }
}

// --- Frontend Static Web App -------------------------------------------------
resource staticWeb 'Microsoft.Web/staticSites@2023-12-01' = {
  name: 'stapp-${suffix}'
  location: location
  sku: { name: 'Standard', tier: 'Standard' }
  properties: {}
}

// --- Role assignments (managed identity, least privilege) --------------------
// Backend -> Key Vault Secrets User
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
resource kvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, backend.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: backend.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Backend -> Cognitive Services OpenAI User
var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
resource openAiRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, backend.id, openAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: backend.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output backendUrl string = 'https://${backend.properties.defaultHostName}'
output backendName string = backend.name
output staticWebName string = staticWeb.name
output openAiEndpoint string = openAi.properties.endpoint
output keyVaultUri string = keyVault.properties.vaultUri
output appInsightsConnectionString string = appInsights.properties.ConnectionString
