"""
Preprared by:  jeff.kelley@anthology.com  2023-May
# traverse a course folder directory to
# get a list of files with a string in their name
# uses https://pypi.org/project/webdavclient3/

"""

from webdav3.client import Client
from sys import setrecursionlimit
import configparser
import re
import sys
import logging
from pprint import pprint
import urllib.parse
import csv

setrecursionlimit(100)  # Avoid runaways

#Logging configuration
logging.basicConfig(
    filename='webdavclient3_find_files.log',
    encoding='utf-8',
    level=logging.INFO,
    format='%(asctime)s : %(levelname)s : %(name)s : %(message)s'
    )
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


listFiles=[]  ##initate list

# keys returned by client.list 
keys = ['created','name','size','modified','etag','isdir','content_type','path']


##TBD turn this into a parameter input
fileString = 'syllabus'  # string to find in file name


# list of regex expressions to filter out file types
exclude = [
    "image*"
    ]  
excludeTypes = "(" + ")|(".join(exclude) + ")"  # Make a regex that matches if any of our regexes match.


# Get connection information from ini file
config = configparser.ConfigParser()
config.read('connection.ini')
root = config['webdav']['Root']
login = config['webdav']['Login']
password = config['webdav']['Password']



###

def davWalk(pathList,searchString):
    """Returns a list of dictionaries for files that contain searchString in filename."""
    for dirPath in pathList:

        #print("---------")
        #print("Looking for files and folders in " + dirPath)
        
        options = {
         'webdav_hostname': root+dirPath,
         'webdav_login':    login,
         'webdav_password': password
        }

        client = Client(options)# Returns a list of dictionaries with files/folder details
        try:
            contents = client.list('', get_info=True)
            #pprint(contents)
        except:
            logging.warning('client.list failed: Cannot conect to ' + dirPath)
            continue

        ## initate
        subDirList = []

        for item in contents:
            if item['path'] == dirPath:  # Exclude self
                logging.debug('Root folder exclude: ' + item['path'])
                continue
            if item['isdir']:        
                subDirList.append(item['path'])  # Add to list for recurse
                logging.debug('Add to SubDirList: ' + item['path'])
                continue
            if re.match(excludeTypes,item['content_type']):  # Excluded file type
                logging.debug('File type exclude: ' + item['path'])
                continue
            if searchString.lower() in item['name'].lower():     # File name match
                logging.debug('File match: ' + item['path'])
                item['path'] = urllib.parse.quote(item['path'])  # Encode the path
                listFiles.append(item)
            else:
                logging.debug('Skip. No match: ' + item['path'])

        if len(subDirList) > 0:
            logging.debug("Next we go look in the sub directories.")
            davWalk(subDirList,searchString)  # Recurse function to traverse the tree
        else:
            continue


## main program..

logging.info("Starting module.")

with open('course_ids.csv', newline='') as csvfile:
    courseList = csv.reader(csvfile, delimiter=',')
    for course in courseList:
        courseId = course[0]
        logging.info(courseId + ': Starting search')
        path= ['/bbcswebdav/courses/'+courseId+'/']
        checkInternal = False   ##TBD parameter switch to include/exclude internal (protected) course folder
        if checkInternal:
            path.append('/bbcswebdav/internal/courses/'+courseId+'/')
              
        davWalk(path,fileString)
        logging.info(courseId + ": Found " + str(len(listFiles)) + " matching files.")

        with open('files.csv', 'w', newline='') as foundFiles:
            writer = csv.DictWriter(foundFiles, fieldnames = keys)
            writer.writerows(listFiles)

logging.info("Module Complete")
logging.info("----------")
