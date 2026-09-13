resource "aws_eks_cluster" "main" {
  name     = var.eks_cluster_name
  role_arn = var.existing_iam_role_arn
  version  = var.eks_kubernetes_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  kubernetes_network_config {
    ip_family = "ipv4"
  }

  tags = {
    Name        = var.eks_cluster_name
    Environment = var.environment
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.environment}-node-group"
  node_role_arn   = var.existing_iam_role_arn
  subnet_ids      = aws_subnet.private[*].id
  capacity_type   = "ON_DEMAND"

  scaling_config {
    desired_size = var.eks_desired_node_size
    max_size     = var.eks_max_node_size
    min_size     = var.eks_min_node_size
  }

  instance_types = var.eks_node_instance_types

  update_config {
    max_unavailable = 1
  }

  labels = {
    environment = var.environment
  }

  tags = {
    Name        = "${var.eks_cluster_name}-node-group"
    Environment = var.environment
  }

  # Managed nodes run in private subnets and use the cluster's public API
  # endpoint during bootstrap.  Make the NAT path explicit so a targeted EKS
  # apply also creates the public and private route associations first.
  depends_on = [
    aws_route_table_association.public,
    aws_route_table_association.private,
  ]
}

resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"

  tags = {
    Environment = var.environment
  }
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"

  tags = {
    Environment = var.environment
  }
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"

  tags = {
    Environment = var.environment
  }
}

resource "helm_release" "aws_lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = "1.7.1"
  namespace  = "kube-system"
  timeout    = 600

  set = [
    { name = "clusterName", value = aws_eks_cluster.main.name },
    { name = "serviceAccount.create", value = "true" },
    { name = "serviceAccount.name", value = "aws-load-balancer-controller" },
    { name = "region", value = var.aws_region },
    { name = "vpcId", value = aws_vpc.main.id },
  ]

  depends_on = [aws_eks_node_group.main]
}
