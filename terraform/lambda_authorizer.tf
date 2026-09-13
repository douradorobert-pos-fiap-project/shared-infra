data "archive_file" "lambda_authorizer" {
  type        = "zip"
  source_file = "${path.module}/lambda/authorizer/index.py"
  output_path = "${path.module}/lambda/authorizer.zip"
}

resource "aws_lambda_function" "authorizer" {
  function_name = "${var.environment}-jwt-authorizer"
  role          = var.existing_iam_role_arn
  runtime       = "python3.12"
  handler       = "index.handler"
  timeout       = 10
  memory_size   = 128

  filename         = data.archive_file.lambda_authorizer.output_path
  source_code_hash = data.archive_file.lambda_authorizer.output_base64sha256

  environment {
    variables = {
      JWT_SECRET_ARN = var.jwt_secret_arn
    }
  }

  tags = {
    Name        = "${var.environment}-jwt-authorizer"
    Environment = var.environment
  }
}
