# Deploying DeepShiva Backend to Azure Container Apps

The backend runs as a single container on **Azure Container Apps** (consumption plan, scale-to-zero) in **Southeast Asia**. The frontend stays on Vercel and points at the Container Apps URL via `VITE_API_BASE_URL`.

## Prerequisites

- Azure account (Student credit works)
- Azure CLI installed: `winget install Microsoft.AzureCLI`
- GitHub account with this repo pushed
- MongoDB Atlas cluster (free M0)
- Qdrant Cloud cluster (free tier)
- Groq API key, Google OAuth client ID/secret

## 1. One-time Azure setup

```bash
# Login
az login

# Pick your subscription
az account set --subscription "<your-subscription-id>"

# Create resource group in Southeast Asia
az group create --name deepshiva-rg --location southeastasia

# Register providers (first time only)
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

# Create Container Apps environment (this also provisions Log Analytics)
az containerapp env create \
  --name deepshiva-env \
  --resource-group deepshiva-rg \
  --location southeastasia
```

## 2. Build & push the image (first time, manually)

After this one push, GitHub Actions takes over on every commit to `master`.

```bash
# From repo root, build locally and push to GHCR
docker build -t ghcr.io/<github-user>/deepshiva-tourism-backend:latest ./backend

# Login to GHCR with a PAT that has write:packages scope
echo $GHCR_PAT | docker login ghcr.io -u <github-user> --password-stdin

docker push ghcr.io/<github-user>/deepshiva-tourism-backend:latest
```

Make the package public in GitHub → Packages → settings, or configure Container Apps with a pull secret (see below).

## 3. Create the Container App

```bash
az containerapp create \
  --name deep-back \
  --resource-group deepshiva-rg \
  --environment deepshiva-env \
  --image ghcr.io/<github-user>/deepshiva-tourism-backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 1 \
  --memory 2Gi \
  --secrets \
      groq-api-key=<GROQ_API_KEY> \
      google-client-id=<GOOGLE_CLIENT_ID> \
      google-client-secret=<GOOGLE_CLIENT_SECRET> \
      mongodb-uri=<MONGODB_URI> \
      qdrant-host=<QDRANT_HOST> \
      qdrant-api-key=<QDRANT_API_KEY> \
      jwt-secret-key=<64-char-random-string> \
      liteapi-key=<LITEAPI_KEY> \
      calendarific-key=<CALENDARIFIC_API_KEY> \
  --env-vars \
      ENV=production \
      GROQ_API_KEY=secretref:groq-api-key \
      GOOGLE_CLIENT_ID=secretref:google-client-id \
      GOOGLE_CLIENT_SECRET=secretref:google-client-secret \
      MONGODB_URI=secretref:mongodb-uri \
      QDRANT_HOST=secretref:qdrant-host \
      QDRANT_API_KEY=secretref:qdrant-api-key \
      JWT_SECRET_KEY=secretref:jwt-secret-key \
      LITEAPI_KEY=secretref:liteapi-key \
      CALLENDRIFIC_API_KEY=secretref:calendarific-key \
      ALLOWED_ORIGINS=https://deep-shiva-tourism.vercel.app,http://localhost:5173 \
      ADMIN_EMAILS=yash@voicehelden.com
```

Note the FQDN returned, e.g. `deep-back.<hash>.southeastasia.azurecontainerapps.io`.

## 4. Point the Vercel frontend at it

In Vercel → project → Settings → Environment Variables:

```
VITE_API_BASE_URL = https://deep-back.<hash>.southeastasia.azurecontainerapps.io/api
```

Redeploy the Vercel project.

## 5. Hook up GitHub Actions auto-deploy

Create an Azure service principal and add it as a GitHub secret so CI can push updates:

```bash
az ad sp create-for-rbac \
  --name deepshiva-gh-deploy \
  --role contributor \
  --scopes /subscriptions/<sub-id>/resourceGroups/deepshiva-rg \
  --sdk-auth
```

Copy the JSON output. In GitHub → repo → Settings → Secrets and variables → Actions, add:

| Secret | Value |
|---|---|
| `AZURE_CREDENTIALS` | the JSON blob from the command above |
| `AZURE_RESOURCE_GROUP` | `deepshiva-rg` |
| `AZURE_CONTAINER_APP` | `deep-back` |

From now on every push to `master` that touches `backend/` rebuilds and rolls the Container App.

## 6. Private GHCR image (optional)

If you prefer to keep the image private:

```bash
az containerapp registry set \
  --name deep-back \
  --resource-group deepshiva-rg \
  --server ghcr.io \
  --username <github-user> \
  --password <ghcr-pat-with-read:packages>
```

## 7. Smoke test

```bash
curl https://<fqdn>/health
# expect JSON with status: healthy

curl https://<fqdn>/
# expect service banner JSON
```

Then open `https://deep-shiva-tourism.vercel.app` and sign in.

## Costs

- Container Apps consumption: free tier covers ~180k vCPU-sec + 360k GiB-sec/month → effectively $0 for demo traffic at min-replicas=0.
- Logs: Log Analytics has a 5 GB/month free ingestion.
- GHCR: free for public images, unlimited pulls from Azure.
- Student credit ($100) is plenty of runway.

## Rotating secrets

```bash
az containerapp secret set \
  --name deep-back \
  --resource-group deepshiva-rg \
  --secrets groq-api-key=<new-value>

az containerapp update \
  --name deep-back \
  --resource-group deepshiva-rg
```

## Teardown

```bash
az group delete --name deepshiva-rg --yes --no-wait
```
