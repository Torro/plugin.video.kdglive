import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import urllib2
from bs4 import BeautifulSoup

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def getKDGLive():
    """Make a list of livepages to be scraped"""
    url = 'https://kerkdienstgemist.nl/browse/live'
    bcnum = int(BeautifulSoup(urllib2.urlopen(url), 'html.parser')
                .find_all('span', 'bold')[2].string)
    pagenum = (bcnum - 1) / 10 + 1
    pagelist = ["{}?page={}".format(url, str(no)) for no
                in range(1, pagenum + 1)]

    return pagelist


def parseKDGLive(pagelist):
    """Make a list of all live broadcasts on the pages in the pagelist"""
    broadcast_tree = {}
    treeindex = 1

    for page in pagelist:
        pagina = BeautifulSoup(urllib2.urlopen(page), 'html.parser')

        for broadcast in pagina.find_all('li', 'live'):
            broadcast_tree.update(
                                  {treeindex:
                                   {'Name': broadcast.h3.a.string
                                    .encode('utf-8'),
                                    'url': broadcast.h3.a['href'],
                                    'Status': broadcast.span.string
                                    }})

            treeindex += 1

    return broadcast_tree


def buildServicesList(broadcast_tree):
    """Fill the 'Live' directory with the live broadcasts in broadcast_tree"""
    broadcast_list = []

    for broadcast in broadcast_tree:
        li = xbmcgui.ListItem(label=broadcast_tree[broadcast]['Name'])
        li.setProperty('IsPlayable', 'true')
        url = build_url(
                        {'mode': 'stream',
                         'url': broadcast_tree[broadcast]['url'],
                         'title': broadcast_tree[broadcast]['Name']
                         })

        broadcast_list.append((url, li, False))

    xbmcplugin.addDirectoryItems(
                                 addon_handle,
                                 broadcast_list,
                                 len(broadcast_list)
                                 )

    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)


def playStation():
    """Get the stream for the selected broadcast; hand it off to kodi"""
    asseturl = urllib2.urlopen('https://www.kerkdienstgemist.nl' +
                               args['url'][0]).url + '/embed'
    stream = BeautifulSoup(
                           urllib2.urlopen(asseturl), 'html.parser'
                           ).body.find_all('script')[3].string.split("'")[1]
    play_item = xbmcgui.ListItem(path=stream)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


mode = args.get('mode', None)

if mode is None:
    lijst = getKDGLive()
    uitzendingen = parseKDGLive(lijst)
    buildServicesList(uitzendingen)

elif mode[0] == 'stream':
    playStation()
