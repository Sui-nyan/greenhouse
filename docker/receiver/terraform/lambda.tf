data "archive_file" "light_lambda_file" {
  type        = "zip"
  source_file = "../lambda_functions/light_lambda.py"
  output_path = "light_function_payload.zip"
}

resource "aws_lambda_function" "light_lambda" {
  function_name    = "light_lambda"
  filename         = "light_function_payload.zip"
  handler          = "light_lambda.light_handler"
  role             = aws_iam_role.core_role.arn
  source_code_hash = data.archive_file.light_lambda_file.output_base64sha256
  runtime          = "python3.9"
}

data "archive_file" "temperature_lambda_file" {
  type        = "zip"
  source_file = "../lambda_functions/temperature_lambda.py"
  output_path = "temperature_function_payload.zip"
}

resource "aws_lambda_function" "temperature_lambda" {
  function_name    = "temperature_lambda"
  filename         = "temperature_function_payload.zip"
  handler          = "temperature_lambda.temperature_handler"
  role             = aws_iam_role.core_role.arn
  source_code_hash = data.archive_file.light_lambda_file.output_base64sha256
  runtime          = "python3.9"
}
