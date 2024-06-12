from datetime import datetime
from zoneinfo import ZoneInfo
import json
import unittest
from unittest.mock import patch, MagicMock, Mock

#the try is needed to have both the scripts and tests working
try:
    import light_lambda 
except ModuleNotFoundError:
    from lambda_functions import light_lambda
    
class TestLambdaFunctions(unittest.TestCase):
    @patch("boto3.client")
    def test_query_database_equals(self, mock_client):
        mock_timestream = MagicMock()
        mock_client.return_value = mock_timestream
        query = """
           asfdgasdf
        """
        mock_timestream.query.return_value = "mocked response"

        actual_response = light_lambda.query_database(query)

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

        actual_response = light_lambda.query_database(query)

        mock_timestream.query.assert_called_once_with(QueryString=query)
        self.assertNotEqual(actual_response, "something else")
    
    @patch("light_lambda.query_database")
    def test_get_sunlight_duration_7200(self, mock_query):
        mock_query.return_value = {
            "Rows": [
                {
                    "Data": [
                        {"ScalarValue": "60.1"},
                        {"ScalarValue": "2023-06-30 14:00:00.000000"},
                        {"ScalarValue": "2023-06-30 15:00:00.000000"},
                    ]
                },
                {
                    "Data": [
                        {"ScalarValue": "65.0"},
                        {"ScalarValue": "2023-06-30 16:00:00.000000"},
                        {"ScalarValue": "2023-06-30 17:00:00.000000"},
                    ]
                },
            ]
        }
        response = light_lambda.get_sunlight_duration(mock_query.return_value)
        self.assertEqual(response, 7200)
        self.assertNotEqual(response, 28800)
    
    @patch("light_lambda.query_database")
    def test_get_sunlight_duration_28800(self, mock_query):
        mock_query.return_value = {
            "Rows": [
                {
                    "Data": [
                        {"ScalarValue": "65.0"},
                        {"ScalarValue": "2023-06-30 08:00:00.000000"},
                        {"ScalarValue": "2023-06-30 10:00:00.000000"},
                    ]
                },
                {
                    "Data": [
                        {"ScalarValue": "80.0"},
                        {"ScalarValue": "2023-06-30 10:00:00.000000"},
                        {"ScalarValue": "2023-06-30 12:00:00.000000"},
                    ]
                },
                {
                    "Data": [
                        {"ScalarValue": "65.0"},
                        {"ScalarValue": "2023-06-30 12:00:00.000000"},
                        {"ScalarValue": "2023-06-30 14:00:00.000000"},
                    ]
                },
                {
                    "Data": [
                        {"ScalarValue": "65.0"},
                        {"ScalarValue": "2023-06-30 14:00:00.000000"},
                        {"ScalarValue": "2023-06-30 16:00:00.000000"},
                    ]
                },
            ]
        }
        response = light_lambda.get_sunlight_duration(mock_query.return_value)
        self.assertEqual(response, 28800)
        self.assertNotEqual(response, 7200)

    @patch("light_lambda.client.publish")
    def test_evaluate_if_light_not_equals(self, mock_publish):
        mock_publish.return_value = {}
        test_cases = [
            (30000, "doesn't need light", False),
            (20000, "needs light", True),
        ]

        for duration, expected_response, need_light in test_cases:
            with self.subTest(duration=duration):
                response = light_lambda.evaluate_if_light(duration, {"example": "message"})
                self.assertEqual(response, expected_response)
                mock_publish.assert_called_once_with(
                    topic="iot/sensor_data",
                    qos=1,
                    payload=json.dumps(
                        {"need_light": need_light}
                    ),
                )
                mock_publish.reset_mock()
    
    @patch("light_lambda.query_database")
    @patch("light_lambda.get_sunlight_duration")
    @patch("light_lambda.evaluate_if_light")
    @patch.object(light_lambda, 'datetime', Mock(wraps=datetime))
    def test_light_handler_after_6_summertime(self, mock_evaluate_if_light, mock_get_sunlight_duration, mock_query_database):
        event = {"example_key": "example_value"}
        context = {}

        target_time = light_lambda.time(18, 0)
        with patch("light_lambda.time", return_value=target_time) as mock_time:
            light_lambda.datetime.now.return_value = datetime(2023, 7, 16, 19, 0, tzinfo=ZoneInfo('UTC'))  # Set current time to 21:00 german time (summertime)
            response = light_lambda.light_handler(event, context)

        self.assertEqual(response, "after 6")
        
        mock_query_database.assert_called_once()
        mock_get_sunlight_duration.assert_called_once()
        mock_evaluate_if_light.assert_called_once()

    @patch("light_lambda.query_database")
    @patch("light_lambda.get_sunlight_duration")
    @patch("light_lambda.evaluate_if_light")
    @patch.object(light_lambda, 'datetime', Mock(wraps=datetime))
    def test_light_handler_not_after_6_summertime(self, mock_query_database, mock_get_sunlight_duration, mock_evaluate_if_light):
        event = {"example_key": "example_value"}
        context = {}

        target_time = light_lambda.time(18, 0)
        
        with patch("light_lambda.time", return_value=target_time) as mock_time:
            light_lambda.datetime.now.return_value = datetime(2023, 7, 16, 16, 0, tzinfo=ZoneInfo('UTC'))  # Set current time to 18:00 german time (summertime)
            response = light_lambda.light_handler(event, context)
            
        self.assertEqual(response, "not after 6")
        
    @patch("light_lambda.query_database")
    @patch("light_lambda.get_sunlight_duration")
    @patch("light_lambda.evaluate_if_light")
    @patch.object(light_lambda, 'datetime', Mock(wraps=datetime))
    def test_light_handler_after_6_wintertime(self, mock_evaluate_if_light, mock_get_sunlight_duration, mock_query_database):
        event = {"example_key": "example_value"}
        context = {}

        target_time = light_lambda.time(18, 0)
        with patch("light_lambda.time", return_value=target_time) as mock_time:
            light_lambda.datetime.now.return_value = datetime(2023, 1, 1, 19, 0, tzinfo=ZoneInfo('UTC'))  # Set current time to 20:00 german time (summertime)
            response = light_lambda.light_handler(event, context)

        self.assertEqual(response, "after 6")
        
        mock_query_database.assert_called_once()
        mock_get_sunlight_duration.assert_called_once()
        mock_evaluate_if_light.assert_called_once()

    @patch("light_lambda.query_database")
    @patch("light_lambda.get_sunlight_duration")
    @patch("light_lambda.evaluate_if_light")
    @patch.object(light_lambda, 'datetime', Mock(wraps=datetime))
    def test_light_handler_not_after_6_wintertime(self, mock_query_database, mock_get_sunlight_duration, mock_evaluate_if_light):
        event = {"example_key": "example_value"}
        context = {}

        target_time = light_lambda.time(18, 0)
        
        with patch("light_lambda.time", return_value=target_time) as mock_time:
            light_lambda.datetime.now.return_value = datetime(2023, 1, 1, 16, 0, tzinfo=ZoneInfo('UTC'))  # Set current time to 17:00 german time (summertime)
            response = light_lambda.light_handler(event, context)
            
        self.assertEqual(response, "not after 6")

if __name__ == "__main__":
    unittest.main()
