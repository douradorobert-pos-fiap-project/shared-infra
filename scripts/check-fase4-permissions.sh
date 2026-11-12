#!/usr/bin/env bash

# Read-only capability audit for the temporary AWS Academy Sandbox session.
# This script never creates, updates, or deletes AWS resources.
set -euo pipefail

for variable_name in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Missing required temporary credential: ${variable_name}" >&2
    exit 2
  fi
done

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required" >&2
  exit 2
fi

aws_region="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
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

run_probe sqs sqs list-queues --max-results 1 --output json
run_probe dynamodb dynamodb list-tables --limit 1 --output json
run_probe ecr ecr describe-repositories --max-results 1 --output json
run_probe eks eks list-clusters --max-results 1 --output json
