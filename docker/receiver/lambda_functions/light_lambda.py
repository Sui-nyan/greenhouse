import json
import boto3
from datetime import datetime, time
from dateutil import tz

client = boto3.client('iot-data', region_name='eu-central-1')
timestream_client = boto3.client('timestream-query', region_name='eu-central-1')

def get_light_data():
    '''Sends a query to the timestream database gathering all light data from today which value is above 60 and the time
    from the next row
    
    Parameters: 
        None
    
    Returns:
        response (dict): a dictionary containing the response from the timestream query
    '''
    query = """
        WITH light_above_threshold AS (
            SELECT time, measure_value::double
            FROM sensor_data_db.sensor_data_table
            WHERE measure_name = 'light'
                AND time >= DATE_TRUNC('day', NOW())
        ),
        all_rows AS (
            SELECT measure_value::double, time,
                LEAD(time) OVER (ORDER BY time ASC) AS next_time,
                ROW_NUMBER() OVER (ORDER BY time ASC) AS row_number
            FROM light_above_threshold
        )
        SELECT measure_value::double, time, next_time
        FROM all_rows
        WHERE measure_value::double > 60
    """

    response = timestream_client.query(QueryString=query)
    return response

def get_sunlight_duration(response: dict):
    '''Iterates the response dictionary and adds the duration between a row which is over the threshold of light 
    exposure and the next row to a total duration
    
    Parameters:
        response (dict): a dictionary containing the response from the timestream query
    
    Returns:
        total_sunlight_duration (int): the total duration of sunlight of the day in seconds
    '''
    rows = response['Rows']
    total_sunlight_duration = 0
    for row in rows:
        row_time = row['Data'][1]['ScalarValue'][:-3]
        next_time = row['Data'][2]['ScalarValue'][:-3] if 'ScalarValue' in row['Data'][2] else None
        
        row_time = datetime.strptime(row_time, '%Y-%m-%d %H:%M:%S.%f')
        next_time = datetime.strptime(next_time, '%Y-%m-%d %H:%M:%S.%f')
        
        duration = next_time - row_time
        duration = round(duration.total_seconds())
        
        total_sunlight_duration = total_sunlight_duration + duration
    return total_sunlight_duration

def evaluate_if_light(total_sunlight_duration: int, message: dict):
    '''Compares the total duration of sunlight of the day with a minimum exposure of sunlight for a day and publishes
    a message to the broker with a message if the plant needs light or not. The message is beeing sent to the topic
    'iot/sensor_data' so it gets picked up by the IoT events Detector Model which looks for the message 'need_light'
    to transition to the next state
    
    Parameters:
        total_sunlight_duration (int): the total duration of sunlight of the day in seconds
        message (dict): a dictionary containing the message from the iotee device
        
    Returns:
        text (str): a string containing the message to be sent to the iotee device
    '''
    if total_sunlight_duration > 28800:
        data = {"need_light": False}
        response = client.publish(
            topic='iot/sensor_data',
            qos=1,
            payload=json.dumps(data)
        )
        return "doesn't need light"
    else:
        data = {"need_light": True}
        response = client.publish(
            topic='iot/sensor_data',
            qos=1,
            payload=json.dumps(data)
        )
        return 'needs light'

def light_handler(event, context):
    '''
    Parameters:
        event (dict): a dictionary containing the message from the iotee device
        context (dict): a dictionary containing the context of the lambda function
        
    Returns:
        text (str): a string containing the message to be sent to the iotee device
    '''
    message = event
    
    # get current german time
    utc_time = datetime.utcnow()
    source_tz = tz.gettz('UTC')
    target_tz = tz.gettz('Europe/Berlin')
    current_time = utc_time.replace(tzinfo=source_tz).astimezone(target_tz).time()
    
    target_time = time(18, 0)
    
    # checks if the current time is after 19 o'clock and prusumuably the sun is not giving enough light anymore
    # the detector model only runs this lambda if current light < 60. 
    # thus no checks for that are needed
    if current_time > target_time:
        response = get_light_data()
        total_sunlight_duration = get_sunlight_duration(response)
        evaluate_if_light(total_sunlight_duration, message)
        return "after 6"
    else:
        return "not after 6"
