"""Tests for infra Terraform configuration.

These tests validate the static structure and configuration of the
Terraform code. They do NOT require AWS credentials.

For tests that interact with AWS, see test_aws_integration.py.
"""

import os
import re
import unittest
from pathlib import Path

TERRAFORM_DIR = Path(__file__).parent.parent / "terraform"


class TestEcrRepositories(unittest.TestCase):
    """Test ECR repository configuration."""

    def test_ecr_file_exists(self):
        ecr_file = TERRAFORM_DIR / "ecr.tf"
        self.assertTrue(ecr_file.exists(), "ecr.tf must exist")

    def test_application_repository_defined(self):
        content = (TERRAFORM_DIR / "ecr.tf").read_text()
        self.assertIn('aws_ecr_repository', content)
        self.assertIn('"application"', content)

    def test_cpf_validator_repository_defined(self):
        content = (TERRAFORM_DIR / "ecr.tf").read_text()
        self.assertIn('aws_ecr_repository', content)
        self.assertIn('"cpf-validator"', content)

    def test_repositories_use_immutable_tags(self):
        content = (TERRAFORM_DIR / "ecr.tf").read_text()
        self.assertIn('image_tag_mutability = "IMMUTABLE"', content)

    def test_repositories_have_scan_on_push(self):
        content = (TERRAFORM_DIR / "ecr.tf").read_text()
        self.assertIn('scan_on_push = true', content)

    def test_repositories_have_lifecycle_policy(self):
        content = (TERRAFORM_DIR / "ecr.tf").read_text()
        self.assertIn('aws_ecr_lifecycle_policy', content)


class TestVpcNetworking(unittest.TestCase):
    """Test VPC and networking configuration."""

    def test_vpc_file_exists(self):
        vpc_file = TERRAFORM_DIR / "vpc.tf"
        self.assertTrue(vpc_file.exists(), "vpc.tf must exist")

    def test_vpc_resource_defined(self):
        content = (TERRAFORM_DIR / "vpc.tf").read_text()
        self.assertIn('resource "aws_vpc" "main"', content)

    def test_public_and_private_subnets(self):
        content = (TERRAFORM_DIR / "vpc.tf").read_text()
        self.assertIn('resource "aws_subnet" "public"', content)
        self.assertIn('resource "aws_subnet" "private"', content)

    def test_internet_gateway_defined(self):
        content = (TERRAFORM_DIR / "vpc.tf").read_text()
        self.assertIn('aws_internet_gateway', content)

    def test_nat_gateway_defined(self):
        content = (TERRAFORM_DIR / "vpc.tf").read_text()
        self.assertIn('aws_nat_gateway', content)

    def test_route_tables_defined(self):
        content = (TERRAFORM_DIR / "vpc.tf").read_text()
        self.assertIn('aws_route_table', content)
        self.assertIn('aws_route_table_association', content)

    def test_vpc_outputs(self):
        content = (TERRAFORM_DIR / "outputs.tf").read_text()
        self.assertIn('vpc_id', content)
        self.assertIn('private_subnet_ids', content)
        self.assertIn('public_subnet_ids', content)


class TestExistingIamRole(unittest.TestCase):
    """Test reuse of the pre-provisioned LabRole."""

    def test_existing_role_variable_defined(self):
        content = (TERRAFORM_DIR / "variables.tf").read_text()
        self.assertIn('variable "existing_iam_role_arn"', content)

    def test_eks_uses_existing_role(self):
        content = (TERRAFORM_DIR / "eks.tf").read_text()
        self.assertIn('role_arn = var.existing_iam_role_arn', content)
        self.assertIn('node_role_arn   = var.existing_iam_role_arn', content)

    def test_no_iam_roles_are_created(self):
        terraform_files = "\n".join(file.read_text() for file in TERRAFORM_DIR.glob("*.tf"))
        self.assertNotIn('resource "aws_iam_role"', terraform_files)


class TestEksCluster(unittest.TestCase):
    """Test EKS configuration."""

    def test_eks_file_exists(self):
        eks_file = TERRAFORM_DIR / "eks.tf"
        self.assertTrue(eks_file.exists(), "eks.tf must exist")

    def test_eks_cluster_defined(self):
        content = (TERRAFORM_DIR / "eks.tf").read_text()
        self.assertIn('resource "aws_eks_cluster" "main"', content)

    def test_eks_node_group_defined(self):
        content = (TERRAFORM_DIR / "eks.tf").read_text()
        self.assertIn('resource "aws_eks_node_group" "main"', content)

    def test_eks_addons_defined(self):
        content = (TERRAFORM_DIR / "eks.tf").read_text()
        self.assertIn('aws_eks_addon', content)
        self.assertIn('vpc-cni', content)
        self.assertIn('coredns', content)
        self.assertIn('kube-proxy', content)

    def test_eks_outputs_defined(self):
        content = (TERRAFORM_DIR / "outputs.tf").read_text()
        self.assertIn('eks_cluster_name', content)
        self.assertIn('eks_cluster_endpoint', content)

    def test_node_group_waits_for_private_network_routes(self):
        content = (TERRAFORM_DIR / "eks.tf").read_text()
        self.assertIn('aws_route_table_association.public', content)
        self.assertIn('aws_route_table_association.private', content)


