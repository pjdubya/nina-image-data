# nina-image-data

## Description

Astrophotography images captured with NINA generally remain locally captured on the device where NINA is running, e.g. a mini PC at the capture site. For users who wish to monitor the progress of their imaging session remotely, they may use RDC to view the progress of NINA throughout the night. This project helps users who are running Home Assistant to retrieve thumbnail versions of their stretched images and display them in a HA card. 

For those who also want to retrieve other data throughout their session such as current RA/DEC position, meridian flip time, and other useful metrics, please also follow the instructions @diabetic_debate 's provided for setting up MQTT in Home Assistant and Ground Station in NINA:

https://www.cloudynights.com/topic/902171-nina-status-dashboard-in-home-assistant-via-mqtt/

## Pre-Requisites

### Home Assistant and pyscript
- Home Assistant running. These instructions were written for Home Assitant running in container mode, and haven't yet been validated for other modes, although it should be similar.
- pyscript installed. See https://github.com/custom-components/pyscript for details. AppDaemon may work also, but HA's built-in python service only supports scripts that don't use imports or blocking I/O. Some recommendations if you use pyscript:
  - Install the HACS component but don't install the UI integration. Instead of the UI integration, follow the README's suggestion to use a pyscript configuration file and add this reference to that in your <config>/configuration.yaml 

```pyscript: !include pyscript/config.yaml```

  - In your configuration.yaml, add the following to your logger

```custom_components.pyscript: info```

  - Create <config>/pyscript/config.yaml and set it to contain follows upcating nina_web_viewer_base_url for your environment.

```
allow_all_imports: true
apps:
  nina-image-data:
    - nina_web_viewer_base_url: http://my_nina_machine.example.com:8888
      image_folder: /config/www/ApImages
      source_folder: /config/pyscript/apps/nina-image-data/source
```

### NINA
- Install Web Session History Viewer in your NINA instance. After restarting NINA, update the plug-in's "web plugin state" to ON and set the port to an available port on the machine running NINA.

## Installation

- If it doesn't already exist, create a pyscript folder in the root/config directory of your HA instance. This folder may already be present, however, upon successful installation of pyscript.
- With pyscript, create additional subfolders apps/nina-image-data
- Copy the __init__.py and 'source' directory into pyscript/apps/nina-image-data/
- In Home Assitant, edit a dashboard and add a new Webpage Card
- Edit the code for the new Webpage Card and set to:
```
		type: iframe
		url: /local/ApImages/index.html
		aspect_ratio: '1'
```


