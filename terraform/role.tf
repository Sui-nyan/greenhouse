resource "aws_iam_role" "core_role" {
  name               = "core_role"
  assume_role_policy = file("${path.module}/assume_role_policy.json")
  description        = "core_role for everything, created with terraform"
}

resource "aws_iam_role_policy" "core_policy" {
  name = "core_policy"
  role = aws_iam_role.core_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:*"]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = ["timestream:*"]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = ["iot:Connect",
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive",
          "iot:GetThingShadow",
          "iot:UpdateThingShadow",
          "iot:DeleteThingShadow",
        "iot:ListNamedShadowsForThing"]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = ["iotevents:*"]
        Resource = ["*"]
    }]
  })
}