resource "kubernetes_namespace_v1" "oficina" {
  metadata {
    name = "oficina"

    labels = {
      "app.kubernetes.io/part-of" = "oficina"
      Environment                 = var.environment
      ManagedBy                   = "terraform"
    }
  }

  depends_on = [
    aws_eks_node_group.main,
  ]
}
