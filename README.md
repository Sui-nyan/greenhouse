# Preface
Latest snapshot of school project HdM

(16 July 2023)


# Greenhouse

This is an Internet of Things project which should manage a grennhouse while using the cloud services from AWS. 

The project utilizes IoT sensors to gather real-time data parameters such as temperature, humidity and light intensity. This data is then transmitted to a cloud service, where it is monitored and processed. Afterwards it's sent to different actors which turn on or off based on the message. 

## Table of Contents
- [Greenhouse](#greenhouse)
  - [Table of Contents](#table-of-contents)
  - [Setup](#setup)
    - [Device Code Setup](#device-code-setup)
    - [Terraform Setup](#terraform-setup)
    - [Terraform State Management with GitLab](#terraform-state-management-with-gitlab)
  - [Run](#run)
  - [Additional Notes](#additional-notes)
    - [How it works](#how-it-works)
- [Code Guidelines](#code-guidelines)
  - [Python](#python)
  - [Terraform](#terraform)
- [Contributors](#contributors)

## Setup
First, the project is using the Pico Enviro+ module with the firmware from the following [link](https://gitlab.mi.hdm-stuttgart.de/iotee/firmware/-/packages).
To install the firmware, you need to connect your device to your pc while holding down the reset button on the back of the case. This will open the file explorer. Now you can upload the firmware (.uf2 file) to the module.

### Device Code Setup
To add the python packages for the project you can run `pip install -r ./client/requirements.txt`. 

### Terraform Setup
Create a `terraform.tfvars` file in the terraform directory and insert the following code:
```terraform    
aws_access_key = ""
aws_secret_key = ""
```
and populate the fields with the access and secret key of your AWS account.
Alternatively you can enter your keys in the terminal when running terraform apply.

### Terraform State Management with GitLab
We utilize GitLab's Terraform state backend to manage and store the state of our infrastructure. Follow the instructions that can be read [here](https://docs.gitlab.com/ee/user/infrastructure/iac/terraform_state.html). To use the GitLab Terraform state backend, it requires the use of a GitLab Personal Access Token. 

You can create a token by following the instructions [here](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#creating-a-personal-access-token). The token needs to have the `api` scope.

Once you have your Personal Access Token, you're ready to initialize your Terraform configuration with the GitLab backend. You can find and copy the init command from the GitLab repository Terraform state page under Infrastructure > Terraform states.

## Run
To set up the AWS cloud infrastructure you can run 
```bash
terraform -chdir=terraform/ init
terraform -chdir=terraform/ apply
```
This will create the necessary resources in AWS and add the certificates for the MQTT connection.

Now when you run 
```bash
python ./client/receiver.py
python ./client/publisher.py
```

The `publisher.py` file will read the sensors of a device and sends the data to the cloud. <br>
If there is the need to send prepared data you may use the `BUTTON_MODE`. This disables the automated sending of data and sends data via press of the different buttons. 

The `receiver.py` code uses the data it receives to trigger various actions on a device.

To setup multiple different devices, change the value for `DEVICE_ID` to different values from the other connected publishing devices. If you want to achiev this on a single PC simply run the first publisher. Then change the values and start it again in a different terminal. (The temperature detector model is able to use this functionality)

## Additional Notes
The project presentations files, which include the architecture diagram and data-flow diagram can be found in the [GitLab Wiki](https://gitlab.mi.hdm-stuttgart.de/csiot/ss23/greenhouse/-/wikis/home).

### How it works
Data is beeing sent on the tpic iot/sensor_data.<br>
There are 3 detector models that are responsible for handling the data to open the windows, turn on the lights and to start the spinklers. 

- window_events: on each input, starts a lambda function that looks into the timestreamfor the day and gets all devices that have published that day. Then gets with a join sql query the five latest timestram entries regarding temperature and the device id and checks if each device id is present with a temperature over 25°C. Depending on the result it sends a message to the iot/sensor_data topic with a special message which can trigger the state transotion.
- light_events: on each input with a light level above 60 or below 60, start a lambda function which gets each light entry in the timestream which is above the threshold and the one after that. It then calculates the total duration of light beeing above the threshold and if it doesn't exceed 8 hours and if it's past 18 o'clock then the light will be turned on. Depending on the result it sends a message to the iot/sensor_data topic with a special message which can trigger the state transotion.
- sprinkler_events: It simply transitions to the next state if the value for the humidity is above 20 or below 20. 

All the states of the models have an on enter event, which sends a message to the iot/actor_data topic. This is being picked up by the gateway (receiver.py) and activates different things based on the message. <br>

# Code Guidelines

## Python	
- Variables and Functions should use snake_case format.
- Use inline comments when needed
- Always use docstrings to describe the purpose of each function

## Terraform
- Use `Terraform fmt` to format your code
- Use `Terraform validate` to validate your code
- Variables should use the snake_case format
- Add all required providers in the main.tf
- Each .tf file should be as small as possible and contain related resources, grouped logically

# Contributors
- Anjo Weddewer (aw181, 41486)
- Antti Kuivaleinen (ak366, 5010497)
- Elisa Zhang (ez018, 40972)
- Firaz Ilhan (fi007, 40032)
- Isaac Morales (im050, 44904)
- Johannes Rödel (jr125, 41959)