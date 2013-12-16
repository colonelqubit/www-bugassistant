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
VERBOSE = 1
# If we want to log our results.
LOG_RESULTS = 0
# The maximum # of bugs we'll iterate over at one time.
MAX_NUM_BUGS = 1
# Download all attachments to disk.
DOWNLOAD_ATTACHMENTS = 1
# Print an HTML file containing detailed information about the
# scrutinized attachments.
CREATE_HTML_REPORT = 1

# Some static variables relating to our Bugzilla and tests.
BUGZILLA_URL = "https://bugs.libreoffice.org/"
RSS_BUGZILLA = BUGZILLA_URL + "buglist.cgi"
ATTACHMENT_URL = "https://bugs.libreoffice.org/attachment.cgi?id="
MIMETYPE = 'application/octet-stream'

# This function takes a hash (keyed by bug_id) containing information
# about bugs, attachments, their mimetype, etc.., and returns an HTML
# table displaying information about them with links, etc..
def attachment_info_to_html_table(bugDict):
    # We seem to want enough tweaks to the headers that it doesn't
    # make sense to try to dynamically guess/format them.
    attachmentHeaders = {'id'        : [0, 'Attachment ID'],
                         'edit'      : [1, 'Edit this attachment'],
                         'filename'  : [2, 'File Name'],
                         'extension' : [3, 'Filename Extension'],
                         'filepath'  : [4, 'File Path'],
                         'mimetype'  : [5, 'MIME-type'],
                         # MIMEtype ascertained by downloading and
                         # testing the file itself.
                         'computedmimetype'  : [6, 'MIME-type'],
                         'lastChange': [7, 'Last Time Changed in DB']}
    # Sort our header keys based on our index value
    headerKeys = sorted(attachmentHeaders.keys(),
                        key=lambda k: attachmentHeaders[k][0])
    print("<table>\n")
    print("<tr><th>Bug ID</th>\n")
    for k in headerKeys:
        print("  <th>{0}</th>\n".format(attachmentHeaders[k][1]))
    print ("</tr>\n")

    # Print our header row.
    for bug_id, attachments in bugDict.items():

        # Print out a row for each bug.
        print("<tr><td><a href=\"{0}{1}\">{1}</a></td></tr>\n".format(BUGZILLA_URL, bug_id, bug_id))
    
        for attachment_id, variables in attachments.items():
            # Print out a row for each attachment.
            print("<tr><td></td>\n")

            # Determine if the mimetype and computed mimetype match.
            mimetypeClass = 'mimeMatch' if (variables["mimetype"] == variables["computedmimetype"]) else 'mimeNoMatch'

            for k in headerKeys:
                # Provide a link into Bugzilla for the attachment.
                if(k == "id"):
                    print("  <td><a href=\"{0}{1}\">{1}</a></td>\n".format(ATTACHMENT_URL, variables[k]))
                # Also provide a link for editing.
                elif(k == "edit"):
                    print("  <td><a href=\"{0}{1}&action=edit\">{1}</a></td>\n".format(ATTACHMENT_URL, variables["id"]))
                # Check that the computed mimetype matches the expected type.
                # Matchess 'mimetype' and 'computedmimetype'
                elif "mimetype" in k:  
                    print("  <td class=\"{0}\">{1}</td>\n".format(mimetypeClass, variables[k]))
                else:
                    print("  <td>{0}</td>\n".format(variables[k]))
            print("</tr>\n")
    print("</table>\n")

