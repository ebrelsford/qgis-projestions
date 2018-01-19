import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from . import settings


def get_projestions(geojson):
    """Get projestions for the given geojson"""
    url = '%s?%s' % (settings.PROJESTIONS_URL, urlencode({'geojson': 'false'}))
    data = json.dumps({'geom': geojson})
    headers = {'Content-Type': 'application/json'}
    request = Request(url, data.encode('utf-8'), headers)
    return json.load(urlopen(request))
