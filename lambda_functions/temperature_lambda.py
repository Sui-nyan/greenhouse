import json
import boto3

client = boto3.client('iot-data', region_name='eu-central-1')

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

def query_database(query):
    '''Sends a query to the timestream database.

    Parameters: 
        query (str): The query to be sent to the timestream database.
    
    Returns:
        response (dict): A dictionary containing the response from the timestream query.
    '''
    timestream_client = boto3.client('timestream-query', region_name='eu-central-1')
    response = timestream_client.query(QueryString=query)
    return response
    
def format_temperature_data(temperature_response):
    '''Formats the temperature data retrieved from the query response passed into a dictionary.

    Parameters: 
        temperature_response (dict): A dictionary containing the temperature response from the timestream query.
    
    Returns:
        result (dict): A dictionary containing the formatted temperature data.
    '''
    rows = temperature_response['Rows']
    result = {}
    for i, entry in enumerate(rows):
        measure_name = entry['Data'][0]['ScalarValue']
        timestamp = entry['Data'][1]['ScalarValue']
        temperature = float(entry['Data'][2]['ScalarValue'])
        device_id = entry['Data'][3]['ScalarValue']
    
        result[i] = {
            'measure_name': measure_name,
            'temperature': temperature,
            'device_id': device_id,
            'timestamp': timestamp
        }
    return result
    

def get_device_ids(response):
    '''Takes a response of unique ids and returns a list of unique device IDs.

    Parameters: 
        None
    
    Returns:
        ids (list): A list of unique device IDs.
    '''
    ids = []
    for entry in response['Rows']:
        scalar_value = entry['Data'][0]['ScalarValue']
        ids.append(scalar_value)
    return ids
    
def all_present_and_hot(temperature_data, device_ids):
    '''Checks if all devices are present in the temperature data and have at least one temperature measurement above a threshold.

    Parameters: 
        temperature_data (dict): A dictionary containing the formatted temperature data.
        device_ids (list): A list of device IDs.
    
    Returns:
        all_present (bool): True if all devices are present and have at least one temperature measurement above the threshold, False otherwise.
    '''
    temperature_threshold = 25.0
    all_present = True
    for id in device_ids:
        # check if device id is present in temperature data
        if id not in [entry['device_id'] for entry in temperature_data.values()]:
            all_present = False
            break
        # check if at least one temperature value for device id is above threshold
        if not any(entry['temperature'] > temperature_threshold for entry in temperature_data.values() if entry['device_id'] == id):
            all_present = False
            break
    return all_present

def temperature_handler(event, context):
    '''Handles the temperature data and publishes a message to the IoT topic based on the analysis.

    Parameters: 
        event: The event data passed to the Lambda function.
        context: The runtime information of the Lambda function.
    
    Returns:
        str: A string indicating whether windows should be opened or not.
    '''
    device_response = query_database(device_query)
    temperature_response = query_database(temperature_query)

    device_ids = get_device_ids(device_response)
    temperature_data = format_temperature_data(temperature_response)
    if all_present_and_hot(temperature_data, device_ids):
        data = {"open_windows": True}
        response = client.publish(
            topic='iot/sensor_data',
            qos=1,
            payload=json.dumps(data)
        )
        return 'opening windows'
    else:
        data = {"open_windows": False}
        response = client.publish(
            topic='iot/sensor_data',
            qos=1,
            payload=json.dumps(data)
        )
        return 'not opening windows'
    