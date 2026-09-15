resource "aws_lb" "app_nlb" {
  name               = "${var.environment}-app-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = aws_subnet.public[*].id

  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "${var.environment}-app-nlb"
    Environment = var.environment
  }
}

resource "aws_security_group_rule" "nlb_to_pods" {
  type              = "ingress"
  security_group_id = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id

  from_port   = 8000
  to_port     = 8000
  protocol    = "tcp"
  cidr_blocks = var.public_subnet_cidrs

  description = "Allow NLB health checks and traffic to application pods"
}

resource "aws_lb_target_group" "app" {
  name        = "${var.environment}-app-tg"
  port        = 80
  protocol    = "TCP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    protocol            = "HTTP"
    port                = "traffic-port"
    path                = "/health"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    interval            = 30
  }

  tags = {
    Name        = "${var.environment}-app-tg"
    Environment = var.environment
  }
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.app_nlb.arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
