#!/usr/bin/env bash

# Plans the next safe infrastructure phase. EKS must exist before the AWS
# Load Balancer Controller can be installed via Helm.
set -euo pipefail

repository_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
terraform_dir="${repository_dir}/terraform"
tfvars_file="${TFVARS_FILE:-${repository_dir}/environments/sandbox/terraform.tfvars}"
plan_options=("$@")

if [[ ! -f "${tfvars_file}" ]]; then
  echo "tfvars file not found: ${tfvars_file}" >&2
  echo "Set TFVARS_FILE to the desired .tfvars file and run again." >&2
  exit 1
fi

terraform -chdir="${terraform_dir}" init

if ! terraform -chdir="${terraform_dir}" state show aws_eks_cluster.main >/dev/null 2>&1; then
  echo "==> Planning phase 1/2: EKS and its node group"
  terraform -chdir="${terraform_dir}" plan \
    -var-file="${tfvars_file}" \
    "${plan_options[@]}" \
    -target=aws_eks_cluster.main \
    -target=aws_eks_node_group.main
else
  echo "==> Planning remaining infrastructure (including AWS Load Balancer Controller)"
  terraform -chdir="${terraform_dir}" plan \
    -var-file="${tfvars_file}" \
    "${plan_options[@]}"
fi
