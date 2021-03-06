# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Projestions
                                 A QGIS plugin
 A projection picker
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
from PyQt5 import QtCore, QtGui, QtWidgets
import os.path
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsVectorLayer
)
from qgis.gui import QgsMessageBar
import traceback
from urllib.error import URLError

from . import projestions_api
from . import projestions_geoms
# Initialize Qt resources from file resources.py
from . import resources
from . import settings

# Import the code for the dialog
from .projestions_dialog import ProjestionsDialog


class CrsTableModel(QtCore.QAbstractTableModel):

    header_labels = ['epsg code', 'area code', 'region', 'units']

    def __init__(self, parent=None, *args):
        super(CrsTableModel, self).__init__(parent, *args)
        self.items = []

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if (role == QtCore.Qt.DisplayRole and
                orientation == QtCore.Qt.Horizontal):
            return self.header_labels[section]
        return QtCore.QAbstractTableModel.headerData(self, section,
                                                     orientation, role)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def setItems(self, items):
        self.layoutAboutToBeChanged.emit()
        self.items = list(items)
        self.layoutChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        if index.row() >= len(self.items):
            return None

        item = self.items[index.row()]
        column = index.column()
        if column == 0:
            return item['coord_ref_sys_code']
        elif column == 1:
            return item['coord_ref_sys_name']
        elif column == 2:
            return item['area_name']
        elif column == 3:
            return item['unit_of_meas_name']
        else:
            return None


class LoadCrssThread(QtCore.QThread):

    DROPDOWN_CHOICES = [
        'ACTIVE_LAYER_BBOX',
        'ACTIVE_LAYER_GEOM',
        'PROJECT',
        'MAP_CANVAS',
    ]

    warningSent = QtCore.pyqtSignal(str)
    taskFinished = QtCore.pyqtSignal(list)

    def __init__(self, iface, extentComboBox, tableModel, **kwargs):
        super(LoadCrssThread, self).__init__(**kwargs)
        self.iface = iface
        self.extentComboBox = extentComboBox
        self.tableModel = tableModel

    def active_layer_extent(self):
        if self.iface.activeLayer():
            return projestions_geoms.layer_extent(self.iface.activeLayer())
        else:
            self.warningSent.emit('Please select a layer before using the '
                                  'active layer option')
            return None

    def active_layer_geom(self):
        if self.iface.activeLayer():
            return projestions_geoms.layer_geom(self.iface.activeLayer())
        else:
            self.warningSent.emit('Please select a layer before using the '
                                  'active layer option')
            return None

    def project_extent(self):
        return projestions_geoms.project_extent()

    def map_canvas_extent(self):
        return projestions_geoms.map_canvas_extent(self.iface.mapCanvas())

    def geojson(self):
        index = self.extentComboBox.currentIndex()
        choice = self.DROPDOWN_CHOICES[index]

        if choice == 'ACTIVE_LAYER_GEOM':
            return self.active_layer_geom()
        elif choice == 'ACTIVE_LAYER_BBOX':
            return self.active_layer_extent()
        elif choice == 'PROJECT':
            return self.project_extent()
        elif choice == 'MAP_CANVAS':
            return self.map_canvas_extent()
        return None

    def run(self):
        geojson = self.geojson()
        projestions = []
        if geojson:
            try:
                projestions = projestions_api.get_projestions(geojson)
            except URLError as e:
                msg = 'URLError while loading projestions: %s' % str(e)
                QgsApplication.instance().messageLog().logMessage(msg, tag="Projestions",
                                         level=Qgis.MessageLevel(1))
                self.warningSent.emit('Failed to get projestions from API. '
                                      'Please try again and see the error log '
                                      'for details.')
            except Exception as e:
                msg = '%s while loading projections' % type(e).__name__
                QgsApplication.instance().messageLog().logMessage(msg, tag="Projestions",
                                         level=Qgis.MessageLevel(1))
                QgsApplication.instance().messageLog().logMessage(traceback.format_exc(),
                                         tag="Projestions",
                                         level=Qgis.MessageLevel(1))
                self.warningSent.emit('Failed to get projestions from API. '
                                      'Please try again and see the error log '
                                      'for details.')

        self.taskFinished.emit(projestions)
        self.quit()


