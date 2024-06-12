resource "awscc_iotevents_input" "window_input" {
  input_definition = {
    attributes = [{
      json_path = "open_windows"
      },
      {
        json_path = "temperature"
    }]
  }
  input_name = "window_input"
}

resource "awscc_iotevents_input" "light_input" {
  input_definition = {
    attributes = [{
      json_path = "need_light"
      },
      {
        json_path = "light"
    }]
  }
  input_name = "light_input"
}

resource "awscc_iotevents_input" "sprinkler_input" {
  input_definition = {
    attributes = [{
      json_path = "humidity"
    }]
  }
  input_name = "sprinkler_input"
}

resource "awscc_iotevents_detector_model" "window" {
  detector_model_name        = "window_events"
  detector_model_description = "monitors and changes the state of the windows, created with terraform"
  evaluation_method          = "SERIAL"
  role_arn                   = aws_iam_role.core_role.arn

  detector_model_definition = {
    states = [
      {
        state_name = "windows_closed"
        on_input = {
          events = [
            {
              event_name = "input_windows_closed_state",
              condition  = "$input.window_input.temperature",
              actions = [
                {
                  lambda = {
                    function_arn = aws_lambda_function.temperature_lambda.arn
                  }
                }
              ]
            }
          ]
          transition_events = [
            {
              event_name = "open_windows"
              condition  = "$input.window_input.open_windows == true"
              actions    = []
              next_state = "windows_open"
            }
          ]
        }
        on_enter = {
          events = [{
            event_name = "enter_windows_closed_state",
            condition  = "$input.window_input.temperature",
            actions = [
              {
                iot_topic_publish = {
                  mqtt_topic = "iot/actor_data"
                  payload = {
                    content_expression = "\"{\\\"state\\\": \\\"windows_closed\\\"}\"",
                    type               = "JSON"
                  }
                }
              }
            ]
            }
          ]
        }
        on_exit = {
          events = []
        }
      },
      {
        state_name = "windows_open"
        on_input = {
          events = [
            {
              event_name = "input_windows_open_state",
              condition  = true,
              actions = [
                {
                  lambda = {
                    function_arn = aws_lambda_function.temperature_lambda.arn
                  }
                }
              ]
            }
          ]
          transition_events = [
            {
              event_name = "close_windows"
              condition  = "$input.window_input.open_windows == false"
              actions    = []
              next_state = "windows_closed"
            }
          ]
        }
        on_enter = {
          events = [{
            event_name = "enter_windows_open_state",
            condition  = "true",
            actions = [
              {
                iot_topic_publish = {
                  mqtt_topic = "iot/actor_data"
                  payload = {
                    content_expression = "\"{\\\"state\\\": \\\"windows_open\\\"}\"",
                    type               = "JSON"
                  }
                }

              }
            ]
          }]
        }
        on_exit = {
          events = []
        }
      }
    ]
    initial_state_name = "windows_closed"
  }
}



resource "awscc_iotevents_detector_model" "light" {
  detector_model_name        = "light_events"
  detector_model_description = "determines if lights need to be on or off, created with terraform"
  evaluation_method          = "SERIAL"
  role_arn                   = aws_iam_role.core_role.arn

  detector_model_definition = {
    states = [
      {
        state_name = "lights_off",
        on_input = {
          events = [
            {
              event_name = "input_light_off_state",
              condition  = "$input.light_input.light < 60",
              actions = [
                {
                  lambda = {
                    function_arn = aws_lambda_function.light_lambda.arn
                  }
                }
              ]
            }
          ],
          transition_events = [
            {
              event_name = "turn_on",
              condition  = "$input.light_input.need_need_light == true",
              actions    = [],
              next_state = "lights_on"
            }
          ]
        },
        on_enter = {
          events = [
            {
              event_name = "enter_lights_off_state",
              condition  = "true",
              actions = [
                {
                  iot_topic_publish = {
                    mqtt_topic = "iot/actor_data",
                    payload = {
                      content_expression = "\"{\\\"state\\\": \\\"light_turned_off\\\"}\"",
                      type               = "JSON"
                    }
                  }
                }
              ]
            }
          ]
        },
        on_exit = {
          events = []
        }
      },
      {
        state_name = "lights_on",
        on_input = {
          events = [
            {
              event_name = "input_light_on_state",
              condition  = "$input.light_input.light < 60",
              actions = [
                {
                  lambda = {
                    function_arn = aws_lambda_function.light_lambda.arn
                  }
                }
              ]
            }
          ],
          transition_events = [
            {
              event_name = "turn_off",
              condition  = "$input.light_input.need_need_light == false",
              actions    = [],
              next_state = "lights_off"
            }
          ]
        },
        on_enter = {
          events = [
            {
              event_name = "enter_lights_off_state",
              condition  = "true",
              actions = [
                {
                  iot_topic_publish = {
                    mqtt_topic = "iot/actor_data",
                    payload = {
                      content_expression = "\"{\\\"state\\\": \\\"light_turned_on\\\"}\"",
                      type               = "JSON"
                    }
                  }
                }
              ]
            }
          ]
        },
        on_exit = {
          events = []
        }
      }
    ]
    initial_state_name = "lights_off"
  }
}

resource "awscc_iotevents_detector_model" "sprinkler" {
  detector_model_name        = "sprinkler_events"
  detector_model_description = "Starts and stops the sprinklers based on humidity, created with terraform"
  evaluation_method          = "SERIAL"
  role_arn                   = aws_iam_role.core_role.arn

  detector_model_definition = {
    states = [
      {
        state_name = "sprinklers_off"
        on_input = {
          events = []
          transition_events = [
            {
              event_name = "start_sprinklers"
              condition  = "$input.sprinkler_input.humidity < 20"
              actions    = []
              next_state = "sprinklers_on"
            }
          ]
        }
        on_enter = {
          events = [{
            event_name = "enter_sprinklers_off_state"
            condition  = "true"
            actions = [
              {
                iot_topic_publish = {
                  mqtt_topic = "iot/actor_data"
                  payload = {
                    content_expression = "\"{\\\"state\\\": \\\"sprinklers_off\\\"}\"",
                    type               = "JSON"
                  }
                }
              }
            ]
          }]
        }
        on_exit = {
          events = []
        }
      },
      {
        state_name = "sprinklers_on"
        on_input = {
          events = []
          transition_events = [
            {
              event_name = "stop_sprinklers"
              condition  = "$input.sprinkler_input.humidity >= 20"
              actions    = []
              next_state = "sprinklers_off"
            }
          ]
        }
        on_enter = {
          events = [{
            event_name = "enter_sprinklers_on_state",
            condition  = "true",
            actions = [
              {
                iot_topic_publish = {
                  mqtt_topic = "iot/actor_data"
                  payload = {
                    content_expression = "\"{\\\"state\\\": \\\"sprinklers_on\\\"}\"",
                    type               = "JSON"
                  }
                }
              }
            ]
          }]
        }
        on_exit = {
          events = []
        }
      }
    ]
    initial_state_name = "sprinklers_off"
  }
}