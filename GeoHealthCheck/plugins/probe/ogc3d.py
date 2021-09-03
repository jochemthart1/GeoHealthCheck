from GeoHealthCheck.probe import Probe
import requests


class Ogc3DTileset(Probe):
    """
    ...
    """

    NAME = '...'
    DESCRIPTION = '...'
    RESOURCE_TYPE = 'OGC:3D'
    REQUEST_METHOD = 'GET'

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
    }
    """Checks avail"""

    def perform_request(self):
        url_base = self._resource.url

        self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, url_base))

        try:
            url = url_base
            self.response = Probe.perform_get_request(url)

        except requests.exceptions.RequestException as e:
            msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

        if self.response:
            self.log('response: status=%d' % self.response.status_code)

            if self.response.status_code / 100 in [4, 5]:
                self.log('Error response: %s' % (str(self.response.text)))