#!/usr/bin/env bash
# Convert backend/.env into az containerapp commands for secrets + env vars.
# Pipe output into Azure Cloud Shell (portal.azure.com → >_ icon → Bash).
#
# Usage:
#   bash scripts/gen-azure-env.sh > azure-commands.sh
#   # open Cloud Shell, paste the contents of azure-commands.sh
#
# Edit APP_NAME / RG if yours differ.

set -euo pipefail

ENV_FILE="${1:-backend/.env}"
APP_NAME="${APP_NAME:-deep-back}"
RG="${RG:-deepshiva-rg}"

# Source-key -> "secret-name:target-env-var" (secret-name "-" means plain env var)
# Keys not listed are skipped.
declare -A MAP=(
  [GROQ_API_KEY]="groq-api-key:GROQ_API_KEY"
  [GROQ_API_KEY2]="groq-api-key-2:GROQ_API_KEY2"
  [GOOGLE_CLIENT_ID]="google-client-id:GOOGLE_CLIENT_ID"
  [GOOGLE_CLIENT_SECRET]="google-client-secret:GOOGLE_CLIENT_SECRET"
  [MONGODB_URI]="mongodb-uri:MONGODB_URI"
  [QDRANT_HOST]="qdrant-host:QDRANT_HOST"
  [QDRANT_API_KEY]="qdrant-api-key:QDRANT_API_KEY"
  [LITEAPI_KEY]="liteapi-key:LITEAPI_KEY"
  [CALLEDRIFIC_API_KEY]="calendarific-key:CALLENDRIFIC_API_KEY"  # fixes .env typo
  [JWT_SECRET_KEY]="jwt-secret-key:JWT_SECRET_KEY"
  [ADMIN_EMAILS]="-:ADMIN_EMAILS"
  [QDRANT_DIM]="-:QDRANT_DIM"
)

# Always added (not from .env)
PLAIN_EXTRA=(
  "ENV=production"
  "ALLOWED_ORIGINS=https://deep-shiva-tourism.vercel.app,http://localhost:5173"
)

declare -A EV
while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  key="${line%%=*}"
  val="${line#*=}"
  key="${key// /}"
  val="${val%$'\r'}"
  EV[$key]="$val"
done < "$ENV_FILE"

SECRETS=()
ENVS=()

for k in "${!MAP[@]}"; do
  [[ -z "${EV[$k]:-}" ]] && continue
  m="${MAP[$k]}"
  sn="${m%%:*}"
  en="${m##*:}"
  v="${EV[$k]}"
  if [[ "$sn" == "-" ]]; then
    ENVS+=("$en=$v")
  else
    SECRETS+=("$sn=$v")
    ENVS+=("$en=secretref:$sn")
  fi
done

for kv in "${PLAIN_EXTRA[@]}"; do
  ENVS+=("$kv")
done

echo "#!/usr/bin/env bash"
echo "# Generated from $ENV_FILE — run in Azure Cloud Shell."
echo "set -e"
echo
echo "APP=$APP_NAME"
echo "RG=$RG"
echo
echo "# 1) Set secrets"
echo "az containerapp secret set \\"
echo "  -n \"\$APP\" -g \"\$RG\" \\"
echo "  --secrets \\"
for i in "${!SECRETS[@]}"; do
  sep=" \\"
  [[ $i -eq $((${#SECRETS[@]}-1)) ]] && sep=""
  printf "    %q%s\n" "${SECRETS[$i]}" "$sep"
done
echo
echo "# 2) Set env vars (references the secrets above)"
echo "az containerapp update \\"
echo "  -n \"\$APP\" -g \"\$RG\" \\"
echo "  --set-env-vars \\"
for i in "${!ENVS[@]}"; do
  sep=" \\"
  [[ $i -eq $((${#ENVS[@]}-1)) ]] && sep=""
  printf "    %q%s\n" "${ENVS[$i]}" "$sep"
done
echo
echo
echo "# 3) Strip the startup probe (killed past revisions after ~6s on wrong port)"
echo "az containerapp update \\"
echo "  -n \"\$APP\" -g \"\$RG\" \\"
echo "  --set properties.template.containers[0].probes=[]"
echo
echo "echo '✅ Secrets, env vars, and probe config applied. A new revision will roll automatically.'"
echo "echo"
echo "FQDN=\$(az containerapp show -n \"\$APP\" -g \"\$RG\" --query 'properties.configuration.ingress.fqdn' -o tsv)"
echo "echo \"Waiting ~60s for new revision to start, then testing /health...\""
echo "sleep 60"
echo "curl -sf \"https://\$FQDN/health\" && echo '' && echo '🎉 Backend is live at https://'\$FQDN || echo '❌ Health check failed — run: az containerapp logs show -n '\$APP' -g '\$RG' --tail 50'"
