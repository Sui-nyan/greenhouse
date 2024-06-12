import json
import unittest
from unittest.mock import Mock, patch


#the try is needed to have the tests work locally and in the pipeline
try:
    from client import receiver
except ModuleNotFoundError:
    import receiver


class TestOnMessage(unittest.TestCase):
    def setUp(self):
        self.iotee_mock = Mock()
        self.client_mock = Mock()
        self.userdata_mock = Mock()
        self.msg_mock = Mock()

    def message_test_helper(self, state, led_args):
        self.msg_mock.payload = json.dumps({"state": state}).encode()

        try:
            with patch("client.receiver.display_text") as display_text_mock:
                receiver.on_message(
                    self.iotee_mock, self.client_mock, self.userdata_mock, self.msg_mock
                )
        except:
            with patch("receiver.display_text") as display_text_mock:
                receiver.on_message(
                    self.iotee_mock, self.client_mock, self.userdata_mock, self.msg_mock
                )

        self.iotee_mock.set_led.assert_called_with(*led_args)
        display_text_mock.assert_called()

    def test_sprinklers_on(self):
        self.message_test_helper("sprinklers_on", (255, 0, 0))

    def test_sprinklers_off(self):
        self.message_test_helper("sprinklers_off", (0, 255, 0))

    def test_windows_closed(self):
        self.message_test_helper("windows_closed", (0, 0, 255))

    def test_windows_open(self):
        self.message_test_helper("windows_open", (255, 255, 0))

    def test_lights_on(self):
        self.message_test_helper("lights_on", (0, 255, 255))

    def test_lights_off(self):
        self.message_test_helper("lights_off", (255, 0, 255))


if __name__ == "__main__":
    unittest.main()
