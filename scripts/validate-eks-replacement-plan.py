#!/usr/bin/env python3
"""Reject an EKS migration plan that changes anything outside its allowlist."""

import json
import sys


EXPECTED_CHANGES = {
    "aws_eks_access_entry.nodes": ["delete", "create"],
    "aws_eks_node_group.main": ["delete", "create"],
}


def main():
    plan = json.load(sys.stdin)
    actual_changes = {
        resource["address"]: resource["change"]["actions"]
        for resource in plan.get("resource_changes", [])
        if resource["change"]["actions"] != ["no-op"]
    }

    if actual_changes != EXPECTED_CHANGES:
        print(
            "unexpected Terraform changes in EKS replacement plan: "
            f"expected {EXPECTED_CHANGES}, got {actual_changes}",
            file=sys.stderr,
        )
        return 1

    print("EKS replacement plan contains only the two approved replacements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
