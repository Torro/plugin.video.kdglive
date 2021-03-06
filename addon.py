# This Python file uses the following encoding: utf-8
import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup
import re

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mediapath = sys.path[0] + '/resources/media/'
iconprivate = mediapath + 'iconPrivate.png'
thumbprivate = mediapath + 'thumbPrivate.png'


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def getKDGLive():
    """Make a list of livepages to be scraped"""
    start_url = 'https://kerkdienstgemist.nl/search?live=1&recent=1'
    response = BeautifulSoup(urllib.urlopen(start_url))
    bcnum = int(response.findAll('span', 'bold')[2].string)
    pagerange = (bcnum - 1) / 5 + 1
    pagelist = ["{}&page={}".format(start_url, str(no)) for no
                in range(1, pagerange + 1)]

    return pagelist


def parseKDGLive(pagelist):
    """Make a list of all live broadcasts on the pages in the pagelist"""
    broadcasts = []
    
    for page in pagelist:
        response = BeautifulSoup(urllib.urlopen(page))

        for broadcast in response.findAll('li', 'live'):
            if broadcast.find('span', 'information').strong:
                broadcasts.append(
                                  (HTMLParser().unescape(broadcast.h3.a.text),
                                   broadcast.a['href']
                                  )
                                 )
    return broadcasts


def buildServicesList(broadcasts):
    """Fill the 'Live' directory with the live broadcasts in broadcast_tree"""
    broadcast_list = []

    for broadcast in broadcasts:
        li = xbmcgui.ListItem(label=unicode(broadcast[0]))
        url = build_url({'mode': 'stream','url': broadcast[1], 'title': u''.join(broadcast[0]).encode('utf-8')})
        li.setProperty('IsPlayable', 'true')
        li.setInfo('video', {'mediatype': 'Video'})

        broadcast_list.append((url, li))

    xbmcplugin.addDirectoryItems(
        addon_handle, broadcast_list, len(broadcast_list)
        )

    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)


def playStation():
    """Get the stream for the selected broadcast; hand it off to kodi"""

    asseturl = urllib.urlopen('https://www.kerkdienstgemist.nl' + args.get('url')[0]).geturl() + '/embed'
    play_item = xbmcgui.ListItem()

    streampage = BeautifulSoup(urllib.urlopen(asseturl))
    if streampage.body.audio:
        play_item.setPath(path='https://kerkdienstgemist.nl/streams/' + asseturl.split('/')[-2] + '.mp3')
        play_item.addStreamInfo('audio', {})
    elif streampage.body.video:
        scriptelem = streampage.body.findAll('script')[1]
        streamlink = re.search('direct_link:\s+\"(https?://.*)\",', scriptelem.text).group(1)

        play_item.setPath(path=streamlink)
        play_item.addStreamInfo('video', {})
    else:
        xbmc.log('Error: Link not found', xbmc.LOGERROR)

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


mode = args.get('mode', None)

if mode is None:
    lijst = getKDGLive()
    uitzendingen = parseKDGLive(lijst)
    buildServicesList(uitzendingen)

elif mode[0] == 'stream':
    playStation()
