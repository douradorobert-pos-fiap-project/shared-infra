# Recreate EKS Node Access Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recreate the empty sandbox worker pool with an `EC2` access entry so AL2023 nodes can join without `ec2:DescribeInstances`.

**Architecture:** The deployment script detects the incompatible EKS-managed `EC2_LINUX` entry. It uses one targeted Terraform apply with explicit replacements for the imported access entry and node group, preserving dependency order and excluding unrelated resources. Fresh sandboxes and already-migrated environments remain non-destructive.

**Tech Stack:** Bash, Terraform 1.15.8, AWS provider 5.100.0, AWS CLI, Amazon EKS, GitHub Actions.

**Spec:** `/home/robertd/repositorios/architecture-docs/fase-4/requirements_fase_4.md`

## Global Constraints

- Reuse the AWS Academy `LabRole`; do not create IAM resources.
- Keep the Terraform S3 state consistent; do not delete AWS resources outside Terraform.
- Only recreate the node group when the access entry type is incompatible.
- Do not destroy the EKS cluster, VPC, databases, or application data.
- Keep the workflow idempotent for sandbox resets and repeated executions.

## Review Focus

- Existing `EC2_LINUX` entry: replace only the node group and imported entry in one targeted apply.
- Existing `EC2` entry: do not destroy or recreate resources.
- No access entry in a fresh sandbox: skip migration and let Terraform create it.
- AWS lookup failure other than not-found: fail instead of silently continuing.
- Terraform state ownership: require the existing entry to be imported before targeted destruction.

---

### Task 1: Add the destructive migration guard

**Files:**
- Modify: `scripts/adopt-eks-node-access-entry.sh`
- Modify: `terraform/eks.tf`
- Test: `tests/test_fase4_static.py`

**Interfaces:**
- Consumes: `EKS_CLUSTER_NAME`, `EXISTING_IAM_ROLE_ARN`, `AWS_REGION`, remote Terraform state.
- Produces: either no migration, or removal from AWS and state of only `aws_eks_node_group.main` and `aws_eks_access_entry.nodes`.

- [ ] **Step 1: Write the failing regression test**

Assert that the script detects `EC2_LINUX`, replaces only the node group and access entry, and no longer attempts `destroy` or `update-access-entry`.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python3 -m unittest tests.test_fase4_static.TestPhase4SharedInfrastructure.test_eks_nodes_bootstrap_without_describe_instances_permission -v`

- [ ] **Step 3: Implement the minimal migration**

Query the access entry type. For `EC2_LINUX`, run one targeted Terraform apply with `-replace` for both resources. For `EC2` or a missing entry, exit without replacement. Remove obsolete username lifecycle handling.

- [ ] **Step 4: Run focused and full verification**

Run the focused test, all 75 tests, `bash -n`, `terraform fmt -check`, `terraform validate`, and `git diff --check`.

- [ ] **Step 5: Commit**

Commit message: `fix: recreate incompatible eks node access entry`

### Task 2: Execute the authorized migration and validate workers

**Files:**
- No source changes expected.

**Interfaces:**
- Consumes: Actions Variables read with `gh`, local temporary AWS credentials, remote S3 state.
- Produces: `EC2` access entry, recreated managed node group, and Ready Kubernetes nodes.

- [ ] **Step 1: Initialize the remote backend with Actions Variables**

Read non-secret variables with `gh variable list --env sandbox`; use local AWS credentials and a placeholder New Relic value for targeted Terraform commands.

- [ ] **Step 2: Run the migration script**

Confirm the plan targets only the node group and node access entry before approving targeted destruction.

- [ ] **Step 3: Recreate the entry and node group**

Run the targeted Terraform apply for `aws_eks_access_entry.nodes` and `aws_eks_node_group.main`.

- [ ] **Step 4: Validate runtime state**

Require the access entry type to be `EC2`, the node group to be `ACTIVE`, and at least one Kubernetes node to become `Ready`.

- [ ] **Step 5: Integrate the automation**

Push the feature branch, open a PR, wait for checks, merge without bypass, then rerun the full Infrastructure workflow and report its final status.
