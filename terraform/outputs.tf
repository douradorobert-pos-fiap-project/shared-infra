output "vpc_id" {
  description = "VPC ID for use by other repositories"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for RDS and EKS use by database repository"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs for load balancers by other repositories"
  value       = aws_subnet.public[*].id
}

output "eks_cluster_name" {
  description = "EKS cluster name for deployment by application repository"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint for application communication"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "eks_node_role_arn" {
  description = "EKS node IAM role ARN"
  value       = var.existing_iam_role_arn
}

output "ecr_application_repository_url" {
  description = "Application ECR repository URL for application and lambda pipelines"
  value       = aws_ecr_repository.application.repository_url
}

output "ecr_application_repository_arn" {
  description = "Application ECR repository ARN"
  value       = aws_ecr_repository.application.arn
}

output "ecr_cpf_validator_repository_url" {
  description = "CPF validator ECR repository URL for lambda pipeline"
  value       = aws_ecr_repository.cpf_validator.repository_url
}

output "ecr_cpf_validator_repository_arn" {
  description = "CPF validator ECR repository ARN"
  value       = aws_ecr_repository.cpf_validator.arn
}

output "api_gateway_id" {
  description = "API Gateway HTTP API ID"
  value       = aws_apigatewayv2_api.http_api.id
}

output "api_gateway_endpoint" {
  description = "API Gateway HTTP API endpoint for client integration"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "api_gateway_arn" {
  description = "API Gateway HTTP API ARN"
  value       = aws_apigatewayv2_api.http_api.arn
}

output "api_gateway_name" {
  description = "API Gateway name"
  value       = aws_apigatewayv2_api.http_api.name
}

output "lambda_arn" {
  description = "Lambda ARN for external reference"
  value       = data.aws_lambda_function.cpf_validator.arn
}

output "api_gateway_logs_arn" {
  description = "CloudWatch log group ARN for API Gateway access logs"
  value       = aws_cloudwatch_log_group.api_logs.arn
}

output "nlb_dns_name" {
  description = "NLB DNS name for application"
  value       = aws_lb.app_nlb.dns_name
}

output "nlb_arn" {
  description = "NLB ARN"
  value       = aws_lb.app_nlb.arn
}

output "jwt_secret_arn" {
  description = "Secrets Manager ARN for JWT secret"
  value       = aws_secretsmanager_secret.jwt.arn
  sensitive   = true
}

output "lambda_authorizer_function_name" {
  description = "Lambda authorizer function name"
  value       = aws_lambda_function.authorizer.function_name
}

output "lambda_authorizer_function_arn" {
  description = "Lambda authorizer function ARN"
  value       = aws_lambda_function.authorizer.arn
}

output "vpc_link_id" {
  description = "VPC Link ID"
  value       = aws_apigatewayv2_vpc_link.main.id
}
