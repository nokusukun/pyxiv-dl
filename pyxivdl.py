#Pixiv clipboard downloader by noku
import clipboard
import asyncio
import validators
import urllib.request
import time
import _thread
import pixivpy3
import urllib.parse as urlparse
import json
import traceback
import os

LINKS = []
API = pixivpy3.AppPixivAPI()
PAPI = pixivpy3.PixivAPI()

#configuration
USERNAME = ""
PASSWORD = ""
RETRIES = 5
PATH = "images"
META_FILEEXT = "txt"
META_PATH = "meta"
FILENAME_PATTERN = "{user[account]} - {title}@{id}"


#downloads LINKS
async def main():
    while True:
        time.sleep(0.05)
        if len(LINKS) != 0:
            await download(LINKS.pop())
    pass

async def download(url):
    try:
        print("Downloading: {0}".format(url[0]))
        if not isExist("meta\\{0}.{1}".format(url[0], META_FILEEXT)):

            #meta = API.illust_detail(url[0])
            
            meta = PAPI.works(int(url[0])).response[0]
            meta_dict = json.loads(json.dumps(meta))
            #Save the metadata in the script path.
            try:
                with open("meta\\{0}.{1}".format(url[0], META_FILEEXT), "w") as mds:
                    mds.write(json.dumps(meta, indent = 4))
            except:
                print("Metadata save failed.({0})".format(url[0]))

            #checks if there is multiple pages in the illust
            if meta.page_count > 1:
                p = 1
                for page in meta.metadata.pages:
                    url_basename = os.path.basename(page.image_urls.large)
                    extension = os.path.splitext(url_basename)[1]
                    print("\tDownloading Page: {0}/{1}".format(p, meta.page_count))
                    API.download(page.image_urls.large, path=PATH, name=FILENAME_PATTERN.format(**meta_dict) + "_{0}{1}".format(p, extension))
                    p += 1
            
            else:
                url_basename = os.path.basename(meta.image_urls.large)
                extension = os.path.splitext(url_basename)[1]
                API.download(meta.image_urls.large, path=PATH, name=FILENAME_PATTERN.format(**meta_dict) + extension)
        else:
            print("Already downloaded. Skipping...")

        print("Queue Size: {0}".format(len(LINKS)))
    except Exception as e:
        traceback.print_exc()
        if url[1] > 0:
            print("File download failed. Retrying. ({0}/{1})".format(url[1], RETRIES))
            LINKPUSH([url[0], url[1] - 1])
        else:
            print("File download failed. Disposing Link.")


def isExist(filename):
    try:
        with open(filename) as file:
            return True
    except:
        return False

def generateID():
    return "".join([str(random.randint(0, 9)) for x in range(0, 16)])

def LINKPOP():
    toReturn = LINKS.pop()
    with open("session.bin", "w") as session:
        session.write(str(LINKS))
    return toReturn

def LINKPUSH(data):
    LINKS.append(data)
    with open("session.bin", "w") as session:
        session.write(str(LINKS))


#queues LINKS

def linkQueuer():
    while True:
        last = ""
        lastLink = "" #won't re-shorten the last unshortened link.
        filetypes = ["jpg", "png", "jpeg", "gif"]
        #trigger = "images.discord.com"
        #"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"

        while True:
            time.sleep(0.05)
            url = clipboard.paste() #gets clipboard data

            if validators.url(url) and last != url:
                if "illust_id=" in url:
                #if trigger in url:
                    urlx = urlparse.urlsplit(url)
                    ID = urlparse.parse_qs(urlx.query)["illust_id"][0]
                    print("Pixiv ID Found: {0}".format(ID))
                    LINKPUSH([ID, RETRIES])
                    last = url
    pass


if __name__ == '__main__':

    if not os.path.exists(PATH):
        os.makedirs(PATH)

    try:
        with open("session.bin") as session:
            LINKS = eval(session)
            print("PAST SESSION RESTORED")
    except:
        pass

    try:
        if USERNAME != "" and PASSWORD != "":
            print("Attempting to login...", end = "")
            API.login(USERNAME, PASSWORD)
            PAPI.login(USERNAME, PASSWORD)
            print("Done!")
    except:
        print("Invalid Credentials, continuing anyway.")
        pass
    _thread.start_new_thread( linkQueuer , ())
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main())
    finally:
        event_loop.close()