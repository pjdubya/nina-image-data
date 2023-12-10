from PIL import Image
import json
import os
import shutil
import requests
from io import BytesIO
import datetime
import asyncio
import logging
import sys
import glob

loggerName = 'nina-image-data--local-logger'

# when running this script from HA's pyscript with pyscript/config.yaml set with configuration for this application, these variables will be set
if 'pyscript.app_config' in globals():
    log.info('pyscript detected: using values provided in <config>/pyscript/config.yaml')
    baseApiUrl = pyscript.app_config[0]['nina_web_viewer_base_url']
    targetDir = pyscript.app_config[0]['image_folder']
    sourceDir = pyscript.app_config[0]['source_folder']
else:
    # we're also going to need our own logger if running outside of pyscript
    log = logging.getLogger(loggerName)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    log.info('pyscript not detected: using values provided in main app file')
    baseApiUrl = 'http://my_nina_machine.example.com:8888'
    targetDir = '../www/ApImages'
    sourceDir = './source'
    
sessionsUrl = baseApiUrl + '/sessions/sessions.json'
imageList = []
targetFiles = []
gatherStatus = "unknown"

def requestGetAsync(url):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, requests.get, url)

async def gatherImages():
    global targetFiles, gatherStatus
    log = logging.getLogger(loggerName)
    # TODO: may still need to add check and create www directory 
    if not os.path.exists(targetDir):
        os.mkdir(targetDir)

    try:
        responseSessions = await requestGetAsync(sessionsUrl)
        jsonResponseSessions = json.loads(responseSessions.text)
        for session in jsonResponseSessions['sessions']:
            sessionKey = jsonResponseSessions['sessions'][0]['key']
            sessionDataUrl = baseApiUrl + '/sessions/{}/sessionHistory.json'.format(sessionKey)
            responseImages = await requestGetAsync(sessionDataUrl)
            jsonResponseImages = json.loads(responseImages.text)

            for target in jsonResponseImages['targets']:
                targetName = target['name']
                for imageRecord in target['imageRecords']:
                    imageKey = imageRecord['id']
                
                    # only download the file again if we don't already have it
                    filename = '{}-{}.jpg'.format(targetName, imageKey) 
                    if (not filename in targetFiles):
                        imageUrl = baseApiUrl + "/sessions/{}/thumbnails/{}.jpg".format(sessionKey, imageKey)    
                        imageData = await requestGetAsync(imageUrl)
                        image = Image.open(BytesIO(imageData.content))    
                        image.save('{}/{}'.format(targetDir, filename))
                        log.debug("downloaded {}".format(imageKey))
                    else:
                        log.debug("already downloaded {}, skipping".format(imageKey))

                    targetFiles[filename] = 'validated'
                    imageListItem = { 'filename': '{}'.format(filename), 'epochMilliseconds': imageRecord['epochMilliseconds'] }              
                    imageList.append(imageListItem)
                    log.debug('appended filename {} epocmilliseconds {} for target {} session {} arraysize {}'. format(filename, imageRecord['epochMilliseconds'], targetName, sessionKey, len(imageList)))
                    
            # purge any (jpg) files found on target directory that were not validated to be part of the still-current NINA image set
            filesToDelete = [(filename, status) for filename, status in targetFiles.items() if status == "unvalidated"]
            for filename, status in filesToDelete:
                log.info("Deleting prior jpg file {} as no longer part of current NINA data set".format(filename))
                os.remove('{}/{}'.format(targetDir, filename))
                
        if (len(imageList) > 0):
            gatherStatus = "success"
        else:
            gatherStatus = "noImages"               

    except ConnectionError:
        gatherStatus = "connectionError"
    except Exception as error:
        gatherStatus = "genericError: {}".format(error)
    except:
        gatherStatus = "otherError"

    return

def buildIndex():
    html = "<!DOCTYPE html><html><title>AP Session Images</title>\n"

    # disable caching since this file will be recreated frequently
    html += "<head>\n"
    html += "<meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\" />\n"
    html += "<meta http-equiv=\"Pragma\" content=\"no-cache\" />\n"
    html += "<meta http-equiv=\"Expires\" content=\"0\" />\n"
    html += "</head>\n"

    html += "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
    html += "<link rel='stylesheet' href='https://www.w3schools.com/w3css/4/w3.css'>\n"
    html += "<link rel='stylesheet' href='css/mycss.css'>\n"
    html += "<body><div class='w3-content w3-display-container'>\n"

    if (gatherStatus == "success"):
        for image in sorted(imageList, key=lambda x: x['epochMilliseconds']):
            time_string = datetime.datetime.fromtimestamp(image['epochMilliseconds'] / 1000).strftime("%m/%d/%Y %I:%M:%S%p")
            html += "\n\t<span class='time'>" + time_string + "</span>\n"
            sequence_string = "{} / {}".format(imageList.index(image) + 1, len(imageList))
            html += "\t<span class='sequence'>" + sequence_string + "</span>\n"
            html += f"\t<img class='slide' src='{image['filename']}' style='width:100%'>\n"

        html += "<button class='w3-button w3-black w3-display-left' onclick='plusDivs(-1)'>&#10094;</button>\n"
        html += "<button class='w3-button w3-black w3-display-right' onclick='plusDivs(1)'>&#10095;</button>\n"
        html += "</div>\n<script src='js/myscripts.js'></script></body></html>\n"
    elif gatherStatus == "noImages":
        html += "</h2>No images yet available to download from NINA.</h2>"
        html += "</div></html>"
    elif gatherStatus == "connectionError":
        html += "</h2>Unable to establish connection to NINA.</h2>"
        html += "</div></html>"
    elif "genericError" in gatherStatus:
        html += "</h2>Error in establishing connection to NINA: {}.</h2>".format(gatherStatus)
        html += "</div></html>"
    elif gatherStatus == "otherError":
        html += "</h2>An unexpected error has occured. See logs for details.</h2>"
        html += "</div></html>"

    targetFile = targetDir + "/index.html"
    # must use os.open here due to pyscript restrictions on using open; delete old file and create new to ensure it's clean
    os.remove(targetFile)
    fd = os.open(targetFile, os.O_RDWR|os.O_CREAT)
    os.write(fd, str.encode(html))        
    os.close(fd)
    log.info('Created index.html in {} with {} images'.format(targetDir, len(imageList)))

def initTarget():
    log = logging.getLogger(loggerName)
    shutil.copytree(os.path.abspath(sourceDir), targetDir, dirs_exist_ok=True)
    log.info('Initialized source support files into {}'.format(targetDir))
    
    # get list of files ending in jpg, ie the previously stored image files, since we dont need to download those again
    global targetFiles
    targetFiles = { f: 'unvalidated' for f in glob.glob('*.jpg', root_dir=targetDir) }
    
    return

async def ninaimagedataasync():
    loop = asyncio.get_running_loop()
    log.info('Starting ninaimagedata')
    imageList.clear()
    initTarget()
    await gatherImages()
    buildIndex()
    log.info('Exiting ninaimagedata')

#comment out the @service line when running locally outside of pyscript
@service
def ninaimagedata():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ninaimagedataasync())
    except Exception as e: log.info(e)

ninaimagedata()