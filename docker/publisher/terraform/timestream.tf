resource "aws_timestreamwrite_database" "timestream_base" {
  database_name = "sensor_data_db"
}

resource "aws_timestreamwrite_table" "timestream_table" {
  database_name = aws_timestreamwrite_database.timestream_base.database_name
  table_name    = "sensor_data_table"

  retention_properties {
    magnetic_store_retention_period_in_days = 1
    memory_store_retention_period_in_hours  = 24
  }
}