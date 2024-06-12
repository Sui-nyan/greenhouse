import json
import unittest
from unittest.mock import patch

#the try is needed to have both the scripts and tests working
try:
    import light_lambda
except ModuleNotFoundError:
    from lambda_functions import light_lambda

class TestLambdaFunctions(unittest.TestCase):
    def setUp(self):
        self.message = {"example": "message"}
        self.mock_data = {
            "Rows": [
                {
                    "Data": [
                        {"ScalarValue": "60"},
                        {"ScalarValue": "2023-06-30 16:00:00.000000"},
                        {"ScalarValue": "2023-06-30 17:00:00.000000"},
                    ]
                },
                {
                    "Data": [
                        {"ScalarValue": "65"},
                        {"ScalarValue": "2023-06-30 18:00:00.000000"},
                        {"ScalarValue": "2023-06-30 19:00:00.000000"},
                    ]
                },
            ]
        }

    @patch("light_lambda.timestream_client.query")
    def test_get_sunlight_duration(self, mock_query):
        mock_query.return_value = self.mock_data
        response = light_lambda.get_sunlight_duration(mock_query.return_value)
        self.assertEqual(response, 7200)

    @patch("light_lambda.client.publish")
    def test_evaluate_if_light(self, mock_publish):
        mock_publish.return_value = {}
        test_cases = [
            (30000, "doesn't need light", False),
            (20000, "needs light", True),
        ]

        for duration, expected_response, need_light in test_cases:
            with self.subTest(duration=duration):
                response = light_lambda.evaluate_if_light(duration, self.message)
                self.assertEqual(response, expected_response)
                mock_publish.assert_called_once_with(
                    topic="iot/sensor_data",
                    qos=1,
                    payload=json.dumps(
                        {"example": "message", "need_light": need_light}
                    ),
                )
                mock_publish.reset_mock()


if __name__ == "__main__":
    unittest.main()
