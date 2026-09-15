#!/usr/bin/env bash

# Sync temporary GitHub Actions AWS credentials into the sandbox controller.
# Never enable shell tracing in this script: its inputs are secrets.
set -euo pipefail

: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_SESSION_TOKEN:?AWS_SESSION_TOKEN is required}"

namespace="kube-system"
secret_name="aws-load-balancer-controller-credentials"
deployment_name="aws-load-balancer-controller"

kubectl create secret generic "${secret_name}" \
  --namespace "${namespace}" \
  --from-literal=AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
  --from-literal=AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
  --from-literal=AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN}" \
  --dry-run=client \
  -o yaml | kubectl apply -f - >/dev/null

if kubectl get deployment "${deployment_name}" --namespace "${namespace}" >/dev/null 2>&1; then
  container_name="$(kubectl get deployment "${deployment_name}" \
    --namespace "${namespace}" \
    -o jsonpath="{.spec.template.spec.containers[0].name}")"

  if [[ -z "${container_name}" ]]; then
    echo "Controller deployment has no container name" >&2
    exit 1
  fi

  patch="{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"${container_name}\",\"env\":[{\"name\":\"AWS_ACCESS_KEY_ID\",\"valueFrom\":{\"secretKeyRef\":{\"name\":\"${secret_name}\",\"key\":\"AWS_ACCESS_KEY_ID\"}}},{\"name\":\"AWS_SECRET_ACCESS_KEY\",\"valueFrom\":{\"secretKeyRef\":{\"name\":\"${secret_name}\",\"key\":\"AWS_SECRET_ACCESS_KEY\"}}},{\"name\":\"AWS_SESSION_TOKEN\",\"valueFrom\":{\"secretKeyRef\":{\"name\":\"${secret_name}\",\"key\":\"AWS_SESSION_TOKEN\"}}}]}]}}}}"

  kubectl patch deployment "${deployment_name}" \
    --namespace "${namespace}" \
    --type strategic \
    --patch "${patch}" >/dev/null
  kubectl rollout restart deployment/"${deployment_name}" --namespace "${namespace}" >/dev/null
  kubectl rollout status deployment/"${deployment_name}" --namespace "${namespace}" --timeout=180s
fi
