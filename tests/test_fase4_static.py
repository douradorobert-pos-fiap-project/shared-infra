"""Static Phase 4 infrastructure contracts; no AWS credentials required."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "terraform"


class TestPhase4SharedInfrastructure(unittest.TestCase):
    def read(self, name):
        return (TF / name).read_text()

    def test_three_independent_microservice_ecr_repositories(self):
        content = self.read("ecr.tf")
        for repository in (
            '"os-service"',
            '"billing-service"',
            '"execution-service"',
        ):
            self.assertIn(repository, content)
        for obsolete_repository in (
            "tech-challenge-fiap-os-service",
            "tech-challenge-fiap-billing-service",
            "tech-challenge-fiap-execution-service",
        ):
            self.assertNotIn(obsolete_repository, content)
        self.assertIn('image_tag_mutability = "IMMUTABLE"', content)
        self.assertIn("scan_on_push = true", content)

    def test_sqs_queues_have_dlqs_redrive_and_sandbox_toggle(self):
        content = self.read("messaging.tf")
        variables = self.read("variables.tf")
        self.assertIn('variable "enable_messaging"', variables)
        messaging_block = variables.split('variable "enable_messaging"', 1)[1].split("}", 1)[0]
        self.assertIn("default     = false", messaging_block)
        self.assertIn("var.enable_messaging", content)
        self.assertIn('resource "aws_sqs_queue" "dlq"', content)
        self.assertIn('resource "aws_sqs_queue" "service"', content)
        self.assertIn("redrive_policy", content)
        self.assertIn("maxReceiveCount", content)

    def test_execution_dynamodb_has_composite_key_gsi_and_toggle(self):
        content = self.read("dynamodb.tf")
        variables = self.read("variables.tf")
        self.assertIn('variable "enable_execution_dynamodb"', variables)
        dynamodb_block = variables.split('variable "enable_execution_dynamodb"', 1)[1].split("}", 1)[0]
        self.assertIn("default     = false", dynamodb_block)
        self.assertIn('resource "aws_dynamodb_table" "execution"', content)
        self.assertIn('hash_key     = "PK"', content)
        self.assertIn('range_key    = "SK"', content)
        self.assertIn('name            = "QueueIndex"', content)
        self.assertIn("PAY_PER_REQUEST", content)

    def test_sandbox_enables_distributed_messaging_and_execution_store(self):
        tfvars = (ROOT / "environments" / "sandbox" / "terraform.tfvars").read_text()

        self.assertIn("enable_messaging          = true", tfvars)
        self.assertIn("enable_execution_dynamodb = true", tfvars)

    def test_api_gateway_has_explicit_routes_for_each_service(self):
        content = self.read("api_gateway.tf")
        for prefix in ("/api/v1/service-orders", "/api/v1/quotes", "/api/v1/executions"):
            self.assertIn(prefix, content)
        self.assertIn("X-Correlation-ID", content)

    def test_phase4_outputs_do_not_expose_secrets(self):
        outputs = self.read("outputs.tf")
        for name in (
            "microservice_ecr_repository_urls",
            "service_queue_urls",
            "service_dlq_urls",
            "execution_dynamodb_table_name",
        ):
            self.assertIn(f'output "{name}"', outputs)
        self.assertNotIn("secret_access_key", outputs.lower())
        self.assertNotIn("session_token", outputs.lower())

    def test_no_new_iam_resources_are_required(self):
        all_tf = "\n".join(path.read_text() for path in TF.glob("*.tf"))
        self.assertNotIn('resource "aws_iam_', all_tf)

    def test_backend_and_account_configuration_are_portable(self):
        main = self.read("main.tf")
        executable_configuration = "\n".join(
            path.read_text()
            for path in (
                *TF.glob("*.tf"),
                ROOT / "environments" / "sandbox" / "terraform.tfvars",
                ROOT / ".github" / "workflows" / "terraform.yml",
            )
        )

        self.assertIn('backend "s3" {}', main)
        self.assertNotIn("terraform-state-", main)
        self.assertNotIn("264040538379", executable_configuration)

    def test_workflow_validates_prs_and_applies_only_by_manual_dispatch(self):
        workflow = (ROOT / ".github" / "workflows" / "terraform.yml").read_text()

        self.assertIn("pull_request:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("environment: sandbox", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("init -backend=false", workflow)
        self.assertIn('-backend-config="key=sandbox/terraform.tfstate"', workflow)

    def test_workflow_consumes_all_sandbox_variables(self):
        workflow = (ROOT / ".github" / "workflows" / "terraform.yml").read_text()

        for name in (
            "AWS_REGION",
            "TF_STATE_BUCKET",
            "EXISTING_IAM_ROLE_ARN",
            "LAMBDA_CPF_VALIDATOR_NAME",
            "EKS_CLUSTER_NAME",
        ):
            self.assertIn(f"vars.{name}", workflow)
        self.assertIn("scripts/check-fase4-permissions.sh", workflow)

    def test_availability_zones_follow_the_selected_region(self):
        variables = self.read("variables.tf")
        vpc = self.read("vpc.tf")
        tfvars = (ROOT / "environments" / "sandbox" / "terraform.tfvars").read_text()

        self.assertNotIn('variable "availability_zones"', variables)
        self.assertIn("data.aws_availability_zones.available.names", vpc)
        self.assertNotIn("us-east-1a", tfvars)
        self.assertNotIn("us-east-1b", tfvars)


if __name__ == "__main__":
    unittest.main()