class LoadCrssProgressBar(QtWidgets.QProgressBar):

    def __init__(self, parent=None, iface=None, extentComboBox=None,
                 tableModel=None, plugin=None):
        super(LoadCrssProgressBar, self).__init__(parent)
        self.iface = iface
        self.extentComboBox = extentComboBox
        self.tableModel = tableModel
        self.plugin = plugin
        self.setRange(0, 1)

    def onStart(self):
        """Clear progress bar, current CRSs, and start loading new ones"""
        self.setRange(0, 0)
        self.tableModel.setItems([])

        # Set up signals
        self.loadCrssThread = LoadCrssThread(self.iface, self.extentComboBox,
                                             self.tableModel)
        self.loadCrssThread.taskFinished.connect(self.onFinished)
        self.loadCrssThread.warningSent.connect(self.onWarning)
        self.loadCrssThread.start()

    def onFinished(self, projestions):
        """Stop the progress bar"""
        self.tableModel.setItems(projestions)

        self.setRange(0, 1)
        self.loadCrssThread.taskFinished.disconnect(self.onFinished)
        self.loadCrssThread.warningSent.disconnect(self.onWarning)
        self.loadCrssThread = None

    def onWarning(self, warning):
        self.iface.messageBar().pushMessage('Warning', warning,
                                            Qgis.MessageLevel(1))


class Projestions:
    """Main Projestions Plugin Implementation"""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QtCore.QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n',
                                   'Projestions_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QtCore.QTranslator()
            self.translator.load(locale_path)

            if QtCore.qVersion() > '4.3.3':
                QtCore.QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = ProjestionsDialog()

        # Set up search button
        try:
            self.dlg.searchButton.clicked.disconnect(self.exec_search_button)
        except Exception:
            pass
        self.dlg.searchButton.clicked.connect(self.exec_search_button)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Projestions')
        self.toolbar = self.iface.addToolBar('Projestions')
        self.toolbar.setObjectName('Projestions')
        self.tableModel = CrsTableModel(self.dlg)

        # Set up progress bar
        self.progressBar = LoadCrssProgressBar(self.dlg, self.iface,
                                               self.dlg.extentComboBox,
                                               self.tableModel, self)
        self.dlg.buttonLayout.insertWidget(0, self.progressBar)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QtCore.QCoreApplication.translate('Projestions', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, status_tip=None,
                   whats_this=None, parent=None):
        icon = QtGui.QIcon(icon_path)
        action = QtWidgets.QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/Projestions/icon.png'
        self.add_action(icon_path, text=self.tr('Projestions'),
                        callback=self.run, parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr('&Projestions'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def on_crs_select(self, current):
        crsCode = current.siblingAtColumn(0).data()
        self.dlg.set_crs(crsCode)

    def exec_search_button(self):
        # Set up the table model to receive CRS list
        self.sortableTableModel = QtCore.QSortFilterProxyModel()
        self.sortableTableModel.setSourceModel(self.tableModel)
        self.dlg.crsTableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.dlg.crsTableView.setModel(self.sortableTableModel)
        self.dlg.crsTableView.selectionModel().currentRowChanged.connect(self.on_crs_select)

        # Aaaaaand go!
        self.progressBar.onStart()

    def run(self):
        """Run method that performs all the real work"""
        self.dlg.show()

        if settings.DEBUG:
            def writelogmessage(message, tag, level):
                with open('/home/eric/tmp/qgis.log', 'a') as logfile:
                    logfile.write('{}({}): {}'.format(tag, level, message))
            QgsApplication.instance().messageLog().messageReceived.connect(writelogmessage)

        if self.dlg.exec_():
            try:
                item = self.dlg.crsTableView.selectionModel().selectedRows()[0]
                row = item.row()
                data = item.data()
                new_crs = QgsCoordinateReferenceSystem(
                    data,
                    QgsCoordinateReferenceSystem.EpsgCrsId
                )
                QgsProject.instance().setCrs(new_crs)
            except IndexError:
                pass
