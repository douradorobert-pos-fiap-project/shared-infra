data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_lambda_function" "cpf_validator" {
  function_name = var.lambda_cpf_validator_name
}
