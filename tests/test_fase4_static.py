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
            "tech-challenge-fiap-os-service",
            "tech-challenge-fiap-billing-service",
            "tech-challenge-fiap-execution-service",
        ):
            self.assertIn(repository, content)
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


if __name__ == "__main__":
    unittest.main()
