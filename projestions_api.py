import json
from urllib import urlencode
from urllib2 import Request, urlopen
import settings


def get_projestions(geojson):
    """Get projestions for the given geojson"""
    url = '%s?%s' % (settings.PROJESTIONS_URL, urlencode({'geojson': 'false'}))
    data = json.dumps({'geom': geojson})
    headers = {'Content-Type': 'application/json'}
    request = Request(url, data, headers)
    return json.load(urlopen(request))
