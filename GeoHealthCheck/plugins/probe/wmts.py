from GeoHealthCheck.probe import Probe
from owslib.wmts import WebMapTileService
from pyproj import Proj, transform


class WmtsGetTileAll(Probe):
    """
    Get WMTS GetTile for all layers.
    """

    NAME = 'Get WMTS GetTile for all layers.'
    DESCRIPTION = """
    Get WMTS GetTile for all layers.
    """
    RESOURCE_TYPE = 'OGC:WMTS'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE=WMTS&VERSION=1.0.0&' + \
                       'REQUEST=GetTile&LAYER={layers}&' + \
                       'TILEMATRIXSET={tilematrixset}&' + \
                       'TILEMATRIX={tilematrix}&TILEROW={tilerow}&' + \
                       'TILECOL={tilecol}&FORMAT={format}&' + \
                       'EXCEPTIONS={exceptions}&STYLE={style}'

    PARAM_DEFS = {
        'layers': {
            'type': 'stringlist',
            'description': 'The WMTS Layer, select one',
            'value': 'All Layers'
        },
        'tilematrixset': {
            'type': 'string',
            'description': 'tilematrixset',
            'value': 'All TileMatrixSets'
        },
        'tilematrix': {
            'type': 'string',
            'description': 'tilematrix',
            'value': 'All TileMatrices'
        },
        'tilerow': {
            'type': 'string',
            'description': 'tilerow',
            'value': 'Center of the Image'
        },
        'tilecol': {
            'type': 'string',
            'description': 'tilecol',
            'value': 'Center of the Image'
        },
        'format': {
            'type': 'string',
            'description': 'The image format',
            'default': 'image/png',
            'required': True,
            'range': None
        },
        'exceptions': {
            'type': 'string',
            'description': 'The Exception format to use',
            'value': 'application/vnd.ogc.se_xml'
        },
        'style': {
            'type': 'string',
            'description': 'The Styles to apply',
            'value': 'default'
        }
    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {
            'default': True
        }
    }
    """
    Checks for WMTS GetTile Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """

    def __init__(self):
        Probe.__init__(self)
        self.layer_count = 0

    def get_metadata(self, resource, version='1.0.0'):
        """
        Get metadata, specific per Resource type.
        :param resource:
        :param version:
        :return: Metadata object
        """
        return WebMapTileService(resource.url, version=version,
                                 headers=self.get_request_headers())

    # Overridden: expand param-ranges from WMTS metadata
    def expand_params(self, resource):

        # Use WMTS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wmts = self.get_metadata_cached(resource, version='1.0.0')
            layers = wmts.contents

            # Take random layer to determine generic attrs
            for layer_name in layers:
                layer_entry = layers[layer_name]
                break

            # Determine image format
            self.PARAM_DEFS['format']['range'] = list(layer_entry.formats)

        except Exception as err:
            raise err

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.wmts = self.get_metadata_cached(self._resource,
                                                 version='1.0.0')

            self.layers = self.wmts.contents

        except Exception as err:
            self.result.set(False, str(err))

    def perform_request(self):
        """ Perform actual request to service, overridden from base class"""

        if not self.layers:
            self.result.set(False, 'Found no WMTS Layers')
            return

        self.result.start()

        results_failed_total = []

        for layer in self.layers:
            self._parameters['layers'] = [layer]

            bbox84 = self.wmts.contents[layer].boundingBoxWGS84
            center_coord_84 = [(bbox84[0] + bbox84[2]) / 2,
                               (bbox84[1] + bbox84[3]) / 2]

            tilematrixsets = self.wmts.tilematrixsets
            for set in tilematrixsets:
                self._parameters['tilematrixset'] = set

                set_crs = tilematrixsets[set].crs
                center_coord = transform(Proj('EPSG:4326'),
                                         Proj(set_crs),
                                         center_coord_84[1],
                                         center_coord_84[0])

                tilematrices = tilematrixsets[set].tilematrix
                for zoom in tilematrices:
                    self._parameters['tilematrix'] = zoom

                    tilecol, tilerow = self.calculate_center_tile(
                        center_coord,
                        tilematrices[zoom])
                    self._parameters['tilecol'] = tilecol
                    self._parameters['tilerow'] = tilerow

                    # Let the templated parent perform
                    Probe.perform_request(self)
                    self.run_checks()

            # Only keep failed Layer results
            # otherwise with 100s of Layers the report grows out of hand...
            results_failed = self.result.results_failed
            if len(results_failed) > 0:
                # We have a failed layer: add to result message
                for result in results_failed:
                    result.message = 'layer %s: %s' % (layer, result.message)

                results_failed_total += results_failed
                self.result.results_failed = []

            self.result.results = []

        self.result.results_failed = results_failed_total

    def calculate_center_tile(self, center_coord, tilematrix):
        scale = tilematrix.scaledenominator
        topleftcorner = tilematrix.topleftcorner
        tilewidth = 0.00028 * scale * tilematrix.tilewidth
        tileheight = 0.00028 * scale * tilematrix.tileheight

        tilecol = int((center_coord[0] - topleftcorner[0]) / tilewidth)
        tilerow = int((topleftcorner[1] - center_coord[1]) / tileheight)

        return tilecol, tilerow


