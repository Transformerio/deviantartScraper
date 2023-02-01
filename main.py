import requests
import json
from array import *
import os
import aiohttp
import asyncio
import aiofiles
import argparse
import re

class getData:
    def __init__(self, username):
        # global variable
        self.urls = []
        self.user = username
        # call to automate
        self.fetchAllArtUrl(username, 0)
        
    def fetchAllArtUrl(self, userName, offset):
        ### Gets all gallary picture urls via JSON API get request
        # offset = where you are in page
        # offset increases as you move down and opposite likewise
        # max limit is 60 anything over will default to 10
        URL = 'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?username=' + userName + '&offset=' + str(offset) + '&limit=60&all_folder=true'
        get = requests.get(URL)
        loader = json.loads(get.text)
        _NEXTOFFSET = loader['nextOffset']
        _RESULTS = loader['results']
        ### json tree
        # hasMore: , nextOffset, results [ deviation { deviationID, etc }, deviation {} ...]
        for deviation in _RESULTS:
            appendMe = []
            # this will bypass mature filter n give URL with token
            #_URL = 'https://backend.deviantart.com/oembed?url=' + deviation['deviation']['url']
            # all found in initial json call
            _TYPE = deviation['deviation']['type']
            _TITLE = deviation['deviation']['title']
            if _TYPE == 'image':
                _DEV = deviation['deviation']
                _MEDIA = _DEV['media']
                _BASEURL = _MEDIA['baseUri']
                _TYPE = _MEDIA['types']
                ## BYPASS = where it needs to reformat url to prettyname idk y lol
                # NO BYPASS
                try:
                    _TOKEN = _MEDIA['token'][0]
                    _URL = _BASEURL + '?token=' + _TOKEN 
                except:
                    print(_TITLE)
                    _URL = _BASEURL
                    #_URLBYPASS = None
                    pass
                # YES BYPASS
                fail = False
                try:
                    _URLTYPE = _MEDIA['types'][8]['c']
                except:
                    fail = True
                if fail == False:
                    try:
                        _TOKEN = _MEDIA['token'][0]
                        _PRETTYNAME = _MEDIA['prettyName']
                        _URLTYPENEW = re.sub('\<.*?>',_PRETTYNAME ,_URLTYPE , flags=re.DOTALL)
                        _URLBYPASS = _BASEURL + '/' + _URLTYPENEW + '?token=' + _TOKEN
                    except:
                        _URLBYPASS = None
                        pass    
                else:
                    _URLBYPASS = None
            else: 
                print(_TITLE + ' IS ' + _TYPE)
                pass
            # adds to global url array
            try:
                appendMe.append(_TITLE)
                appendMe.append(_URL) 
                appendMe.append(_URLBYPASS)
                self.urls.append(appendMe)
            except Exception as e:
                print('[' + _TYPE + ']' + _TITLE + ':     ' + str(e))
                pass
        # recursion to get all gallary links
        if _NEXTOFFSET != None:
            self.fetchAllArtUrl(userName, _NEXTOFFSET)
        else:
            print('[Fetch URL] Complete')
            # pretty print print('\n'.join(urls))
        self.saveUrls()

    def saveUrls(self):
        ### saves global url array as json to the user folder under data.json
        f = open("Data/" + self.user + "/data.json", "w")
        f.write(json.dumps(self.urls))
        # pretty print f.write(str('\n'.join(imageUrls)))
        f.close()
        print('[Save to file] Complete')

    """ Decapercated because extremely inefficient and unessary
    #call through saveUrls
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(self.enforceBypass(self.urls))
    async def enforceBypass(self, urls):
        async with aiohttp.ClientSession() as session:
            #for items in urls:
                async with session.get(items[1]) as resp:
                    data = json.loads(await resp.text())
                    items[1] = data["url"]
                    print('OK')
            print('[Bypass] Complete')
    """    
    async def download(self):
        ### using the global url array, async download all media(images as of now 7/15) into the Posts folder under the creator's username
        # counter var for print [i / total] 
        i  = 0
        total = str(len(self.urls))
        log = open('Data/' + self.user + '/log.txt', 'w')
        async with aiohttp.ClientSession() as session:
            for item in self.urls:
                i+=1
                # parse global url array [ [title, directImageURL], [] ...]
                title = item[0]
                if "/" in title:
                    title = title.replace("/", "_")
                url = item[1]
                urlBypass = item[2]
                # pretty print for console and for log
                ext = url[url.find('?')-3:url.find('?')]
                logText = '{:.<25}'.format('[' + title + ']')
                counterStatus = str(i) + '/' + total
                # logPath = 'Data/' + self.user + '/log.txt'
                path = 'Data/' + self.user + '/Posts/' + title + '.' + ext
                ### checks to see if file already exists, if so run skip
                if os.path.isfile(path) == False:
                    ### downloads the media and if fail, ignore and log
                    if urlBypass == None:
                        async with session.get(url) as resp:
                            try:
                                #print(url)
                                f = await aiofiles.open(path, mode = 'wb+')
                                await f.write(await resp.read())
                                log.write(logText + '{:.>15}'.format('OK') + '\n')
                                f.close()
                                print('{:.<35}'.format('[' + counterStatus + ' ' + title + ']') + 'OK')
                            except:
                                print(url)
                                log.write(logText + '{:.>15}'.format('FAIL') + '\n')
                                print('{:.<35}'.format('[' + counterStatus + ' ' + title + ']') + 'FAIL')
                                pass
                    else:
                        try:
                            #if(respB.status == 403 or resp.reason == 'HTTPForbidden'):
                            async with session.get(urlBypass) as respB:
                                f = await aiofiles.open(path, mode = 'wb+')
                                await f.write(await respB.read())
                                log.write(logText + '{:.>15}'.format('OK') + '\n')
                                f.close()
                                print('{:.<35}'.format('[' + counterStatus + ' ' + title + ']') + 'UNAUTHORIZED OK')
                            #else:
                        except Exception as e:
                            print(e)
                            pass
                else: 
                    log.write(logText + '{:.>15}'.format('SKIP') + '\n')
                    print('{:.<35}'.format('[' + counterStatus + ' ' + title + ']') + 'SKIP')
                    pass
    ### --- debugger function ---
    def get(self):
        self.writeToFile(self.urls)

    def showHTML(self, text):
        f = open("reader.html", "w")
        f.write(str(text))
        f.close()
    ### -------------------------

