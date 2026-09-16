resource "helm_release" "newrelic" {
  name             = "newrelic"
  repository       = "https://helm-charts.newrelic.com"
  chart            = "nri-bundle"
  version          = var.new_relic_chart_version
  namespace        = "newrelic"
  create_namespace = true
  timeout          = 600

  set_sensitive = [
    {
      name  = "global.licenseKey"
      value = var.new_relic_license_key
    },
  ]

  set = [
    { name = "global.cluster", value = aws_eks_cluster.main.name },
    { name = "kube-state-metrics.enabled", value = "true" },
    { name = "nri-kube-events.enabled", value = "true" },
    { name = "newrelic-logging.enabled", value = "true" },
  ]

  depends_on = [
    aws_eks_cluster.main,
    aws_eks_node_group.main,
  ]
}