class WmtsGetTileAllRest(WmtsGetTileAll):
    """
    Get WMTS map tile for all layers, REST.
    """

    NAME = 'Get WMTS GetTile for all layers REST.'
    DESCRIPTION = """
    Get WMTS GetTile for all layers REST.
    """
    REQUEST_TEMPLATE = '/wmts/{layers}/{tilematrixset}/{tilematrix}' + \
                       '/{tilerow}/{tilecol}.png'


class WmtsGetTileLayers(WmtsGetTileAll):
    """
    Get WMTS map tile for specific layers.
    """

    NAME = 'WMTS GetTile operation on specific layers'
    DESCRIPTION = """
    Do WMTS GetTile request on user-specified layers.
    """

    PARAM_DEFS = {
        'layers': {
            'type': 'stringlist',
            'description': 'The WMTS Layer, select one',
            'default': [],
            'required': True,
            'range': None
        },
        'tilematrixset': {
            'type': 'string',
            'description': 'tilematrixset',
            'value': 'All TileMatrixSets'
        },
        'tilematrix': {
            'type': 'string',
            'description': 'tilematrix',
            'value': 'All TileMatrices'
        },
        'tilerow': {
            'type': 'string',
            'description': 'tilerow',
            'value': 'Center of the Image'
        },
        'tilecol': {
            'type': 'string',
            'description': 'tilecol',
            'value': 'Center of the Image'
        },
        'format': {
            'type': 'string',
            'description': 'The image format',
            'default': 'image/png',
            'required': True,
            'range': None
        },
        'exceptions': {
            'type': 'string',
            'description': 'The Exception format to use',
            'value': 'application/vnd.ogc.se_xml'
        },
        'style': {
            'type': 'string',
            'description': 'The Styles to apply',
            'value': 'default'
        }
    }

    def expand_params(self, resource):

        # Use WMTS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wmts = self.get_metadata_cached(resource, version='1.0.0')
            layers = wmts.contents
            self.PARAM_DEFS['layers']['range'] = list(layers.keys())

            # Take random layer to determine generic attrs
            for layer_name in layers:
                layer_entry = layers[layer_name]
                break

            # Determine image format
            self.PARAM_DEFS['format']['range'] = list(layer_entry.formats)

        except Exception as err:
            raise err

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.wmts = self.get_metadata_cached(self._resource,
                                                 version='1.0.0')

            self.layers = self._parameters['layers']

        except Exception as err:
            self.result.set(False, str(err))


class WmtsGetTileLayersRest(WmtsGetTileLayers):
    """
    Get WMTS map tile for specific layers, REST.
    """

    NAME = 'Get WMTS GetTile for specific layers REST.'
    DESCRIPTION = """
    Get WMTS GetTile for specific layers REST.
    """
    REQUEST_TEMPLATE = '/wmts/{layers}/{tilematrixset}/{tilematrix}' + \
                       '/{tilerow}/{tilecol}.png'