class TestApiGateway(unittest.TestCase):
    """Test API Gateway configuration."""

    def test_api_gateway_file_exists(self):
        api_file = TERRAFORM_DIR / "api_gateway.tf"
        self.assertTrue(api_file.exists(), "api_gateway.tf must exist")

    def test_http_api_defined(self):
        content = (TERRAFORM_DIR / "api_gateway.tf").read_text()
        self.assertIn('resource "aws_apigatewayv2_api" "http_api"', content)
        self.assertIn('protocol_type = "HTTP"', content)

    def test_lambda_integration_defined(self):
        content = (TERRAFORM_DIR / "api_gateway.tf").read_text()
        self.assertIn('aws_apigatewayv2_integration', content)
        self.assertIn('AWS_PROXY', content)

    def test_default_stage_defined(self):
        content = (TERRAFORM_DIR / "api_gateway.tf").read_text()
        self.assertIn('aws_apigatewayv2_stage', content)

    def test_cloudwatch_logs_defined(self):
        content = (TERRAFORM_DIR / "api_gateway.tf").read_text()
        self.assertIn('aws_cloudwatch_log_group', content)

    def test_api_gateway_outputs(self):
        content = (TERRAFORM_DIR / "outputs.tf").read_text()
        self.assertIn('api_gateway_id', content)
        self.assertIn('api_gateway_endpoint', content)


class TestLambdaPermission(unittest.TestCase):
    """Test Lambda permission configuration."""

    def test_lambda_permission_file_exists(self):
        perm_file = TERRAFORM_DIR / "lambda_permission.tf"
        self.assertTrue(perm_file.exists(), "lambda_permission.tf must exist")

    def test_lambda_permission_defined(self):
        content = (TERRAFORM_DIR / "lambda_permission.tf").read_text()
        self.assertIn('resource "aws_lambda_permission"', content)
        self.assertIn('lambda:InvokeFunction', content)
        self.assertIn('apigateway.amazonaws.com', content)

    def test_uses_source_arn_for_least_privilege(self):
        content = (TERRAFORM_DIR / "lambda_permission.tf").read_text()
        self.assertIn('source_arn', content)
        self.assertIn('execution_arn', content)

    def test_no_wildcard_principal(self):
        """Verify the principal is not a wildcard."""
        content = (TERRAFORM_DIR / "lambda_permission.tf").read_text()
        self.assertNotIn('principal     = "*"', content)


class TestLambdaExternalReference(unittest.TestCase):
    """Test external Lambda reference."""

    def test_lambda_name_variable_defined(self):
        content = (TERRAFORM_DIR / "variables.tf").read_text()
        self.assertIn('lambda_cpf_validator_name', content)

    def test_lambda_data_source_defined(self):
        content = (TERRAFORM_DIR / "data.tf").read_text()
        self.assertIn('data "aws_lambda_function"', content)

    def test_lambda_arn_output(self):
        content = (TERRAFORM_DIR / "outputs.tf").read_text()
        self.assertIn('lambda_arn', content)


class TestOutputs(unittest.TestCase):
    """Test required outputs are defined."""

    REQUIRED_OUTPUTS = [
        "vpc_id",
        "private_subnet_ids",
        "public_subnet_ids",
        "eks_cluster_name",
        "eks_cluster_endpoint",
        "ecr_application_repository_url",
        "ecr_cpf_validator_repository_url",
        "api_gateway_id",
        "api_gateway_endpoint",
        "lambda_arn",
    ]

    def test_outputs_file_exists(self):
        outputs_file = TERRAFORM_DIR / "outputs.tf"
        self.assertTrue(outputs_file.exists(), "outputs.tf must exist")

    def test_all_required_outputs_defined(self):
        content = (TERRAFORM_DIR / "outputs.tf").read_text()
        for output in self.REQUIRED_OUTPUTS:
            self.assertIn(output, content, f"Output {output} must be defined")