# This function prints out an HTML page containing information about
# all of the bugs/attachments we've scrutinized.
def create_html_report(bugDict):
    global BUGZILLA_URL

    headString = """
<html>
  <head>
    <title>The Glorious Battle against Incorrect MIME-types!</title>

    <link rel="stylesheet" type="text/css" href="styles.css">
  </head>

  <body>
    <h2>Information about the MIME-types of our <a href="%s">Bugzilla</a> attachments</h2>
    """

    tailString = """
  </body>
</html>
    """
    
    print("Creating HTML file with attachment info.")
    with open("index.html", "w") as handle:
        # Redirect stdout into our file handle to make our statements
        # much easier.
        sys.stdout = handle
        print(headString % BUGZILLA_URL)
        attachment_info_to_html_table(bugDict) 
        print(tailString)
        # Fix stdout back to what it was, originally.
        sys.stdout = sys.__stdout__

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
def get_through_rpc_query(url, mimetype, bugDict):
    # We're interested in this bug because of one of its attachments.
    if VERBOSE: print("Bug URL: " + url)
    bug_id = str(url.rsplit('=', 2)[1])
    if VERBOSE: print("Bug ID: " + bug_id)

    # Create a dict to store info about the attachments on this bug.
    attachInfoDict = {}

    query = dict()
    query['ids'] = bug_id
    proxy = xmlrpclib.ServerProxy('https://bugs.freedesktop.org/xmlrpc.cgi')
#    proxy = xmlrpclib.ServerProxy('https://bugs.freedesktop.org/xmlrpc.cgi',
#                                  use_datetime = True)
    result = proxy.Bug.attachments(query)
    attachments = result['bugs'][bug_id]
    count = 0

    if VERBOSE:
        # Print out structured data for our attachments.
        print("Structured Data for these attachments:")
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(attachments)

    for a in attachments:
        a_id = str(a['id'])
        a_file_name = str(a['file_name'])
        a_extension = os.path.splitext(a_file_name)[1][1:].strip()
        # The new filename is <bug_id>_<attachment_id>_<filename>.
        # Sanitize the given filename first:
        #sanitizedFileName = "".join([x if x.isalnum() else "_" for x in a_file_name])
        filepath = "attachments/%s_%s_%s" % (a_id, bug_id, a_file_name)

        a_mime = str(a['content_type'])

        if VERBOSE:
            print("--> Attachment ID  : " + a_id)
            print("--> Attachment Name: " + a_file_name)
            print("--> Attachment MIME: " + a_mime)

        if DOWNLOAD_ATTACHMENTS:
            # Grab the attachment.
            if VERBOSE:
                print("----> Writing attachment out to (%s)." % filepath)
                with open("attachments/%s" % filepath, "wb") as handle:
                    handle.write(a['data'].data)

        # If we have access to the particular file, check the MIMEtype!
        computedMimetype = ""
        try:
            print("would usually compute mimetype here")
            #computedMimetype = call(["file", "-b", "--mime-type", filepath])
        except IOError as e:
            # If the file does not exist, then we ignore the step and
            # move on.
            print("File not found/related")
        except :
            # If we don't know what went wrong, we just mention the
            # failure.
            print("Sorry, not sure what went wrong here...")

        if a['content_type'] == mimetype:
            count += 1

        # Store information about each attachment.
        lastChangeTime = a['last_change_time'].strftime("%Y-%m-%d %H:%M")
        attachInfoDict[a_id] = {'id'               : a_id,
                                'filename'         : a_file_name,
                                'extension'        : a_extension,
                                'filepath'         : filepath,
                                'mimetype'         : a_mime,
                                'computedmimetype' : computedMimetype,
                                'lastChange'       : lastChangeTime
                                # We'd also like to include last_updated date,
                                # Info about file extension, etc..
                                }

    # Store the attachment dict back into our master dict.
    bugDict[bug_id] = attachInfoDict
    return count

def get_through_rss_query(queryurl, mimetype):
    url = queryurl + '?query_format=advanced&f1=attachments.mimetype&v1=%s&o1=equals&product=LibreOffice&ctype=atom' % mimetype
    print('Query url is: ' + url)
    d = feedparser.parse(url)

    # Create a dictionary var to store information about our
    # bugs/attachments.
    bugDict = {}
    
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
            attachCount = attachCount + get_through_rpc_query(bug['id'],
                                                              mimetype,
                                                              bugDict)
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

    # Write it to an HTML file.
    if CREATE_HTML_REPORT:
        create_html_report(bugDict)

print("Starting our search!")


get_through_rss_query(RSS_BUGZILLA, MIMETYPE)

print("Our search has come to an end...")

# vim:set shiftwidth=4 softtabstop=4 expandtab:
