resource "aws_dynamodb_table" "execution" {
  count        = var.enable_execution_dynamodb ? 1 : 0
  name         = "${var.environment}-execution-service"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  global_secondary_index {
    name            = "QueueIndex"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.enable_dynamodb_point_in_time_recovery
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Service = "execution-service"
    Phase   = "4"
  }
}
