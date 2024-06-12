from time import sleep
import json
import signal
import sys
import time
from utils import connect_to_mqtt, start_iotee
import ssl
import time

#the try is needed to have both the scripts and tests working
try:
    from utils import connect_to_mqtt, start_iotee
except ModuleNotFoundError:
    from client.utils import connect_to_mqtt, start_iotee

#define your device as you wish, you may enable `BUTTON_MODE` to debug your code
BUTTON_MODE = True
COM_PORT = "COM7"
DEVICE_ID = "002"

def signal_handler(signal: int, frame: object, iotee: object):
    '''Handler function that stops the iotee thread on ctrl+c
    
    Parameters:
        signal (int): signal number
        frame (frame): current stack frame
        iothee (Iotee): iotee object
        
    Returns:
        None
    '''
    print('Shutting down')
    iotee.stop()
    sys.exit(0)

# callback functions for mqtt
def on_connect(client: object, userdata: any, flags: dict, response_code: int):
    '''Callback function on connectingto a broker, prints if connection was successful
    
    Parameters:
        client (Client): mqtt client object
        userdata (Any): userdata
        flags (dict): flags
        response_code (int): response code
        
    Returns:
        None
    '''
    if response_code == 0:
        print('Connected with status: {0}'.format(response_code))
    else:
        print('Connection failed with status: {0}'.format(response_code))

def on_publish(client: object, userdata: any, mid: int):
    '''Callback function on publishing a message, 
    prints the message id
    
    Parameters:
        client (Client): mqtt client object
        userdata (Any): userdata
        mid (int): message id
        
    Returns:
        None
    '''
    print('message number:', mid)


# message template
data = {
    "device_id" : DEVICE_ID,
    "timestamp": 0.0,
    "inputName": "sensorData",
    "pressure": 0.0,
    "temperature": 0.0,
    "humidity": 0.0,
    "light": 0.0,
    "proximity": 0.0
}


# callback functions for iotee
def on_temperature(value):
    '''Callback function on receiving a temperature value, 
    reads the value and stores it in a global dictionary called data
    
    Parameters:
        value (float): temperature value
        
    Returns:
        None
    '''
    data['temperature'] = value
    print('temperature: {:.2f}'.format(value))

def on_humidity(value):
    '''Callback function on receiving a humidity value, 
    reads the value and stores it in a global dictionary called data
    
    Parameters:
        value (float): humidity value
        
    Returns:
        None
    '''
    data['humidity'] = value
    print('humidity: {:.2f}'.format(value))

def on_light(value):
    '''Callback function on receiving a light value, 
    reads the value and stores it in a global dictionary called data
    
    Parameters:
        value (float): light value
        
    Returns:
        None
    '''
    data['light'] = value
    print('light: {:.2f}'.format(value))

def on_proximity(value):
    '''Callback function on receiving a proximity value, 
    reads the value and stores it in a global dictionary called data
    
    Parameters:
        value (float): proximity value
        
    Returns:
        None
    '''
    data['proximity'] = value
    print('proximity: {:.2f}'.format(value))

def on_button_pressed(button):
    '''
    
    Parameters:
        button (str): button on the iotee device that was pressed. Can be 'A', 'B', 'X', 'Y'
        
    Returns:
        None
    '''
    global ran
    if button == 'A':
        data['temperature'] = 30.0  # >25
    elif button == 'B':
        data['temperature'] = 20.0  # <=25
    elif button == 'X':
        data['humidity'] = 10.0  # < 20
    elif button == 'Y':
        data['humidity'] = 30.0  # >= 20
    print(f'Button press data for Button {button}: {data}' )
    ran = True


# gets the sensor data from the connected devive on COM_port through callback functions
def request_sensor_data(iotee):
    '''Requests sensor data from the iotee device and adds a timestamp to a global dictionary called data. 
    Each request stores the value of the sensor in a global dictionary called data. 
    
    Parameters:
        iotee (Iotee): iotee object
        
    Returns:
        None 
    '''
    timestamp = int(time.time())
    print('\n')
    print('time of getting data:', timestamp)
    data['timestamp'] = timestamp
    iotee.request_temperature()
    iotee.request_humidity()
    iotee.request_light()
    iotee.request_proximity()


ran = False
# main loop for sending data
def main(button_mode):
    '''Main loop that starts the iotee thread, connects to the mqtt broker and sends data on a specific topic
    
    Parameters:
        button_mode (bool): a boolean that indicates it the main loop should listen to button presses or send actual 
                            data autmatically
                            
    Returns:
        None
    '''
    global ran
    iotee = start_iotee(COM_PORT) # manually change the COM Port if you have multiple devices
    signal.signal(signal.SIGINT, lambda signal, frame: signal_handler(signal, frame, iotee))

    iotee.on_temperature = on_temperature
    iotee.on_humidity = on_humidity
    iotee.on_light = on_light
    iotee.on_proximity = on_proximity
    iotee.on_button_pressed = on_button_pressed

    client = connect_to_mqtt()
    client.on_connect = on_connect
    client.on_publish = on_publish

    while True:
        try:
            if button_mode == False:
                request_sensor_data(iotee)
                sleep(1)
                client.publish('iot/sensor_data', payload=json.dumps(data), qos=1)
                sleep(4)
            else:
                if ran == True:
                    client.publish('iot/sensor_data', payload=json.dumps(data), qos=1)
                    ran = False
                sleep(1)
        except ssl.SSLEOFError as e:
            print('SSL error occurred:', e)
            print('Attempting to reconnect')
            client.reconnect()
        except Exception as e:
            print('An error occurred:', e)


if __name__ == '__main__':
    '''Starts the main loop'''
    main(button_mode=BUTTON_MODE)
