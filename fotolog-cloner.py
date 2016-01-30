#!/usr/bin/env python

import sys
import os
from lxml import html
import requests
import json

def getFirstEntryFor(rootUrl):
	requestUrl = rootUrl + "mosaic/"
	tree = getTreeForUrl(requestUrl)
	return tree.xpath('//ul[@id="list_photos_mosaic"]/li[1]/a/@href')[0]
	
def getTreeForUrl(url):
	page = requests.get(url)
	return html.fromstring(page.content)

def clonePage(url):
	print('		cloning ' + url + "...")
	tree = getTreeForUrl(url)

	originalPhotoUrl = tree.xpath('//div[@id="flog_img_holder"]/a/img/@src')[0]
	photoUrl = downloadPhoto(originalPhotoUrl)
	description = tree.xpath('//div[@id="description_photo"]/p[normalize-space()]/text()')
	date = description[-1]
	description = '\n'.join(description)
	description = description[0:len(description) - len(date)]
	comments = scrapComments(tree)

	with open(getFilePathToSave(url)+".json", 'w') as outfile:
	    json.dump({"originalUrl":url, "originalPhotoUrl":originalPhotoUrl, "photoUrl":photoUrl, "date":date, "description":description, "comments":comments}, outfile, indent=4)

	nextEntry = tree.xpath('//div[@id="flog_img_holder"]/a/@href')
	return nextEntry[0] if nextEntry else None

def downloadPhoto(url):
	path = url.split('/')[-2]
	local_filename = url.split('/')[-1]
	r = requests.get(url, stream=True)
	with open(path + "/" + local_filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024):
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
	return local_filename

def getFilePathToSave(url):
	folder = url.split("/")[-3]
	fileName = url.split("/")[-2]

	if not os.path.exists(folder):
		os.makedirs(folder)
	return folder + "/" + fileName

def scrapComments(tree):
	commentAuthorNames = tree.xpath('//div[@class="flog_img_comments" and not(@id="comment_form")]//b/a/text()')
	commentAuthorUrls = tree.xpath('//div[@class="flog_img_comments" and not(@id="comment_form")]//b/a/@href')
	commentMessages = tree.xpath('concat-texts(//div[@class="flog_img_comments" and not(@id="comment_form")]/p)')
	comments = []

	for i, commentAuthorName in enumerate(commentAuthorNames, start=0):
		comment = {'authorName':commentAuthorName, 'authorUrl':commentAuthorUrls[i], 'message':commentMessages[i]}
		dateIndex = len(comment["authorName"]) + 4
		commentDate = comment["message"][dateIndex:dateIndex + 10]
		comment["date"] = commentDate
		comment["message"] = comment["message"][dateIndex + 11:len(comment["message"])]
		comments.append(comment)
	return comments


ns = html.etree.FunctionNamespace(None)
def cat(context, elements):
    return [''.join(e.xpath('.//text()')) for e in elements]
ns['concat-texts'] = cat


rootUrl = 'http://fotolog.com/' + str(sys.argv[1]) + "/"
print('Creating a clone from >> ' + rootUrl + " <<...")

count = 0
nextEntry = getFirstEntryFor(rootUrl)
while nextEntry:
	nextEntry = clonePage(nextEntry)
	count += 1

print('Done! Cloned ' + count + ' entries')