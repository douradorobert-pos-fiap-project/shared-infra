"""AWS integration tests for deployed infra.

These tests require AWS credentials and a deployed infrastructure.
Run only after `terraform apply` completes successfully.

Usage:
    pytest tests/test_aws_integration.py -v
"""

import os
import unittest

import boto3


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "true",
    "Set RUN_INTEGRATION_TESTS=true to run integration tests"
)
class TestEksClusterIntegration(unittest.TestCase):
    """Verify EKS cluster is operational."""

    @classmethod
    def setUpClass(cls):
        cls.cluster_name = os.environ.get("EKS_CLUSTER_NAME", "sandbox-eks")
        cls.region = os.environ.get("AWS_REGION", "us-east-1")
        cls.eks = boto3.client("eks", region_name=cls.region)

    def test_cluster_exists(self):
        try:
            response = self.eks.describe_cluster(name=self.cluster_name)
            self.assertIn("status", response["cluster"])
        except self.eks.exceptions.ResourceNotFoundException:
            self.fail(f"EKS cluster {self.cluster_name} not found")

    def test_cluster_active(self):
        response = self.eks.describe_cluster(name=self.cluster_name)
        self.assertEqual(response["cluster"]["status"], "ACTIVE")

    def test_node_group_exists(self):
        response = self.eks.list_nodegroups(clusterName=self.cluster_name)
        self.assertGreater(len(response.get("nodegroups", [])), 0)


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "true",
    "Set RUN_INTEGRATION_TESTS=true to run integration tests"
)
class TestApiGatewayIntegration(unittest.TestCase):
    """Verify API Gateway is configured and reachable."""

    @classmethod
    def setUpClass(cls):
        cls.region = os.environ.get("AWS_REGION", "us-east-1")
        cls.apigw = boto3.client("apigatewayv2", region_name=cls.region)

    def test_api_exists(self):
        apis = self.apigw.get_apis()
        api_names = [api["Name"] for api in apis.get("Items", [])]
        self.assertTrue(
            any("cpf-validator" in name for name in api_names),
            f"CPF validator API not found. Found: {api_names}"
        )

    def test_post_cpf_route_exists(self):
        apis = self.apigw.get_apis()
        cpf_api = next(
            (api for api in apis.get("Items", []) if "cpf-validator" in api["Name"]),
            None
        )
        self.assertIsNotNone(cpf_api)
        routes = self.apigw.get_routes(ApiId=cpf_api["ApiId"])
        route_keys = [route["RouteKey"] for route in routes.get("Items", [])]
        self.assertIn("POST /cpf", route_keys)


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "true",
    "Set RUN_INTEGRATION_TESTS=true to run integration tests"
)
class TestEcrRepositories(unittest.TestCase):
    """Verify ECR repositories are created."""

    @classmethod
    def setUpClass(cls):
        cls.region = os.environ.get("AWS_REGION", "us-east-1")
        cls.ecr = boto3.client("ecr", region_name=cls.region)

    def test_application_repo_exists(self):
        try:
            self.ecr.describe_repositories(repositoryNames=["application"])
        except self.ecr.exceptions.RepositoryNotFoundException:
            self.fail("Application ECR repository not found")

    def test_cpf_validator_repo_exists(self):
        try:
            self.ecr.describe_repositories(repositoryNames=["cpf-validator"])
        except self.ecr.exceptions.RepositoryNotFoundException:
            self.fail("CPF validator ECR repository not found")


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "true",
    "Set RUN_INTEGRATION_TESTS=true to run integration tests"
)
class TestVpcIntegration(unittest.TestCase):
    """Verify VPC and subnets are created."""

    @classmethod
    def setUpClass(cls):
        cls.region = os.environ.get("AWS_REGION", "us-east-1")
        cls.ec2 = boto3.client("ec2", region_name=cls.region)

    def test_vpc_exists(self):
        vpcs = self.ec2.describe_vpcs(
            Filters=[{"Name": "tag:Environment", "Values": ["sandbox"]}]
        )
        self.assertGreater(len(vpcs.get("Vpcs", [])), 0)

    def test_subnets_exist(self):
        subnets = self.ec2.describe_subnets(
            Filters=[{"Name": "tag:Environment", "Values": ["sandbox"]}]
        )
        self.assertGreaterEqual(len(subnets.get("Subnets", [])), 4)


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "true",
    "Set RUN_INTEGRATION_TESTS=true to run integration tests"
)
class TestPostCpfEndpoint(unittest.TestCase):
    """End-to-end test: POST /cpf returns a response from the Lambda."""

    @classmethod
    def setUpClass(cls):
        cls.endpoint = os.environ.get("API_GATEWAY_ENDPOINT")
        if not cls.endpoint:
            raise unittest.SkipTest("API_GATEWAY_ENDPOINT not set")

    def test_post_cpf_returns_response(self):
        import urllib.request
        import json

        url = f"{self.endpoint}/cpf"
        data = json.dumps({"cpf": "12345678900"}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                self.assertEqual(response.status, 200)
        except urllib.error.HTTPError as e:
            self.fail(f"POST /cpf returned {e.code}: {e.read()}")


if __name__ == "__main__":
    unittest.main()
