from PIL import Image
import json
import os
import shutil
import requests
from io import BytesIO
import datetime

# NOTES:
## Next version will move this to an environment variable:
baseApiUrl = 'https://my_nina_machine.example.com:8888'


sessionsUrl = baseApiUrl + '/sessions/sessions.json'
targetDirWeb = 'ApImages'
targetDirBase = '../www/'
targetDir = targetDirBase + targetDirWeb

imgListWeb = []

def gatherImages():

    if not os.path.exists(targetDirBase):
        os.mkdir(targetDirBase)
    
    if not os.path.exists(targetDir):
        os.mkdir(targetDir)

    responseSessions = requests.get(sessionsUrl)
    jsonResponseSessions = json.loads(responseSessions.text)
    for session in jsonResponseSessions['sessions']:
        sessionKey = jsonResponseSessions['sessions'][0]['key']
        sessionDataUrl = baseApiUrl + '/sessions/{}/sessionHistory.json'.format(sessionKey)
        responseImages = requests.get(sessionDataUrl)
        jsonResponseImages = json.loads(responseImages.text)

        for target in jsonResponseImages['targets']:
            targetName = target['name']
            for imageRecord in target['imageRecords']:
                imageKey = imageRecord['id']
                imageUrl = baseApiUrl + "/sessions/{}/thumbnails/{}.jpg".format(sessionKey, imageKey)
    
                imageData = requests.get(imageUrl)

                img = Image.open(BytesIO(imageData.content))
    
                filename = '{}-{}.jpg'.format(targetName, imageKey)
                img.save('{}/{}'.format(targetDir, filename))
                # fromtimestamp takes seconds so need to convert ms to sec
                imageListItem = { 'filename': '{}'.format(filename), 'epochMilliseconds': imageRecord['epochMilliseconds'] }              
                imgListWeb.append(imageListItem)

    return

def buildIndex(imageList) -> None:

    html = "<!DOCTYPE html><html><title>AP Session Images</title>"
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

    with open(targetDir + "/index.html", "w") as index_file:
        index_file.write(html)
    print(f"Created index.html in {targetDir} with {len(imageList)} images")

def initSource():
    
    # copytree requires the destination be non-existent. we'll be rebuilding the rest of the directory using other functions anyway.
    if os.path.exists(targetDir):
        shutil.rmtree(targetDir)

    if os.path.exists(targetDir + '/css'):
        os.rmdir(targetDir + '/css')

    if os.path.exists(targetDir + '/js'):
        os.rmdir(targetDir + '/js')

    shutil.copytree(os.path.abspath('./source'), targetDir)

    print(f"Initialized source support files into {targetDir}")

    return


initSource()

gatherImages()

buildIndex(imgListWeb)