class TestPipeline(unittest.TestCase):
    """Test CI/CD pipeline configuration."""

    def test_workflow_file_exists(self):
        workflow = Path(__file__).parent.parent / ".github" / "workflows" / "terraform.yml"
        self.assertTrue(workflow.exists(), "terraform.yml must exist")

    def test_uses_temporary_aws_credentials(self):
        content = (Path(__file__).parent.parent / ".github" / "workflows" / "terraform.yml").read_text()
        self.assertIn('configure-aws-credentials', content)
        self.assertIn('aws-access-key-id', content)
        self.assertIn('aws-secret-access-key', content)
        self.assertIn('aws-session-token', content)

    def test_has_format_step(self):
        content = (Path(__file__).parent.parent / ".github" / "workflows" / "terraform.yml").read_text()
        self.assertIn('terraform fmt', content)

    def test_has_validate_step(self):
        content = (Path(__file__).parent.parent / ".github" / "workflows" / "terraform.yml").read_text()
        self.assertIn('terraform validate', content)

    def test_has_plan_step(self):
        content = (Path(__file__).parent.parent / ".github" / "workflows" / "terraform.yml").read_text()
        self.assertIn('plan-infrastructure.sh', content)

    def test_has_apply_step(self):
        content = (Path(__file__).parent.parent / ".github" / "workflows" / "terraform.yml").read_text()
        self.assertIn('apply-infrastructure.sh', content)


class TestBackend(unittest.TestCase):
    """Test state-management assumptions."""

    def test_no_undeclared_remote_backend(self):
        content = (TERRAFORM_DIR / "main.tf").read_text()
        self.assertNotIn('backend "s3"', content)


class TestFileStructure(unittest.TestCase):
    """Test that the required file structure exists."""

    REQUIRED_FILES = [
        "terraform/main.tf",
        "terraform/variables.tf",
        "terraform/outputs.tf",
        "terraform/providers.tf",
        "terraform/ecr.tf",
        "terraform/vpc.tf",
        "terraform/eks.tf",
        "terraform/api_gateway.tf",
        "terraform/lambda_permission.tf",
        "terraform/data.tf",
        "environments/sandbox/terraform.tfvars",
        ".github/workflows/terraform.yml",
    ]

    def test_all_required_files_exist(self):
        for relative_path in self.REQUIRED_FILES:
            file_path = Path(__file__).parent.parent / relative_path
            self.assertTrue(
                file_path.exists(),
                f"Required file missing: {relative_path}"
            )


class TestNoRdsOwnership(unittest.TestCase):
    """Verify RDS is not managed by infra repository."""

    def test_no_rds_resources(self):
        """Ensure no RDS resources are defined in the infra repo."""
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('aws_db_instance', content, f"{tf_file.name} should not contain RDS resources")
            self.assertNotIn('aws_rds_cluster', content, f"{tf_file.name} should not contain RDS resources")
            self.assertNotIn('aws_db_subnet_group', content, f"{tf_file.name} should not contain RDS resources")


class TestNoKubernetesResources(unittest.TestCase):
    """Verify no Kubernetes resources are managed by infra repository."""

    def test_no_kubernetes_namespace(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_namespace"', content,
                             f"{tf_file.name} should not contain kubernetes_namespace")

    def test_no_kubernetes_deployment(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_deployment"', content,
                             f"{tf_file.name} should not contain kubernetes_deployment")

    def test_no_kubernetes_service(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_service', content,
                             f"{tf_file.name} should not contain kubernetes_service")

    def test_no_kubernetes_manifest(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_manifest"', content,
                             f"{tf_file.name} should not contain kubernetes_manifest")

    def test_no_kubernetes_configmap(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_config_map"', content,
                             f"{tf_file.name} should not contain kubernetes_config_map")

    def test_no_kubernetes_secret(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_secret"', content,
                             f"{tf_file.name} should not contain kubernetes_secret")

    def test_no_horizontal_pod_autoscaler(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "kubernetes_horizontal_pod_autoscaler"', content,
                             f"{tf_file.name} should not contain kubernetes_horizontal_pod_autoscaler")


class TestNoApiGatewayRoutes(unittest.TestCase):
    """Verify no API Gateway routes are defined in infra repository."""

    def test_no_apigatewayv2_route(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('resource "aws_apigatewayv2_route"', content,
                             f"{tf_file.name} should not contain api_gateway routes")


class TestNoApplicationWorkload(unittest.TestCase):
    """Verify application-specific resources are not managed by infra repository."""

    def test_no_oficina_namespace(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('oficina', content,
                             f"{tf_file.name} should not reference oficina namespace")

    def test_no_oficina_api_service(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('oficina-api', content,
                             f"{tf_file.name} should not reference oficina-api service")

    def test_no_target_group_binding(self):
        for tf_file in TERRAFORM_DIR.glob("*.tf"):
            content = tf_file.read_text()
            self.assertNotIn('TargetGroupBinding', content,
                             f"{tf_file.name} should not contain TargetGroupBinding")


if __name__ == "__main__":
    unittest.main()
