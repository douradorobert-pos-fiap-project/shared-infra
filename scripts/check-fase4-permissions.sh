#!/usr/bin/env bash

# Read-only capability audit for the temporary AWS Academy Sandbox session.
# This script never creates, updates, or deletes AWS resources.
set -euo pipefail

for variable_name in \
  AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN \
  AWS_REGION TF_STATE_BUCKET EXISTING_IAM_ROLE_ARN LAMBDA_CPF_VALIDATOR_NAME; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Missing required temporary credential: ${variable_name}" >&2
    exit 2
  fi
done

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required" >&2
  exit 2
fi

aws_region="${AWS_REGION}"
probe_output="$(mktemp)"
trap 'rm -f "${probe_output}"' EXIT

run_probe() {
  local capability="$1"
  shift

  if AWS_PAGER="" aws --no-cli-pager --region "${aws_region}" "$@" >"${probe_output}" 2>&1; then
    printf '%s\tALLOWED\n' "${capability}"
  else
    printf '%s\tDENIED_OR_UNAVAILABLE\n' "${capability}"
  fi
}

printf 'AWS_PERMISSION_CHECK_V1\n'
printf 'region\t%s\n' "${aws_region}"

if account_id="$(AWS_PAGER="" aws --no-cli-pager --region "${aws_region}" \
  sts get-caller-identity --query Account --output text 2>"${probe_output}")"; then
  printf 'identity\tALLOWED\taccount=%s\n' "${account_id}"
else
  printf 'identity\tDENIED_OR_UNAVAILABLE\n'
  exit 3
fi

if [[ ! "${EXISTING_IAM_ROLE_ARN}" =~ ^arn:aws[a-zA-Z-]*:iam::([0-9]{12}):role/(.+)$ ]]; then
  printf 'role\tDENIED_OR_UNAVAILABLE\treason=invalid-arn\n'
  exit 4
fi

configured_account_id="${BASH_REMATCH[1]}"
role_name="${BASH_REMATCH[2]##*/}"
if [[ "${configured_account_id}" != "${account_id}" ]]; then
  printf 'role\tDENIED_OR_UNAVAILABLE\treason=account-mismatch\n'
  exit 4
fi

if ! actual_role_arn="$(AWS_PAGER="" aws --no-cli-pager --region "${aws_region}" \
  iam get-role --role-name "${role_name}" --query Role.Arn --output text 2>"${probe_output}")" || \
  [[ "${actual_role_arn}" != "${EXISTING_IAM_ROLE_ARN}" ]]; then
  printf 'role\tDENIED_OR_UNAVAILABLE\n'
  exit 4
fi
printf 'role\tALLOWED\n'

if AWS_PAGER="" aws --no-cli-pager --region "${aws_region}" \
  s3api head-bucket --bucket "${TF_STATE_BUCKET}" >"${probe_output}" 2>&1; then
  printf 'state_bucket\tALLOWED\n'
else
  printf 'state_bucket\tDENIED_OR_UNAVAILABLE\n'
  exit 5
fi

if AWS_PAGER="" aws --no-cli-pager --region "${aws_region}" \
  lambda get-function --function-name "${LAMBDA_CPF_VALIDATOR_NAME}" \
  >"${probe_output}" 2>&1; then
  printf 'cpf_lambda\tALLOWED\n'
else
  printf 'cpf_lambda\tDENIED_OR_UNAVAILABLE\n'
  exit 6
fi

run_probe sqs sqs list-queues --max-results 1 --output json
run_probe dynamodb dynamodb list-tables --limit 1 --output json
run_probe ecr ecr describe-repositories --max-results 1 --output json
run_probe eks eks list-clusters --max-results 1 --output json
