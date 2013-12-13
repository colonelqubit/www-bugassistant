#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

#This digs through a pile of bugzilla's and populates the cwd with a big
#collection of bug-docs in per-filetype dirs with bug-ids as names with
#prefixes to indicate which bug-tracker, e.g.
#
#fdo-bugid-X.suffix
#rhbz-bugid-X.suffix
#moz-bugid-X.suffix
#
#where X is the n'th attachment of that type in the bug

from __future__ import print_function
import feedparser
import base64
import datetime
import glob
import re
import os, os.path
import stat
import sys
import time
import xmlrpclib
import pprint

try:
    from urllib.request import urlopen
except:
    from urllib import urlopen
try:
    import xmlrpc.client as xmlrpclib
except:
    import xmlrpclib
from xml.dom import minidom
from xml.sax.saxutils import escape

# If we want lots of information during the run...
VERBOSE = 0
# If we want to log our results.
LOG_RESULTS = 0
# The maximum # of bugs we'll iterate over at one time.
MAX_NUM_BUGS = 1000
# Download all attachments to disk.
DOWNLOAD_ATTACHMENTS = 0

def urlopen_retry(url):
    maxretries = 3
    for i in range(maxretries + 1):
        try:
            return urlopen(url)
        except IOError as e:
            print("caught IOError: " + str(e))
            if maxretries == i:
                raise
            print("retrying...")

# DEPRECATED: Using get_through_rpc_query now
def get_from_bug_url_via_xml(url, mimetype):
    id = url.rsplit('=', 2)[1]
    if VERBOSE: print("Parsing Bug ID: " + id)
    sock = urlopen_retry(url+"&ctype=xml")
    dom = minidom.parse(sock)
    sock.close()
    count = 0
    for attachment in dom.getElementsByTagName('attachment'):
        if VERBOSE: print("--> Attachment: " + attachment)
        if VERBOSE: print("--> mimetype is", end=' ')
        for node in attachment.childNodes:
            if node.nodeName == 'type':
                #print(node.firstChild.nodeValue, end=' ')
                if node.firstChild.nodeValue.lower() != mimetype.lower():
                    #print('skipping')
                    break
                else:
                    count = count + 1
                    break
    return count

# Get information about the attachment and its mimetype.
def get_through_rpc_query(url, mimetype):
    # We're interested in this bug because of one of its attachments.
    if VERBOSE: print("Bug URL: " + url)
    id = url.rsplit('=', 2)[1]
    if VERBOSE: print("Bug ID: " + id)
    query = dict()
    query['ids'] = id
    proxy = xmlrpclib.ServerProxy('https://bugs.freedesktop.org/xmlrpc.cgi')
    result = proxy.Bug.attachments(query)
    attachments = result['bugs'][id]
    count = 0

    if VERBOSE:
        # Print out structured data for our attachments.
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(attachments)

    for a in attachments:
        a_id = str(a['id'])
        a_file_name = str(a['file_name'])
        if VERBOSE:
            print("--> Attachment ID  : " + a_id)
            print("--> Attachment Name: " + a_file_name)
            print("--> Attachment MIME: " + str(a['content_type']))

        if DOWNLOAD_ATTACHMENTS:
            # Grab the attachment.
            # The new filename is <bug_id>_<attachment_id>_<filename>.
            filepath = "attachments/%s_%s_%s" % (a_id, id, a_file_name)
            if VERBOSE:
                print("----> Writing attachment out to %s." % filepath)
                with open("attachments/%s" % filepath, "wb") as handle:
                    handle.write(a['data'].data)

        if a['content_type'] == mimetype:
            count += 1

    return count

def get_through_rss_query(queryurl, mimetype):
    url = queryurl + '?query_format=advanced&f1=attachments.mimetype&v1=application%2Foctet-stream&o1=equals&product=LibreOffice&ctype=atom'
    print('Query url is: ' + url)
    d = feedparser.parse(url)
    
    total_bugs = len(d['entries'])
    print('We have %s bugs to process.' % total_bugs)
    if (total_bugs > MAX_NUM_BUGS):
        print("\nWARNING: total_bugs(%s) is larger than MAX_NUM_BUGS(%s).\n" %
              (total_bugs, MAX_NUM_BUGS))

    print("----------------------------")
    attachCount = 0
    numBugs = 0
    for bug in d['entries']:
        # Break-out when we've reached our bug limit
        if(MAX_NUM_BUGS > numBugs):
            numBugs += 1
        else:
            break

        try:
            print ("before")
            attachCount = attachCount + get_through_rpc_query(bug['id'],
                                                              mimetype)
            print("After")
        except KeyboardInterrupt:
            raise # Ctrl+C should work
        except:
            print(bug['id'] + " failed: " + str(sys.exc_info()[0]))
            pass

        if VERBOSE: print("Total count = " + str(attachCount))

    # Write it to a log.
    if LOG_RESULTS:
        file = open("mimetypecount.csv", "a")
        file.write("\"" + time.strftime("%d/%m/%Y") + "\",\"" +
                   str(attachCount) + "\"\n")
        file.close()

print("Starting our search!")

rss_bugzilla = 'http://bugs.libreoffice.org/buglist.cgi'
mimetype = 'application/octet-stream'

get_through_rss_query(rss_bugzilla, mimetype)

print("Our search has come to an end...")

# vim:set shiftwidth=4 softtabstop=4 expandtab:
