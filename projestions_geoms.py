from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsFeature, QgsGeometry, QgsJSONExporter,
                       QgsMapLayerRegistry)

import settings


WGS84 = QgsCoordinateReferenceSystem(4326)


def extent_to_geojson(extent):
    return QgsGeometry().fromRect(extent).exportToGeoJSON()


def layer_extent(layer):
    currentCrs = layer.crs()
    transform = QgsCoordinateTransform(currentCrs, WGS84)
    return extent_to_geojson(transform.transformBoundingBox(layer.extent()))


def layer_geom(layer):
    featureList = []

    if layer.featureCount() > settings.PROJESTIONS_MAX_FEATURES:
        # If too many features, randomly select some
        import processing
        processing.runalg('qgis:randomselection', layer, 0,
                          settings.PROJESTIONS_MAX_FEATURES,
                          progress=False)
        featureList = layer.selectedFeatures()
        layer.removeSelection()
    else:
        # Else get all of the features
        feature = QgsFeature()
        iterator = layer.getFeatures()
        while iterator.nextFeature(feature):
            feature.setGeometry(feature.geometry().simplify(0.1))
            featureList.append(feature)
            feature = QgsFeature()

    exporter = QgsJSONExporter(layer, 6)
    exporter.setExcludedAttributes(layer.attributeList())
    return exporter.exportFeatures(featureList)


def project_extent():
    """
    Calculate the project's extent from each layer's extent.

    Can't assume on-the-fly transformation is on, so we convert each
    layer's extent to 4326, then combine it.
    """
    extent = None
    for layer in QgsMapLayerRegistry.instance().mapLayers().values():
        transform = QgsCoordinateTransform(layer.crs(), WGS84)
        layer_extent = transform.transformBoundingBox(layer.extent())
        if extent:
            extent.combineExtentWith(layer_extent)
        else:
            extent = layer_extent
    return extent_to_geojson(extent)


def map_canvas_extent(mapCanvas):
    settings = mapCanvas.mapSettings()

    # Force on-the-fly projection to ensure that the reprojection works
    settings.setCrsTransformEnabled(True)
    transform = QgsCoordinateTransform(settings.destinationCrs(), WGS84)
    return extent_to_geojson(transform.transformBoundingBox(settings.extent()))
