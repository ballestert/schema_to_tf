# Provider configuration
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Name of the project"
  default     = "electricitymaps"
}

# EventBridge schedule
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "${var.project_name}-daily-trigger"
  description         = "Triggers the ElectricityMaps data ingestion process daily at 6AM"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.ingest_data.arn
}

# Lambda functions
resource "aws_lambda_function" "ingest_data" {
  filename      = "ingest_data_lambda.zip"
  function_name = "${var.project_name}-ingest-data"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.lambda_handler"
  runtime       = "python3.12"

  environment {
    variables = {
      LANDING_ZONE_BUCKET = aws_s3_bucket.landing_zone.id
      PARAM_BUCKET        = aws_s3_bucket.param.id
    }
  }
}

resource "aws_lambda_function" "process_azure" {
  filename      = "process_azure_lambda.zip"
  function_name = "${var.project_name}-process-azure"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.lambda_handler"
  runtime       = "python3.12"

  environment {
    variables = {
      RESULT_BUCKET = aws_s3_bucket.result.id
    }
  }
}

resource "aws_lambda_function" "process_aws" {
  filename      = "process_aws_lambda.zip"
  function_name = "${var.project_name}-process-aws"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.lambda_handler"
  runtime       = "python3.12"

  environment {
    variables = {
      RESULT_BUCKET = aws_s3_bucket.result.id
    }
  }
}

# S3 buckets
resource "aws_s3_bucket" "landing_zone" {
  bucket = "${var.project_name}-landing-zone"
}

resource "aws_s3_bucket" "result" {
  bucket = "${var.project_name}-result"
}

resource "aws_s3_bucket" "param" {
  bucket = "${var.project_name}-param"
}

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.landing_zone.arn,
          "${aws_s3_bucket.landing_zone.arn}/*",
          aws_s3_bucket.result.arn,
          "${aws_s3_bucket.result.arn}/*",
          aws_s3_bucket.param.arn,
          "${aws_s3_bucket.param.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ]
        Resource = "*"
      }
    ]
  })
}

# Athena resources
resource "aws_athena_database" "electricitymaps_db" {
  name   = "${var.project_name}_db"
  bucket = aws_s3_bucket.result.id
}

resource "aws_athena_workgroup" "electricitymaps_workgroup" {
  name = "${var.project_name}-workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.result.bucket}/athena-results/"
    }
  }
}

# Outputs
output "landing_zone_bucket" {
  value = aws_s3_bucket.landing_zone.id
}

output "result_bucket" {
  value = aws_s3_bucket.result.id
}

output "param_bucket" {
  value = aws_s3_bucket.param.id
}

output "ingest_lambda_arn" {
  value = aws_lambda_function.ingest_data.arn
}

output "process_azure_lambda_arn" {
  value = aws_lambda_function.process_azure.arn
}

output "process_aws_lambda_arn" {
  value = aws_lambda_function.process_aws.arn
}

output "athena_database_name" {
  value = aws_athena_database.electricitymaps_db.name
}

output "athena_workgroup_name" {
  value = aws_athena_workgroup.electricitymaps_workgroup.name
}