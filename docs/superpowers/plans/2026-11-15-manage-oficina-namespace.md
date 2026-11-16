# Manage Oficina Namespace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the shared `oficina` Kubernetes namespace reproducible through `shared-infra` Terraform.

**Architecture:** Add the Kubernetes provider with the same EKS exec authentication used by Helm and manage exactly one shared namespace. Keep all application workloads in their service repositories. Apply the namespace in a dedicated post-kubeconfig Terraform phase so later Helm failures cannot prevent this prerequisite from being created.

**Tech Stack:** Terraform, Kubernetes provider, EKS, GitHub Actions, Python unittest

**Spec:** Approved ownership decision in the 2026-11-15 conversation.

## Global Constraints

- Only `shared-infra` owns the shared `oficina` namespace.
- Microservice Deployments, Services, Secrets, ConfigMaps, HPAs and Jobs remain outside this repository.
- Namespace creation must occur after EKS/node provisioning and before Helm releases.
- No manual import is needed because the namespace is currently absent.
- Work occurs only on `feature/fase-4-infrastructure`; no AWS deployment is executed by this change.

## Review Focus

- Provider authentication must use the configured cluster name and region.
- Namespace must depend on EKS node availability.
- Workflow ordering must guarantee namespace creation before the full Helm apply.
- Existing tests prohibiting application workloads must remain effective.
- Documentation must reflect the Phase 4 ownership change.

---

### Task 1: Provision the Shared Namespace

**Files:**
- Modify: `terraform/main.tf`
- Modify: `terraform/providers.tf`
- Create: `terraform/namespace.tf`
- Modify: `.github/workflows/terraform.yml`
- Modify: `tests/test_terraform_static.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `aws_eks_cluster.main`, `aws_eks_node_group.main`, `var.aws_region`.
- Produces: Kubernetes namespace `oficina` for database bootstrap and all microservices.

- [ ] **Step 1: Replace historical namespace prohibition with ownership tests**

Assert the Kubernetes provider declaration/configuration, the single `kubernetes_namespace_v1.oficina` resource, its node-group dependency, and workflow ordering before the full apply. Retain negative tests for every application workload type.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_terraform_static -v`
Expected: failures for missing provider, namespace and workflow phase.

- [ ] **Step 3: Implement provider, namespace and workflow phase**

Add `hashicorp/kubernetes`, configure EKS exec auth, create the labelled namespace, and target it after kubeconfig setup but before Helm synchronization/full apply.

- [ ] **Step 4: Update documentation**

Record that shared infrastructure owns only the namespace while service repositories own all workloads.

- [ ] **Step 5: Verify and commit**

Run the full test suite, Terraform format/validate and workflow YAML validation. Commit as `feat: manage shared oficina namespace`.
