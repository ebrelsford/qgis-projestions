from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsFeature, QgsGeometry, QgsJsonExporter,
                       QgsProcessingFeedback, QgsProject)

from . import settings


WGS84 = QgsCoordinateReferenceSystem(4326)


def extent_to_geojson(extent):
    return QgsGeometry().fromRect(extent).asJson()


def layer_extent(layer):
    currentCrs = layer.crs()
    transform = QgsCoordinateTransform(currentCrs, WGS84, QgsProject.instance())
    return extent_to_geojson(transform.transformBoundingBox(layer.extent()))


def layer_geom(layer):
    featureList = []

    if layer.featureCount() > settings.PROJESTIONS_MAX_FEATURES:
        # If too many features, randomly select some
        import processing
        processing.run('qgis:randomselection', {
            'INPUT': layer,
            'METHOD': 0,
            'NUMBER': settings.PROJESTIONS_MAX_FEATURES,
        }, feedback=QgsProcessingFeedback())
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

    exporter = QgsJsonExporter(layer, 6)
    exporter.setExcludedAttributes(layer.attributeList())
    return exporter.exportFeatures(featureList)


def project_extent():
    """
    Calculate the project's extent from each layer's extent.

    Can't assume on-the-fly transformation is on, so we convert each
    layer's extent to 4326, then combine it.
    """
    extent = None
    for layer in list(QgsProject.instance().mapLayers().values()):
        transform = QgsCoordinateTransform(layer.crs(), WGS84, QgsProject.instance())
        layer_extent = transform.transformBoundingBox(layer.extent())
        if extent:
            extent.combineExtentWith(layer_extent)
        else:
            extent = layer_extent
    return extent_to_geojson(extent)


def map_canvas_extent(mapCanvas):
    settings = mapCanvas.mapSettings()
    transform = QgsCoordinateTransform(settings.destinationCrs(), WGS84, QgsProject.instance())
    return extent_to_geojson(transform.transformBoundingBox(settings.extent()))
