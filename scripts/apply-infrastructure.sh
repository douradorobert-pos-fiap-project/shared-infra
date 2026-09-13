#!/usr/bin/env bash

# Applies the infrastructure in the required bootstrap order:
# EKS control plane/node group -> AWS Load Balancer Controller and remaining resources.
set -euo pipefail

repository_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
terraform_dir="${repository_dir}/terraform"
tfvars_file="${TFVARS_FILE:-${repository_dir}/environments/sandbox/terraform.tfvars}"
apply_options=("$@")

if [[ ! -f "${tfvars_file}" ]]; then
  echo "tfvars file not found: ${tfvars_file}" >&2
  echo "Set TFVARS_FILE to the desired .tfvars file and run again." >&2
  exit 1
fi

terraform -chdir="${terraform_dir}" init

echo "==> Phase 1/2: creating EKS and its node group"
terraform -chdir="${terraform_dir}" apply \
  -var-file="${tfvars_file}" \
  "${apply_options[@]}" \
  -target=aws_eks_cluster.main \
  -target=aws_eks_node_group.main

echo "==> Phase 2/2: applying remaining infrastructure (including AWS Load Balancer Controller)"
terraform -chdir="${terraform_dir}" apply \
  -var-file="${tfvars_file}" \
  "${apply_options[@]}"