class fileManager: 
    ### creates the folders and files required
    def __init__(self, username):
        dataPath = '../devScrape/Data'
        userPath = '../devScrape/Data/' + username + '/'
        userDataPath = userPath + '/data.json'
        userPostPath = userPath + '/Posts'
        # userDownloadLogPath not needed to be created as it is created during the os.write call
        #userDownloadLogPath = userPath + '/log.txt'
        if os.path.isdir(dataPath) == False:
            os.mkdir(dataPath)
        if os.path.isdir(userPath) == False:
            os.mkdir(userPath)
        if os.path.isfile(userDataPath) == False:
            with open(userDataPath, 'w'): pass
        if os.path.isdir(userPostPath) == False:
            os.mkdir(userPostPath)
        #if os.path.isfile(userDownloadLogPath) == False:
        #    with open(userDownloadLogPath, 'w'): pass
    # helper methods to see if file/folder exist
    def fileExists(path):
        return os.path.isfile(path)
    def folderExists(path):
        return os.path.isdir(path)

        
def main(): 
    #arguemnt handler
    # main.py -u username
    parser = argparse.ArgumentParser(description = 'Deviantart Gallary Downloader')
    parser.add_argument('-u', help = 'Enter the Username of the Gallary Owner')
    args = parser.parse_args()
    _targetUser = args.u

    initialize = fileManager(_targetUser)
    data = getData(_targetUser)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(data.download())

if __name__ == "__main__":
    main()
