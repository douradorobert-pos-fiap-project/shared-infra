resource "aws_secretsmanager_secret" "jwt" {
  name                    = "${var.environment}/jwt-secret"
  recovery_window_in_days = 0

  tags = {
    Name        = "${var.environment}-jwt-secret"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "jwt" {
  secret_id = aws_secretsmanager_secret.jwt.id
  secret_string = jsonencode({
    secret = "CHANGE-ME-IN-PRODUCTION"
  })
}
