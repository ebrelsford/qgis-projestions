# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProjestionsDialog
                                 A QGIS plugin
 projection suggestions
                             -------------------
        begin                : 2016-02-29
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Eric Brelsford
        email                : ebrelsford@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QColor
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsGeometry,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes
)
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsRubberBand

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'projestions_dialog_base.ui'))

class ProjestionsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ProjestionsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        layerPath = QgsApplication.instance().pkgDataPath() + '/resources/data/world_map.shp'
        self.mapLayers = [QgsVectorLayer(layerPath)]
        self.mapCrs = QgsCoordinateReferenceSystem(
            4326,
            QgsCoordinateReferenceSystem.EpsgCrsId
        )
        self.previewBand = QgsRubberBand(self.mAreaCanvas, QgsWkbTypes.PolygonGeometry)
    def show(self):
        self.mAreaCanvas.setDestinationCrs(self.mapCrs)
        self.mAreaCanvas.setLayers(self.mapLayers)
        self.mAreaCanvas.zoomToFullExtent()
        super().show()

    def set_crs(self, crsCode):
        crs = QgsCoordinateReferenceSystem(
            crsCode,
            QgsCoordinateReferenceSystem.EpsgCrsId
        )
        rect = crs.bounds()

        if rect.area() != 0.0:
            # Add bounding box to map
            geom = QgsGeometry.fromRect(rect)
            self.previewBand.setToGeometry(geom)
            self.previewBand.setColor(QColor(255, 0, 0, 65))

            # Zoom to extent of bounding box
            rect.scale(1.1)
            self.mAreaCanvas.setExtent(rect)
        else:
            self.previewBand.hide()
            self.mAreaCanvas.zoomToFullExtent()

        self.mAreaCanvas.refresh()
