import unittest
from unittest.mock import patch, MagicMock

try:
    from temperature_lambda import query_database, format_temperature_data, get_device_ids, all_present_and_hot, temperature_handler
except ModuleNotFoundError:
    from lambda_functions.temperature_lambda import query_database, format_temperature_data, get_device_ids, all_present_and_hot, temperature_handler

class TestMyModule(unittest.TestCase):
    @patch("boto3.client")
    def test_query_database_equals(self, mock_client):
        mock_timestream = MagicMock()
        mock_client.return_value = mock_timestream
        query = """
           asfdgasdf
        """
        mock_timestream.query.return_value = "mocked response"

        actual_response = query_database(query)

        mock_timestream.query.assert_called_once_with(QueryString=query)
        self.assertEqual(actual_response, "mocked response")

    @patch("boto3.client")
    def test_query_database_not_equals(self, mock_client):
        mock_timestream = MagicMock()
        mock_client.return_value = mock_timestream
        query = """
           asfdgasdf
        """
        mock_timestream.query.return_value = "mocked response"

        actual_response = query_database(query)

        mock_timestream.query.assert_called_once_with(QueryString=query)
        self.assertNotEqual(actual_response, "something else")
    
    
    def test_format_temperature_data(self):
        temperature_response = {
            'Rows': [
                {'Data': [{'ScalarValue': 'temperature'}, {'ScalarValue': '2023-07-14'}, {'ScalarValue': '25.0'}, {'ScalarValue': '001'}]},
                {'Data': [{'ScalarValue': 'temperature'}, {'ScalarValue': '2023-07-14'}, {'ScalarValue': '26.0'}, {'ScalarValue': '002'}]}
            ]
        }
        result = format_temperature_data(temperature_response)
        expected_result = {
            0: {'measure_name': 'temperature', 'temperature': 25.0, 'device_id': '001', 'timestamp': '2023-07-14'},
            1: {'measure_name': 'temperature', 'temperature': 26.0, 'device_id': '002', 'timestamp': '2023-07-14'}
        }
        self.assertEqual(result, expected_result)

    def test_get_device_ids(self):
        response = {
            'Rows': [
                {'Data': [{'ScalarValue': '001'}]},
                {'Data': [{'ScalarValue': '002'}]}
            ]
        }
        result = get_device_ids(response)
        expected_result = ['001', '002']
        self.assertEqual(result, expected_result)
    
    def test_all_present_and_hot(self):
        temperature_data = {
            0: {'measure_name': 'temperature', 'temperature': 25.0, 'device_id': 'device1', 'timestamp': '2023-07-14'},
            1: {'measure_name': 'temperature', 'temperature': 26.0, 'device_id': 'device2', 'timestamp': '2023-07-14'}
        }
        device_ids = ['device1', 'device2']
        result = all_present_and_hot(temperature_data, device_ids)
        self.assertFalse(result)

    def test_all_present_and_hot_not_present(self):
        temperature_data = {
            0: {'measure_name': 'temperature', 'temperature': 25.0, 'device_id': 'device1', 'timestamp': '2023-07-14'},
            1: {'measure_name': 'temperature', 'temperature': 26.0, 'device_id': 'device2', 'timestamp': '2023-07-14'}
        }
        device_ids = ['device1', 'device2', 'device3']
        result = all_present_and_hot(temperature_data, device_ids)
        self.assertFalse(result)

    def test_all_present_and_hot_not_hot(self):
        temperature_data = {
            0: {'measure_name': 'temperature', 'temperature': 20.0, 'device_id': 'device1', 'timestamp': '2023-07-14'},
            1: {'measure_name': 'temperature', 'temperature': 26.0, 'device_id': 'device2', 'timestamp': '2023-07-14'}
        }
        device_ids = ['device1', 'device2']
        result = all_present_and_hot(temperature_data, device_ids)
        self.assertFalse(result)

    @patch("temperature_lambda.query_database")
    @patch("temperature_lambda.get_device_ids")
    @patch("temperature_lambda.format_temperature_data")
    @patch("temperature_lambda.all_present_and_hot")
    @patch("temperature_lambda.client.publish")
    def test_temperature_handler_true(self, mock_publish, mock_all_present_and_hot, mock_format_temperature_data, mock_get_device_ids, mock_query_database):
        event = {"example_key": "example_value"}
        context = {}
        device_query = """SELECT DISTINCT measure_value::varchar 
        FROM sensor_data_db."sensor_data_table" 
        WHERE measure_name='device_id'"""
        temperature_query = """SELECT t1.measure_name, t1.time, t1.measure_value::double AS temperature, t2.measure_value::varchar AS device_id
        FROM (
            SELECT measure_name, time, measure_value::double
            FROM sensor_data_db."sensor_data_table"
            WHERE measure_name = 'temperature'
            ORDER BY time DESC
            LIMIT 5
        ) AS t1
        JOIN (
            SELECT measure_name, time, measure_value::varchar
            FROM sensor_data_db."sensor_data_table"
            WHERE measure_name = 'device_id'
        ) AS t2 ON t1.time = t2.time"""
        device_response = "device_response"
        temperature_response = "temperature_response"
        device_ids = ["device1", "device2"]
        temperature_data = "temperature_data"
        
        # Mock data that is being tested
        mock_query_database.side_effect = [device_response, temperature_response]
        mock_get_device_ids.return_value = device_ids
        mock_format_temperature_data.return_value = temperature_data
        mock_all_present_and_hot.return_value = True
        mock_publish.return_value = {}

        response = temperature_handler(event, context)

        # assert that functions were called with correct values and return correct values
        self.assertEqual(response, "opening windows")
        mock_query_database.assert_has_calls([
            unittest.mock.call(device_query),
            unittest.mock.call(temperature_query)
        ])
        mock_get_device_ids.assert_called_once_with(device_response)
        mock_format_temperature_data.assert_called_once_with(temperature_response)
        mock_all_present_and_hot.assert_called_once_with(temperature_data, device_ids)
        mock_publish.assert_called_once_with(
            topic='iot/sensor_data',
            qos=1,
            payload='{"open_windows": true}'
        )
        
    @patch("temperature_lambda.query_database")
    @patch("temperature_lambda.get_device_ids")
    @patch("temperature_lambda.format_temperature_data")
    @patch("temperature_lambda.all_present_and_hot")
    @patch("temperature_lambda.client.publish")
    def test_temperature_handler_false(self, mock_publish, mock_all_present_and_hot, mock_format_temperature_data, mock_get_device_ids, mock_query_database):
        event = {"example_key": "example_value"}
        context = {}
        device_query = """SELECT DISTINCT measure_value::varchar 
        FROM sensor_data_db."sensor_data_table" 
        WHERE measure_name='device_id'"""
        temperature_query = """SELECT t1.measure_name, t1.time, t1.measure_value::double AS temperature, t2.measure_value::varchar AS device_id
        FROM (
            SELECT measure_name, time, measure_value::double
            FROM sensor_data_db."sensor_data_table"
            WHERE measure_name = 'temperature'
            ORDER BY time DESC
            LIMIT 5
        ) AS t1
        JOIN (
            SELECT measure_name, time, measure_value::varchar
            FROM sensor_data_db."sensor_data_table"
            WHERE measure_name = 'device_id'
        ) AS t2 ON t1.time = t2.time"""
        device_response = "device_response"
        temperature_response = "temperature_response"
        device_ids = ["device1", "device2"]
        temperature_data = "temperature_data"
        
        # Mock data that is being tested
        mock_query_database.side_effect = [device_response, temperature_response]
        mock_get_device_ids.return_value = device_ids
        mock_format_temperature_data.return_value = temperature_data
        mock_all_present_and_hot.return_value = False
        mock_publish.return_value = {}

        response = temperature_handler(event, context)

        # assert that functions were called with correct values and return correct values
        self.assertEqual(response, "not opening windows")
        mock_query_database.assert_has_calls([
            unittest.mock.call(device_query),
            unittest.mock.call(temperature_query)
        ])
        mock_get_device_ids.assert_called_once_with(device_response)
        mock_format_temperature_data.assert_called_once_with(temperature_response)
        mock_all_present_and_hot.assert_called_once_with(temperature_data, device_ids)
        mock_publish.assert_called_once_with(
            topic='iot/sensor_data',
            qos=1,
            payload='{"open_windows": false}'
        )

if __name__ == '__main__':
    unittest.main()