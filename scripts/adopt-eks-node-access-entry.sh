#!/usr/bin/env bash
set -euo pipefail

: "${EKS_CLUSTER_NAME:?EKS_CLUSTER_NAME is required}"
: "${EXISTING_IAM_ROLE_ARN:?EXISTING_IAM_ROLE_ARN is required}"
: "${AWS_REGION:?AWS_REGION is required}"

resource_address="aws_eks_access_entry.nodes"
import_id="${EKS_CLUSTER_NAME}:${EXISTING_IAM_ROLE_ARN}"

if terraform -chdir=terraform state show "${resource_address}" >/dev/null 2>&1; then
  echo "EKS node access entry is already managed by Terraform"
  exit 0
fi

if ! aws eks describe-access-entry \
  --cluster-name "${EKS_CLUSTER_NAME}" \
  --principal-arn "${EXISTING_IAM_ROLE_ARN}" \
  --region "${AWS_REGION}" >/dev/null 2>&1; then
  echo "No existing EKS node access entry to adopt"
  exit 0
fi

terraform -chdir=terraform import \
  -var-file=../environments/sandbox/terraform.tfvars \
  "${resource_address}" \
  "${import_id}"

echo "Existing EKS node access entry adopted by Terraform"
