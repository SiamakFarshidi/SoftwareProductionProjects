from selenium import webdriver
from selenium.webdriver.common.by import By
from inscriptis import get_text
from urllib.parse import urlparse
#####################################################################################################################
pageVisits = set()
stackofURLs=set()
#####################################################################################################################
def addToCorpus(data,filename):
    f = open("./"+filename, "a+")
    f.write(data)
    f.close()
#####################################################################################################################
def cleanhtml(raw_html):
    return get_text(raw_html)
#####################################################################################################################
def getContetnts(url):
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(0.5)
    title = driver.title
    pageHtmlContent=driver.page_source
    driver.quit()
    pageTextualContetnts=cleanhtml(pageHtmlContent)
    return pageTextualContetnts
#####################################################################################################################
def fetchURLs(seed):
    driver = webdriver.Chrome()
    driver.get(seed)
    driver.implicitly_wait(0.5)
    links = driver.find_elements(By.TAG_NAME, 'a')
    domain=urlparse(seed).netloc
    # Iterate over link elements
    for link in links:
        newURL=link.get_attribute('href')
        if((newURL not in pageVisits) and (urlparse(newURL).netloc==domain)):
            pageVisits.add(newURL)
            stackofURLs.add(newURL)
        if(len(pageVisits)>NumberOfPageVisits):
            break
        print ('['+str(len(pageVisits))+'] Adding URL: '+link.get_attribute('href'))
#####################################################################################################################
def startCrawlingProcess(seed,filename):
    fetchURLs(seed)
    counter=0
    while len(pageVisits)<NumberOfPageVisits:
        if(len(stackofURLs)>0):
            fetchURLs(stackofURLs.pop())
    extractData(filename)
#####################################################################################################################
def extractData(filename):
    counter =1
    while pageVisits:
        URL=pageVisits.pop()
        addToCorpus(getContetnts(URL),filename)
        print('[' + str(counter) + '] Extracting data from: ' + URL)
        counter = counter + 1
#####################################################################################################################
NumberOfPageVisits=100
startCrawlingProcess("https://azure.microsoft.com/","Azure.txt")
#startCrawlingProcess("https://aws.amazon.com/","AWS.txt")
