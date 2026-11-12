locals {
  service_queues = var.enable_messaging ? {
    os-service        = "os-service-events"
    billing-service   = "billing-service-events"
    execution-service = "execution-service-events"
  } : {}
}

resource "aws_sqs_queue" "dlq" {
  for_each                  = local.service_queues
  name                      = "${var.environment}-${each.value}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    Service = each.key
    Purpose = "dead-letter"
  }
}

resource "aws_sqs_queue" "service" {
  for_each                   = local.service_queues
  name                       = "${var.environment}-${each.value}"
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq[each.key].arn
    maxReceiveCount     = var.sqs_max_receive_count
  })

  tags = {
    Service = each.key
    Purpose = "integration-events"
  }
}
