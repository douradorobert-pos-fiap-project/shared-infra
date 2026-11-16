#!/usr/bin/env bash
set -euo pipefail

: "${EKS_CLUSTER_NAME:?EKS_CLUSTER_NAME is required}"
: "${EXISTING_IAM_ROLE_ARN:?EXISTING_IAM_ROLE_ARN is required}"
: "${AWS_REGION:?AWS_REGION is required}"

resource_address="aws_eks_access_entry.nodes"
import_id="${EKS_CLUSTER_NAME}:${EXISTING_IAM_ROLE_ARN}"
state_managed=false

if terraform -chdir=terraform state show "${resource_address}" >/dev/null 2>&1; then
  state_managed=true
fi

set +e
entry_type_output="$(aws eks describe-access-entry \
  --cluster-name "${EKS_CLUSTER_NAME}" \
  --principal-arn "${EXISTING_IAM_ROLE_ARN}" \
  --region "${AWS_REGION}" \
  --query 'accessEntry.type' \
  --output text 2>&1)"
describe_status=$?
set -e

if ((describe_status != 0)); then
  if [[ "${entry_type_output}" == *"ResourceNotFoundException"* ]]; then
    if [[ "${state_managed}" == true ]]; then
      terraform -chdir=terraform state rm "${resource_address}"
      echo "Removed stale EKS node access entry from Terraform state"
    fi
    echo "No existing EKS node access entry to adopt"
    exit 0
  fi

  echo "${entry_type_output}" >&2
  exit "${describe_status}"
fi

entry_type="${entry_type_output}"

if [[ "${state_managed}" == false ]]; then
  terraform -chdir=terraform import \
    -var-file=../environments/sandbox/terraform.tfvars \
    "${resource_address}" \
    "${import_id}"

  echo "Existing EKS node access entry adopted by Terraform"
else
  echo "EKS node access entry is already managed by Terraform"
fi

if [[ "${entry_type}" == "EC2" ]]; then
  echo "EKS node access entry already supports instance ID node names"
  exit 0
fi

if [[ "${entry_type}" != "EC2_LINUX" ]]; then
  echo "Unsupported EKS node access entry type: ${entry_type}" >&2
  exit 1
fi

echo "Replacing incompatible EC2_LINUX access entry and empty managed node group"

terraform -chdir=terraform apply \
  -auto-approve \
  -var-file=../environments/sandbox/terraform.tfvars \
  -target=aws_eks_access_entry.nodes \
  -target=aws_eks_node_group.main \
  -replace=aws_eks_access_entry.nodes \
  -replace=aws_eks_node_group.main
