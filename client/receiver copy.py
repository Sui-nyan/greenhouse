import json
import sys
import signal
from functools import partial

#the try is needed to have both the scripts and tests working
try:
    from utils import connect_to_mqtt, subscribe_to, start_iotee
except ModuleNotFoundError:
    from client.utils import connect_to_mqtt, subscribe_to, start_iotee


COM_PORT = "COM3"

def signal_handler(signal:int, frame: object, iotee: object):
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

def on_message(iotee: object, client: object, userdata: any, message: object):
    '''Callback function on receiving a message, 
    parses the message in a json format, and then determines based on the value of state 
    what message to display on the iotee device
    
    Parameters:
        iotee (Iotee): iotee object
        client (Client): mqtt client object
        userdata (Any): userdata
        message (Message): MQTTMessage object, containing payload, topic, qos, retain
    
    Returns: 
        None
    '''
    message = json.loads(message.payload.decode())
    if message['state'] == 'sprinklers_on':
        iotee.set_led(255, 0, 0) #red
        text = 'Sprinklers \nare on'
        display_text(iotee, text)
        print('Sprinklers are on')

    elif message['state'] == 'sprinklers_off':
        iotee.set_led(0, 255, 0) #green
        text = 'Sprinklers \nare off'
        display_text(iotee, text)
        print('Sprinklers are off')

    elif message['state'] == 'windows_closed':
        iotee.set_led(0, 0, 255) #blue
        text = 'Windows \nare closed'
        display_text(iotee, text)
        print('Windows are closed')

    elif message['state'] == 'windows_open':
        iotee.set_led(255, 255, 0) #yellow
        text = 'Windows \nare open'
        display_text(iotee, text)
        print('Windows are open')

    elif message['state'] == 'lights_on':
        iotee.set_led(0, 255, 255) #cyan
        text = 'Lights \nare on'
        display_text(iotee, text)
        print('Lights are on')

    elif message['state'] == 'lights_off':
        iotee.set_led(255, 0, 255) #purple
        text = 'Lights \nare off'
        display_text(iotee, text)
        print('Lights are off')


def process_text(text: str):
    '''Appends a new string to a string list called old_texts, and returns a new string of the 3 newest appended 
    elements
    
    Parameters:
        text (str): a text to be appended to old_texts
    
    Returns:
        new_text (str): a text seperated by \n of the 3 newest appended texts to old_texts
    '''
    global old_texts
    old_texts.append(text)
    # only keep the 3 newest appended texts if bigger than 3
    if len(old_texts) > 3:
        old_texts = old_texts[-3:]
    # create a new text of 3 elements from old_texts, separated by \n
    new_text = ''
    for old_text in reversed(old_texts):
        new_text += f'{old_text}\n'
    return new_text

def display_text(iotee: object, text: str):
    '''Displays a formatted version of the text on the iotee device
    
    Parameters:
        iotee (Iotee): iotee object
        text (str): text to be displayed on the iotee device
    
    Returns:
        None
    '''
    text = process_text(text)
    iotee.set_display(text)

old_texts = []

#main loop for receiving data
def main():
    '''Main loop that starts the iotee thread, connects to the mqtt broker, and subscribes to the topics'''
    iotee = start_iotee(COM_PORT)
    signal.signal(signal.SIGINT, lambda signal, frame: signal_handler(signal, frame, iotee))

    client = connect_to_mqtt()
    
    client.on_connect = on_connect
    client.on_message = partial(on_message, iotee)

    subscribe_to(client, ['iot/error', 'iot/actor_data'], 1)
    client.loop_forever()
    
    
if __name__ == '__main__':
    '''Starts the main loop'''
    main()
