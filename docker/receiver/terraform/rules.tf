resource "aws_iot_topic_rule" "iot_rule" {
  name        = "iot_rule"
  description = "rule to route all data on sensor_data to detector models, created with terraform"
  enabled     = true
  sql_version = "2016-03-23"
  sql         = "SELECT * FROM 'iot/sensor_data'"
  iot_events {
    input_name = "window_input"
    role_arn   = aws_iam_role.core_role.arn
  }
  iot_events {
    input_name = "light_input"
    role_arn   = aws_iam_role.core_role.arn
  }
  iot_events {
    input_name = "sprinkler_input"
    role_arn   = aws_iam_role.core_role.arn
  }
  error_action {
    republish {
      role_arn = aws_iam_role.core_role.arn
      topic    = "iot/error"
    }
  }
}

resource "aws_iot_topic_rule" "timestream_routing" {
  name        = "timestream_routing"
  description = "rule to route all data on sensor_data to timestream, created with terraform"
  enabled     = true
  sql_version = "2016-03-23"
  sql         = "SELECT * FROM 'iot/sensor_data'"
  timestream {
    database_name = "sensor_data_db"
    table_name    = "sensor_data_table"
    dimension {
      name  = "device_id"
      value = uuid()
    }
    role_arn = aws_iam_role.core_role.arn
  }
}