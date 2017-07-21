# This Python file uses the following encoding: utf-8
import sys
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

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
    url = 'https://kerkdienstgemist.nl/browse/live'
    bcnum = int(BeautifulSoup(urllib.urlopen(url))
                .findAll('span', 'bold')[2].string)
    pagenum = (bcnum - 1) / 10 + 1
    pagelist = ["{}?page={}".format(url, str(no)) for no
                in range(1, pagenum + 1)]

    return pagelist


def parseKDGLive(pagelist):
    """Make a list of all live broadcasts on the pages in the pagelist"""
    broadcast_tree = {}
    treeindex = 1

    for page in pagelist:
        pagina = BeautifulSoup(urllib.urlopen(page))

        for broadcast in pagina.findAll('li', 'live'):
            broadcast_tree.update(
                {treeindex:
                 {'Name': broadcast.h3.a.string.encode('utf-8'),
                  'url': broadcast.h3.a['href'],
                  'Status': broadcast.findAll('span')[2].string
                  }
                 }
                )

            treeindex += 1

    return broadcast_tree


def buildServicesList(broadcast_tree):
    """Fill the 'Live' directory with the live broadcasts in broadcast_tree"""
    broadcast_list = []

    for broadcast in broadcast_tree:
        li = xbmcgui.ListItem(label=broadcast_tree[broadcast]['Name'])
        url = build_url(
            {'mode': 'stream',
             'url': broadcast_tree[broadcast]['url'],
             'title': broadcast_tree[broadcast]['Name']})

        if broadcast_tree[broadcast]['Status'] is not None:
            li.setLabel('(Privé) ' + li.getLabel())
            li.setProperty('IsPlayable', 'false')
            li.setArt({'icon': iconprivate,
                       'thumb': thumbprivate})
        else:
            li.setProperty('IsPlayable', 'true')

        broadcast_list.append((url, li, False))

    xbmcplugin.addDirectoryItems(
        addon_handle, broadcast_list, len(broadcast_list)
        )

    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)


def playStation():
    """Get the stream for the selected broadcast; hand it off to kodi"""
    asseturl = urllib.urlopen('https://www.kerkdienstgemist.nl' + args.get('url')[0]).geturl() + '/embed'
    stream = BeautifulSoup(urllib.urlopen(asseturl)).body.findAll('script')[3].string.split("'")[1]
    play_item = xbmcgui.ListItem(path=stream)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


mode = args.get('mode', None)

if mode is None:
    lijst = getKDGLive()
    uitzendingen = parseKDGLive(lijst)
    buildServicesList(uitzendingen)

elif mode[0] == 'stream':
    playStation()
