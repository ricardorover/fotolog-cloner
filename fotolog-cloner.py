#!/usr/bin/env python
# -*- coding: UTF8 -*-

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
	title = tree.xpath('//div[@id="description_photo"]/h1[normalize-space()]/text()')
	title = title[0] if title else ""
	description = tree.xpath('//div[@id="description_photo"]/p[normalize-space()]/text()')
	date = description[-1]
	description = '\n'.join(description)
	description = description[0:len(description) - len(date)]
	comments = scrapeComments(tree)
	wallNextEntries = tree.xpath('//ul[@id="slide_list_photo"]/li/a/@href')
	nextEntry = tree.xpath('//div[@id="flog_img_holder"]/a/@href')

	with open(getFilePathToSave(url)+".json", 'w') as outfile:
	    json.dump({"originalUrl":url, "originalPhotoUrl":originalPhotoUrl, "photoUrl":photoUrl, "date":date, "title":title, "description":description, "comments":comments, "wallNextEntries":wallNextEntries, "nextEntry":nextEntry}, outfile, indent=4)

	return nextEntry[0] if nextEntry else None

def downloadPhoto(url):
	folder = url.split('/')[-2]
	if not os.path.exists(folder):
		os.makedirs(folder)
	local_filename = url.split('/')[-1]
	r = requests.get(url, stream=True)
	with open(folder + "/" + local_filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024):
			if chunk:
				f.write(chunk)
	return local_filename

def getFilePathToSave(url):
	folder = url.split("/")[-3]
	if not os.path.exists(folder):
		os.makedirs(folder)
	fileName = url.split("/")[-2]
	return folder + "/" + fileName

def scrapeComments(tree):
	comments = tree.xpath('//div[@class="flog_img_comments" and not(@id="comment_form")]')
	commentObjects = []
	for comment in comments:
		authorUrl = comment.xpath('.//a/@href')[0]
		authorNameRaw = comment.xpath('.//a/text()')
		authorName = authorNameRaw[0] if authorNameRaw else authorUrl.split("/")[-2]
		dateIndex = len(authorName) + 4
		message = comment.xpath('concat-texts(./p)')[0]
		message = fixMessageWithEmailObfuscatorScriptIfNeeded(comment, message, authorName)
		date = message[dateIndex:dateIndex + 10]
		message = message[dateIndex + 11:len(message)]
		commentObjects.append({'authorName':authorName, 'authorUrl':authorUrl, 'message':message, 'date':date})
	return commentObjects

def fixMessageWithEmailObfuscatorScriptIfNeeded(comment, message, authorName):
	mailObfuscatorScriptRaw = comment.xpath('.//script/text()')
	mailObfuscatorScript = "[email protected]   "+mailObfuscatorScriptRaw[0] if mailObfuscatorScriptRaw else ""
	if mailObfuscatorScript:
		return authorName + "    " + message[len(mailObfuscatorScript):len(message)]
	else:
		return message
		

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

print('Done! Cloned all the ' + str(count) + ' entries from '+rootUrl)