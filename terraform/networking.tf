resource "aws_security_group" "internal_alb" {
  name_prefix = "${var.environment}-internal-alb-"
  description = "Internal ALB used by API Gateway VPC Link"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from API Gateway VPC Link"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.vpc_link.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-internal-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group_rule" "internal_alb_to_pods" {
  type                     = "ingress"
  security_group_id        = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  source_security_group_id = aws_security_group.internal_alb.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  description              = "Allow internal ALB traffic to application pods"
}

data "aws_lb" "internal_alb" {
  name       = "${var.environment}-api-alb"
  depends_on = [helm_release.aws_lb_controller]
}

data "aws_lb_listener" "internal_alb" {
  load_balancer_arn = data.aws_lb.internal_alb.arn
  port              = 80
}
