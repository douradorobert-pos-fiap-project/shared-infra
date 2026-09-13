# CloudWatch Logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.environment}-api"
  retention_in_days = 30

  tags = {
    Name        = "${var.environment}-api-logs"
    Environment = var.environment
  }
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.environment}-api"
  protocol_type = "HTTP"
  description   = "HTTP API - entry point for all services"

  cors_configuration {
    allow_origins = var.api_gateway_cors_origins
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-api-key"]
    max_age       = 300
  }

  tags = {
    Name        = "${var.environment}-api"
    Environment = var.environment
  }
}

# Lambda Authorizer
resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.http_api.id
  authorizer_type  = "REQUEST"
  authorizer_uri   = aws_lambda_function.authorizer.invoke_arn
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.environment}-jwt-authorizer"

  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = false

  authorizer_result_ttl_in_seconds = 300
}

# VPC Link
resource "aws_apigatewayv2_vpc_link" "main" {
  name               = "${var.environment}-vpclink"
  security_group_ids = [aws_security_group.vpc_link.id]
  subnet_ids         = aws_subnet.private[*].id

  tags = {
    Name        = "${var.environment}-vpclink"
    Environment = var.environment
  }
}

resource "aws_security_group" "vpc_link" {
  name_prefix = "${var.environment}-vpclink-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-vpclink-sg"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# --- Integrations ---

# Lambda Integration (CPF Validator)
resource "aws_apigatewayv2_integration" "lambda_cpf" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  description            = "Lambda integration for CPF validator"
  connection_type        = "INTERNET"
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
  integration_uri        = data.aws_lambda_function.cpf_validator.invoke_arn
}

# NLB Integration (Application via VPC Link)
resource "aws_apigatewayv2_integration" "nlb_eks" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "HTTP_PROXY"
  description            = "NLB integration for EKS application via VPC Link"
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.main.id
  integration_method     = "ANY"
  payload_format_version = "1.0"
  timeout_milliseconds   = 30000
  integration_uri        = aws_lb_listener.app.arn
}

# Default Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId       = "$context.requestId"
      sourceIp        = "$context.identity.sourceIp"
      requestTime     = "$context.requestTime"
      httpMethod      = "$context.httpMethod"
      path            = "$context.path"
      routeKey        = "$context.routeKey"
      status          = "$context.status"
      responseLength  = "$context.responseLength"
      responseLatency = "$context.responseLatency"
    })
  }

  tags = {
    Name        = "${var.environment}-api-stage"
    Environment = var.environment
  }
}
