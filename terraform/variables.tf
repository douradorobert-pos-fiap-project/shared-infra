variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., sandbox, prod)"
  type        = string
  default     = "sandbox"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "eks_cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "sandbox-eks"
}

variable "eks_kubernetes_version" {
  description = "Kubernetes version for the EKS control plane"
  type        = string
  default     = "1.31"
}

variable "eks_node_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "eks_desired_node_size" {
  description = "Desired number of nodes in EKS node group"
  type        = number
  default     = 2
}

variable "eks_min_node_size" {
  description = "Minimum number of nodes in EKS node group"
  type        = number
  default     = 1
}

variable "eks_max_node_size" {
  description = "Maximum number of nodes in EKS node group"
  type        = number
  default     = 4
}

variable "lambda_cpf_validator_name" {
  description = "Name of the existing CPF validator Lambda function"
  type        = string
  default     = "CpfValidatorTest"
}

variable "existing_iam_role_arn" {
  description = "ARN of the existing LabRole used by EKS, worker nodes, and the Lambda authorizer"
  type        = string
  default     = "arn:aws:iam::264040538379:role/LabRole"

  validation {
    condition     = can(regex("^arn:[^:]+:iam::[0-9]{12}:role/.+$", var.existing_iam_role_arn))
    error_message = "existing_iam_role_arn must be the ARN of an existing IAM role."
  }
}

variable "api_gateway_cors_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "jwt_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the JWT secret"
  type        = string
  default     = "" # Set via terraform.tfvars or CI/CD
}

variable "lb_controller_namespace" {
  description = "Kubernetes namespace for AWS LB Controller"
  type        = string
  default     = "kube-system"
}

variable "lb_controller_service_account_name" {
  description = "Kubernetes ServiceAccount used by the AWS Load Balancer Controller"
  type        = string
  default     = "aws-load-balancer-controller"
}

variable "new_relic_license_key" {
  description = "New Relic license key supplied through CI/CD"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.new_relic_license_key)) > 0
    error_message = "new_relic_license_key must be provided through CI/CD."
  }
}

variable "new_relic_chart_version" {
  description = "Version of the official New Relic nri-bundle Helm chart"
  type        = string
  default     = "8.0.10"
}
