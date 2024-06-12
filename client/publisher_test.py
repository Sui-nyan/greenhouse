import unittest
from unittest.mock import MagicMock, patch

#the try is needed to have the tests work locally and in the pipeline
try:
    import publisher
except ModuleNotFoundError:
    from client import publisher


class PublisherTest(unittest.TestCase):
    def setUp(self):
        self.button_press_tests = {
            "A": ("temperature", 30),
            "B": ("temperature", 20),
            "X": ("humidity", 10),
            "Y": ("humidity", 30),
        }

    def test_on_button_pressed(self):
        with patch("builtins.print"):
            for button, (attribute, expected_value) in self.button_press_tests.items():
                with self.subTest(button=button):
                    publisher.on_button_pressed(button)
                    self.assertEqual(publisher.data[attribute], expected_value)

    def test_sensor_callbacks(self):
        callback_tests = {
            "on_temperature": (42.5, "temperature"),
            "on_humidity": (15.2, "humidity"),
            "on_light": (1000, "light"),
            "on_proximity": (5, "proximity"),
        }
        for method, (value, attribute) in callback_tests.items():
            with self.subTest(method=method):
                getattr(publisher, method)(value)
                self.assertEqual(publisher.data[attribute], value)


    def test_request_sensor_data(self):
        iotee = MagicMock()
        with patch("time.time", return_value=12345):
            publisher.request_sensor_data(iotee)
        self.assertEqual(publisher.data["timestamp"], 12345)
        iotee.request_temperature.assert_called_once()
        iotee.request_humidity.assert_called_once()
        iotee.request_light.assert_called_once()
        iotee.request_proximity.assert_called_once()


if __name__ == "__main__":
    unittest.main()
