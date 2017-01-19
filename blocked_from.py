
#============================================================================================#
#      Maltego transform to return HTTP response codes of a target site via list of proxies  #
#          by Lawrence Alexander 2017 @LawrenceA_UK la2894@my.open.ac.uk                     #
#============================================================================================#

from MaltegoTransform import MaltegoTransform
from MaltegoTransform import MaltegoEntity
import sys
import requests
import csv
import re
import random
import time
import codecs

# Set up transform object

t_form = MaltegoTransform()

headers = {}

# Take in domain from Maltego
url = sys.argv[1]

# Format input domain as URL
if url[0:4] is not "http":    
    url="http://www." + url
if url[-1] is not"/":
    url+="/" 
 
# Load proxy and User-Agent files
proxyfile="proxies.txt"
infile=open(proxyfile,"r")
proxies=infile.read().splitlines()
proxies =filter(None, proxies)

# Hat tip to https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
agentfile="user-agents.txt"
in_file=open(agentfile,"r")
user_agents=in_file.readlines()

failcounter=0
blocked = False

# Iterate through proxy list with random delay between requests 

for proxy in proxies: 
    time.sleep(random.randint(3,7))
    proxy=proxy.strip()    
    # Assign random User-Agent for each request
    headers['User-Agent']= user_agents[random.randint(0,len(user_agents)-1)].strip()
    try: 
        query = requests.get(url,proxies={'http':proxy}, headers=headers)  
        
        # Where site returns code potentially indicative of blocking or censorship,        
        # add the proxy IP as new entity
        
        if query.status_code == 403 or query.status_code == 451 or query.status_code == 503 or query.status_code == 504 or query.status_code == 400:
            blocked=True
            ip_address = re.search('[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}',proxy)
            t_form.addEntity("maltego.IPv4Address", ip_address.group())
            t_form.addEntity("maltego.Phrase", "HTTP %s" % str(query.status_code))
                        
    except:
        failcounter+=1        
        if failcounter==len(proxies):
            t_form.addException("Query failed for %s" % url)
            t_form.throwExceptions()
                       
infile.close()


# If all proxies returned HTTP OK, conclude site is not blocked      
if query.status_code == 200 and blocked==False:
    t_form.addEntity("maltego.Phrase", "[Not Blocked]")
    
# Return XML for Maltego 
t_form.returnOutput()     
    
