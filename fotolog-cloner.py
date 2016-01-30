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

	photoUrl = tree.xpath('//div[@id="flog_img_holder"]/a/img/@src')[0]
	description = tree.xpath('//div[@id="description_photo"]//text()')[0]
	comments = scrapComments(tree)

	print comments

	with open(getFilePathToSave(url), 'w') as outfile:
	    json.dump({"originalUrl":url, "photoUrl":photoUrl, "description":description, "comments":comments}, outfile)

	nextEntry = tree.xpath('//div[@id="flog_img_holder"]/a/@href')
	return nextEntry[0] if nextEntry else None

def adjustElementsArray(comments):
	response = []
	for comment in comments:
		response.append(html.tostring(comment))
	return response

def getFilePathToSave(url):
	folder = url.split("/")[-3]
	fileName = url.split("/")[-2]+".json"

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