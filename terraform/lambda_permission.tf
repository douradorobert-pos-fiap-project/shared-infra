resource "aws_lambda_permission" "cpf_invocation" {
  statement_id = "AllowAPIGatewayInvoke"
  action       = "lambda:InvokeFunction"
  # The AWS provider accepts a function ARN here. Keeping the ARN avoids
  # brittle string parsing and also supports a qualified Lambda ARN.
  function_name = data.aws_lambda_function.cpf_validator.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "authorizer_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/authorizers/*"
}
