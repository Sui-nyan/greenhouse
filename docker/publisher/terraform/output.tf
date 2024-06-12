output "cert" {
  value = tls_cert_request.cert_request.cert_request_pem
}

output "key" {
  value     = tls_private_key.my_private_key.private_key_pem
  sensitive = true
}

output "thing_arn" {
  value = aws_iot_thing.my_thing.arn
}

output "iot_core_endpoint" {
  value = data.aws_iot_endpoint.current.endpoint_address
}