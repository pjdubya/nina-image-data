# nina-image-data

## Description

Astrophotography images captured with NINA generally remain locally captured on the device where NINA is running, e.g. a mini PC at the capture site. For users who wish to monitor the progress of their imaging session remotely, they may use RDC to view the progress of NINA throughout the night. This project helps users who are running Home Assistant to retrieve thumbnail versions of their stretched images and display them in a HA card. 

For those who also want to retrieve other data throughout their session such as current RA/DEC position, meridian flip time, and other useful metrics, please also follow the instructions @diabetic_debate 's provided for setting up MQTT in Home Assistant and Ground Station in NINA:

https://www.cloudynights.com/topic/902171-nina-status-dashboard-in-home-assistant-via-mqtt/

## Pre-Requisites

### Home Assistant
1. Home Assistant running. These instructions were written for Home Assitant running in container mode, and haven't yet been validated for other modes, although it should be similar.
1. python3 installed

### NINA
1. Install Web Session History Viewer in your NINA instance. After restarting NINA, update the plug-in's "web plugin state" to ON and set the port to an available port on the machine running NINA.

## Installation

1. If it doesn't already exist, create a python_scripts folder in the root/config directory of your HA instance
1. Copy the nina.image-data.py and 'source' directory into python_scripts
1. ssh into the server running Home Assitant and navigate to the python_scripts directory
1. Execute the following to create the python env with the necessary libraries:
		python -m venv env
		. env/bin/activate
		pip install --upgrade pip
		pip install Pillow
		pip install requests
1. Edit nina.image-data.py line 10 to set the baseApiUrl to the URL of your Web Session History Viewer, e.g. https://my_nina_machine.example.com:8888
1. For now, execute the script once to build your initial image capture (mext release will add steps soon regarding how to enable this script to be executed from an HA automation). Exeucte from ssh while in same directory as the python script.
		python ./nina.image-data.py
 
1. In Home Assitant, edit a dashboard and add a new Webpage Card
1. Edit the code for the new Webpage Card and set to:
		type: iframe
		url: /local/ApImages/index.html
		aspect_ratio: '1'


