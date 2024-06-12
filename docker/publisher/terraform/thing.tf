resource "aws_iot_thing" "my_thing" {
  name = "iot_gateway"
  attributes = {
    arn = aws_iam_role.core_role.arn
  }
}

resource "aws_iot_policy" "my_policy" {
  name   = "gateway_policy"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Connect"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Publish", "iot:Subscribe", "iot:Receive"],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "tls_private_key" "my_private_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}


locals {
  certificate_path         = "../client/certs/certificate.pem"
  private_key_path         = "../client/certs/private.key"
  root_ca_certificate_path = "../client/certs/root-CA.crt"
}


data "http" "ca_pem" {
  url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
}

resource "local_file" "root_ca_certificate" {
  content  = data.http.ca_pem.response_body
  filename = local.root_ca_certificate_path
}



resource "aws_iot_certificate" "my_certificate" {
  active = true
  csr    = tls_cert_request.cert_request.cert_request_pem
}

resource "aws_iot_policy_attachment" "my_policy_attachment" {
  policy = aws_iot_policy.my_policy.name
  target = aws_iot_certificate.my_certificate.arn
}

resource "aws_iot_thing_principal_attachment" "my_principal_attachment" {
  thing     = aws_iot_thing.my_thing.name
  principal = aws_iot_certificate.my_certificate.arn
}

resource "local_file" "certificate" {
  content  = aws_iot_certificate.my_certificate.certificate_pem
  filename = local.certificate_path
}


resource "tls_cert_request" "cert_request" {
  private_key_pem = tls_private_key.my_private_key.private_key_pem
  subject {
    common_name = aws_iot_thing.my_thing.name
  }
}

resource "local_file" "private_key" {
  content  = tls_private_key.my_private_key.private_key_pem
  filename = local.private_key_path
}

