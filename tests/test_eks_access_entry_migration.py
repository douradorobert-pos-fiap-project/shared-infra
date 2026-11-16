"""Behavioral tests for the destructive EKS access-entry migration."""

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "adopt-eks-node-access-entry.sh"
VALIDATOR = ROOT / "scripts" / "validate-eks-replacement-plan.py"

EXACT_PLAN = {
    "resource_changes": [
        {"address": "aws_eks_access_entry.nodes", "change": {"actions": ["delete", "create"]}},
        {"address": "aws_eks_node_group.main", "change": {"actions": ["delete", "create"]}},
        {"address": "aws_vpc.main", "change": {"actions": ["no-op"]}},
    ]
}


class TestEksAccessEntryMigration(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.log"
        self._write_fake_aws()
        self._write_fake_terraform()

    def tearDown(self):
        self.tempdir.cleanup()

    def _write_executable(self, name, content):
        path = self.bin / name
        path.write_text(textwrap.dedent(content))
        path.chmod(0o755)

    def _write_fake_aws(self):
        self._write_executable(
            "aws",
            """\
            #!/usr/bin/env python3
            import os
            import sys
            with open(os.environ["CALL_LOG"], "a") as log:
                log.write("aws " + " ".join(sys.argv[1:]) + "\\n")
            mode = os.environ.get("AWS_MODE", "EC2")
            if mode == "NOT_FOUND":
                print("ResourceNotFoundException: missing", file=sys.stderr)
                sys.exit(254)
            if mode == "ACCESS_DENIED":
                print("AccessDeniedException: denied", file=sys.stderr)
                sys.exit(254)
            print(mode)
            """,
        )

    def _write_fake_terraform(self):
        self._write_executable(
            "terraform",
            """\
            #!/usr/bin/env python3
            import os
            import sys
            args = sys.argv[1:]
            with open(os.environ["CALL_LOG"], "a") as log:
                log.write("terraform " + " ".join(args) + "\\n")
            command = next((arg for arg in args if not arg.startswith("-chdir=")), "")
            if command == "state" and "show" in args:
                sys.exit(0 if os.environ.get("STATE_MANAGED", "true") == "true" else 1)
            if command == "import" and os.environ.get("IMPORT_FAIL") == "true":
                sys.exit(1)
            if command == "plan":
                for arg in args:
                    if arg.startswith("-out="):
                        open(arg.split("=", 1)[1], "w").close()
                sys.exit(0)
            if command == "show":
                print(os.environ["PLAN_JSON"])
                sys.exit(0)
            sys.exit(0)
            """,
        )

    def run_script(self, **overrides):
        env = os.environ.copy()
        env.update({
            "PATH": f"{self.bin}:{env['PATH']}",
            "CALL_LOG": str(self.log),
            "AWS_REGION": "us-east-1",
            "EKS_CLUSTER_NAME": "oficina-sandbox",
            "EXISTING_IAM_ROLE_ARN": "arn:aws:iam::123456789012:role/LabRole",
            "PLAN_JSON": json.dumps(EXACT_PLAN),
            "STATE_MANAGED": "true",
        })
        env.update(overrides)
        return subprocess.run([str(SCRIPT)], cwd=ROOT, env=env, capture_output=True, text=True, check=False)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_ec2_entry_is_not_replaced(self):
        result = self.run_script(AWS_MODE="EC2")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(any(" plan " in f" {call} " for call in self.calls()))
        self.assertFalse(any(" apply " in f" {call} " for call in self.calls()))

    def test_missing_entry_removes_stale_state_without_apply(self):
        result = self.run_script(AWS_MODE="NOT_FOUND")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(any("state rm aws_eks_access_entry.nodes" in call for call in self.calls()))
        self.assertFalse(any(" apply " in f" {call} " for call in self.calls()))

    def test_non_not_found_aws_error_fails_closed(self):
        result = self.run_script(AWS_MODE="ACCESS_DENIED")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("AccessDeniedException", result.stderr)
        self.assertFalse(any(" apply " in f" {call} " for call in self.calls()))

    def test_import_happens_before_scoped_plan_and_saved_plan_apply(self):
        result = self.run_script(AWS_MODE="EC2_LINUX", STATE_MANAGED="false")
        self.assertEqual(0, result.returncode, result.stderr)
        calls = self.calls()
        import_index = next(i for i, call in enumerate(calls) if " import " in f" {call} ")
        plan_index = next(i for i, call in enumerate(calls) if " plan " in f" {call} ")
        apply_calls = [call for call in calls if " apply " in f" {call} "]
        self.assertLess(import_index, plan_index)
        self.assertEqual(1, len(apply_calls))
        self.assertNotIn("-replace=", apply_calls[0])
        self.assertIn("-target=aws_eks_access_entry.nodes", calls[plan_index])
        self.assertIn("-target=aws_eks_node_group.main", calls[plan_index])
        self.assertIn("-replace=aws_eks_access_entry.nodes", calls[plan_index])
        self.assertIn("-replace=aws_eks_node_group.main", calls[plan_index])

    def test_failed_import_blocks_plan_and_apply(self):
        result = self.run_script(AWS_MODE="EC2_LINUX", STATE_MANAGED="false", IMPORT_FAIL="true")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(any(" plan " in f" {call} " for call in self.calls()))
        self.assertFalse(any(" apply " in f" {call} " for call in self.calls()))

    def test_plan_validator_rejects_an_unexpected_changed_resource(self):
        unsafe_plan = dict(EXACT_PLAN)
        unsafe_plan["resource_changes"] = [
            *EXACT_PLAN["resource_changes"],
            {"address": "kubernetes_namespace_v1.oficina", "change": {"actions": ["delete"]}},
        ]
        result = subprocess.run(
            ["python3", str(VALIDATOR)],
            input=json.dumps(unsafe_plan),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unexpected Terraform changes", result.stderr)


if __name__ == "__main__":
    unittest.main()
