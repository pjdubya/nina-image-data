from PIL import Image
import json
import os
import shutil
import requests
from io import BytesIO
import datetime

# when running this script from HA's pyscript with pyscript/config.yaml set with configuration for this application, these variables will be set
if 'pyscript.app_config' in globals():
    log.info('pyscript detected: using values provided in <config>/pyscript/config.yaml')
    baseApiUrl = pyscript.app_config[0]['nina_web_viewer_base_url']
    targetDir = pyscript.app_config[0]['image_folder']
    sourceDir = pyscript.app_config[0]['source_folder']
else:
    log.info('pyscript not detected: using values provided in main app file')
    baseApiUrl = 'https://my_nina_machine.example.com:8888'
    targetDir = '../www/ApImages'
    sourceDir = './source'

sessionsUrl = baseApiUrl + '/sessions/sessions.json'

imgListWeb = []

def gatherImages():
    
    # TODO: may still need to add check and create www directory 
    
    if not os.path.exists(targetDir):
        os.mkdir(targetDir)

    responseSessions = task.executor(requests.get, sessionsUrl)
    jsonResponseSessions = json.loads(responseSessions.text)
    for session in jsonResponseSessions['sessions']:
        sessionKey = jsonResponseSessions['sessions'][0]['key']
        sessionDataUrl = baseApiUrl + '/sessions/{}/sessionHistory.json'.format(sessionKey)
        responseImages = task.executor(requests.get, sessionDataUrl)
        jsonResponseImages = json.loads(responseImages.text)

        for target in jsonResponseImages['targets']:
            targetName = target['name']
            for imageRecord in target['imageRecords']:
                imageKey = imageRecord['id']
                imageUrl = baseApiUrl + "/sessions/{}/thumbnails/{}.jpg".format(sessionKey, imageKey)
    
                imageData = task.executor(requests.get, imageUrl)

                img = Image.open(BytesIO(imageData.content))
    
                filename = '{}-{}.jpg'.format(targetName, imageKey)
                img.save('{}/{}'.format(targetDir, filename))
                # fromtimestamp takes seconds so need to convert ms to sec
                imageListItem = { 'filename': '{}'.format(filename), 'epochMilliseconds': imageRecord['epochMilliseconds'] }              
                imgListWeb.append(imageListItem)

    return

def buildIndex(imageList) -> None:

    html = "<!DOCTYPE html><html><title>AP Session Images</title>"

    # disable caching since this file will be recreated frequently
    html += "<head>"
    html += "<meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\" />"
    html += "\<meta http-equiv=\"Pragma\" content=\"no-cache\" />"
    html += "<meta http-equiv=\"Expires\" content=\"0\" />"
    html += "</head>"

    html += "<meta name='viewport' content='width=device-width, initial-scale=1'>"
    html += "<link rel='stylesheet' href='https://www.w3schools.com/w3css/4/w3.css'>"
    html += "<link rel='stylesheet' href='css/mycss.css'>"
    html += "<body><div class='w3-content w3-display-container'>"

    # start with most recent image so latest image will be listed first
    for image in sorted(imageList, key=lambda x: x['epochMilliseconds'], reverse=True):
        time_string = datetime.datetime.fromtimestamp(image['epochMilliseconds'] / 1000).strftime("%m/%d/%Y %I:%M:%S%p")
        html += "<span class='myDate'>" + time_string + "</span>"
        html += f"<img class='mySlides' src='{image['filename']}' style='width:100%'>"

    html += "<button class='w3-button w3-black w3-display-left' onclick='plusDivs(-1)'>&#10094;</button>"
    html += "<button class='w3-button w3-black w3-display-right' onclick='plusDivs(1)'>&#10095;</button>"
    html += "</div><script src='js/myscripts.js'></script></body></html>"

    targetFile = targetDir + "/index.html"
    # must use os.open here due to pyscript restrictions on using open
    fd = os.open(targetFile, os.O_RDWR|os.O_CREAT)
    os.write(fd, str.encode(html))        
    os.close(fd)
    log.info('Created index.html in {} with {} images'.format(targetDir, len(imageList)))

def initSource():
    
    # copytree requires the destination be non-existent. we'll be rebuilding the rest of the directory using other functions anyway.
    if os.path.exists(targetDir):
        shutil.rmtree(targetDir)

    if os.path.exists(targetDir + '/css'):
        os.rmdir(targetDir + '/css')

    if os.path.exists(targetDir + '/js'):
        os.rmdir(targetDir + '/js')

    shutil.copytree(os.path.abspath(sourceDir), targetDir)

    log.info('Initialized source support files into {}'.format(targetDir))

    return

@service
def ninaimagedata(action=None, id=None):
    log.info('Starting ninaimagedata')
    initSource()
    gatherImages()
    buildIndex(imgListWeb)
    log.info('Exiting ninaimagedata')
