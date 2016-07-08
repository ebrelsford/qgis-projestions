# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Projestions
                                 A QGIS plugin
 projection suggestions
                             -------------------
        begin                : 2016-02-29
        copyright            : (C) 2016 by Eric Brelsford
        email                : ebrelsford@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Projestions class from file Projestions.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .projestions import Projestions
    return Projestions(iface)
