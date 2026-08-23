#!/usr/bin/env bash
# Deploy AgriSetu backend to Cloud Run.
#
# Prereqs (one-time):
#   gcloud auth login
#   gcloud config set project <YOUR_PROJECT_ID>
#   gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
#       artifactregistry.googleapis.com firestore.googleapis.com
#
# Secrets: this script passes GEMINI_API_KEY as a plain env var for
# hackathon speed. For anything beyond a hackathon, use
# `gcloud secrets create` + --set-secrets instead of --set-env-vars.
#
# Usage:
#   GEMINI_API_KEY=xxxx ./deploy.sh

set -euo pipefail

# Always deploy from the backend/ folder regardless of where this
# script is invoked from (repo root or backend/ itself) — Cloud Run
# builds from the Dockerfile's directory as the build context.
cd "$(dirname "${BASH_SOURCE[0]}")"

PROJECT_ID="${PROJECT_ID:-agrisetu-hackathon}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${SERVICE_NAME:-agrisetu-backend}"

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "ERROR: set GEMINI_API_KEY before running this script." >&2
  echo "  GEMINI_API_KEY=xxxx ./deploy.sh" >&2
  exit 1
fi

ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://agrisetu-frontend.web.app,http://localhost:5173}"

echo "Deploying ${SERVICE_NAME} to Cloud Run (project=${PROJECT_ID}, region=${REGION})..."

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY},GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.0-flash},FIREBASE_PROJECT_ID=${PROJECT_ID},ALLOWED_ORIGINS=${ALLOWED_ORIGINS},ENV=production" \
  --memory 512Mi \
  --timeout 60

echo ""
echo "Done. Grant the Cloud Run runtime service account Firestore access if you haven't:"
echo "  gcloud projects add-iam-policy-binding ${PROJECT_ID} \\"
echo "    --member=\"serviceAccount:\$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(spec.template.spec.serviceAccountName)')\" \\"
echo "    --role=\"roles/datastore.user\""
