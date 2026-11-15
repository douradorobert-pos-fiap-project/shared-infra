environment              = "sandbox"
vpc_cidr                 = "10.0.0.0/16"
public_subnet_cidrs      = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs     = ["10.0.10.0/24", "10.0.11.0/24"]
eks_kubernetes_version   = "1.31"
eks_node_instance_types  = ["t3.medium"]
eks_desired_node_size    = 2
eks_min_node_size        = 1
eks_max_node_size        = 4
api_gateway_cors_origins = ["*"]

# JWT secret ARN - will be populated after initial apply
jwt_secret_arn = ""
