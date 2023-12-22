import urllib.request
import html_to_json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from inscriptis import get_text
from urllib.parse import urlparse
from selenium.common import exceptions
import json
import re
from sentence_transformers import SentenceTransformer, util
from summa import summarizer

#####################################################################################################################
def configSelenium():
    options = webdriver.ChromeOptions()

    options.add_argument('headless')
    options.add_argument('--disable-infobars')
    options.add_argument('--incognito')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--user-agent="mozilla/5.0 (x11; ubuntu; linux x86_64; rv:52.0) gecko/20100101 firefox/52.0"')
    options.add_argument('--access-control-allow-origin= "*"')
    options.add_argument('--access-control-allow-methods= "get"')
    options.add_argument('--access-control-allow-headers= "content-type"')
    options.add_argument('--access-control-max-age= "3600"')
    options.add_argument('--accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"')
    options.add_argument('--connection = "keep-alive"')
    options.add_argument('--cookie = "phpsessid=r2t5uvjq435r4q7ib3vtdjq120"')
    options.add_argument('--pragma = "no-cache"')
    options.add_argument('--cache-control = "no-cache"')
    options.add_argument('--keep-alive = "300"')
    options.add_argument('--accept-language ="en-us,en;q=0.5"')
    options.add_argument('--accept-encoding ="gzip,deflate"')
    options.add_argument('--accept-charset = "iso-8859-1,utf-8;q=0.7,*;q=0.7"')
    options.add_argument('--server = "apache/2"')

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=options)
    return driver
#####################################################################################################################
def remove_key_from_nested_json(json_obj, key_to_remove):
    if isinstance(json_obj, dict):
        for key in list(json_obj.keys()):
            if key == "_values" and (not is_natural_language(json_obj[key])):
                del json_obj[key]

            if key in key_to_remove:
                del json_obj[key]
            else:
                remove_key_from_nested_json(json_obj[key], key_to_remove)
    elif isinstance(json_obj, list):
        for item in json_obj:
            remove_key_from_nested_json(item, key_to_remove)

#####################################################################################################################
def is_natural_language(value):
    if isinstance(value, str):
        pattern = r'^[A-Za-z\s,\'".!?]+$'
        match = re.match(pattern, value)
        return match is not None
    return True
#####################################################################################################################
def getWebpageContent(url):
    driver=configSelenium()
    try:
        driver.get(url)
        driver.implicitly_wait(0.5)
    except exceptions.StaleElementReferenceException as e:
        print(e)
        pass

    title = driver.title

    pageHtmlContent = driver.page_source
    #pageTextualContetnts = get_text(pageHtmlContent)

    output_json = html_to_json.convert(pageHtmlContent)

    return output_json, title
#####################################################################################################################
def saveJsonObject(jsonObject,filename):
    f = open("./"+filename, "w+")
    f.write(json.dumps(jsonObject, indent=2))
    f.close()
#####################################################################################################################
def filterTages(jsonObject):
    filterList=["script","path","svg","noscript","style","meta","json","img","a","link","button","_attributes"]
    remove_key_from_nested_json(jsonObject,filterList )
#####################################################################################################################
def printJSON(jsonObject):
    json_formatted_str = json.dumps(jsonObject, indent=2)
    print(json_formatted_str)
#####################################################################################################################
def traverse_and_remove_empty_items(json_obj):
    if isinstance(json_obj, dict):
        for key, value in list(json_obj.items()):
            if isinstance(value, list):
                # Remove empty items (e.g., empty dictionaries) from the list
                json_obj[key] = [item for item in value if not (isinstance(item, dict) and not item)]
                for item in json_obj[key]:
                    traverse_and_remove_empty_items(item)  # Recursively traverse items in nested lists

                # Remove lists containing "[" and "]" as separate items
                json_obj[key] = [item for item in json_obj[key] if not (item == ("[" or "]") in json_obj[key])]
            else:
                traverse_and_remove_empty_items(value)  # Recursively traverse nested objects
    elif isinstance(json_obj, list):
        # Remove empty items from the list
        json_obj[:] = [item for item in json_obj if not (isinstance(item, dict) and not item)]

        # Remove lists containing "[" and "]" as separate items
        json_obj[:] = [item for item in json_obj if not (item == ("[" or "]") in json_obj)]

        for item in json_obj:
            traverse_and_remove_empty_items(item)  # Recursively traverse items in a list
#####################################################################################################################
# noinspection PyInterpreter
def traverse_and_add_items(json_obj, result_list):
    if isinstance(json_obj, dict):
        for key, value in list(json_obj.items()):
            if isinstance(value, list):
                # Recursively traverse items in nested lists
                traverse_and_add_items(value, result_list)
            else:
                traverse_and_add_items(value, result_list)  # Recursively traverse nested objects

            # Check if the key is "_value" and the value meets the conditions
            if key == "_value" and len(str(value)) > 1 and value not in ("[", "]"):
                result_list.append(value)

    elif isinstance(json_obj, list):
        for item in json_obj:
            traverse_and_add_items(item, result_list)  # Recursively traverse items in a list
#####################################################################################################################
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
cosine_threshold = 0.5  # Adjust as needed
def contextPruning(context,lstText):

    embeddings1 = model.encode(context, convert_to_tensor=True)
    lstRelevantText=[]
    strText=""

    for substring_to_check in lstText:
        embeddings2 = model.encode(substring_to_check, convert_to_tensor=True)
        cosine_similarity = util.pytorch_cos_sim(embeddings1, embeddings2)
        semantic_similarity_score = cosine_similarity.item()
        #print(f"Semantic Similarity Score: {semantic_similarity_score:.2f}")

        if semantic_similarity_score >= cosine_threshold:
            lstRelevantText.append(substring_to_check)
            strText = strText + " " + substring_to_check

    return lstRelevantText, summarizer.summarize(strText)

#####################################################################################################################
def main():
    result_list=[]
    context=""

    #url="https://www.ah.nl/producten/product/wi495314/chiquita-bananen-family-pack"
    #url = "https://www.jumbo.com/producten/jumbo-carpaccio-roast-met-italiaanse-kruiden-pesto-en-kaas-ca-600g-572312KGR"
    #url= "https://aws.amazon.com/athena/?nc2=h_ql_prod_an_ath"
    url="https://www.oracle.com/cloud/cloud-native/functions/"

    jsonObject,context=getWebpageContent(url)
    filterTages(jsonObject)
    traverse_and_remove_empty_items(jsonObject)
    traverse_and_add_items(jsonObject,result_list)
    #printJSON(jsonObject)
    result_list,txtSummary=contextPruning(context, result_list)
    print(result_list)
    print("---------------------")
    print("Summery: " + txtSummary)


    saveJsonObject(jsonObject,"jsonTest.json")
#####################################################################################################################

main()