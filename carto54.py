# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Carto54
                                 A QGIS plugin
 This plugins is used to add more customization to the Carto54 Web app
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-06-30
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Conseil Départemental de Meurthe-et-Moselle
        email                : hvitoux@departement54.fr
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .carto54_dialog import Carto54Dialog
import os.path

from .utils.output import Output
from .utils.table import fill_table
from .utils import server


class Carto54:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Carto54_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Carto54')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        return QCoreApplication.translate('Carto54', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/carto54/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Carto54 - Configuration'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Carto54'),
                action)
            self.iface.removeToolBarIcon(action)

    def destination(self):
        return self.dlg.ipt_dest.text()

    def host(self):
        return self.dlg.ipt_host.text()

    def add_qp_row(self):
        server.add_row(self.dlg.tw_qp)

    def delete_qp_row(self):
        table = self.dlg.tw_qp
        for item in table.selectedItems():
            table.removeRow(item.row())

    def fill_display_table(self, output):
        fill_table(self.dlg.tw_display, output.fields())

    def handle_check(self, item, output):
        isChecked, attribute = item.checkState() == Qt.Checked, item.data(1)
        row = self.dlg.tw_display.row(item)
        field_name = self.dlg.tw_display.item(row, 0).text()
        matching_field = output.field(field_name)
        if isChecked:
            matching_field["options"][attribute] = True
        else:
            matching_field["options"][attribute] = False

    def generate_output(self, output):
        """
        Save the output
        """
        output.set_query_params(server.query_params(self.dlg.tw_qp))
        print(output.__dict__)
        #output.save()
        #self.dlg.close()

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started

        # Default values
        default_directory = QgsProject.instance().absolutePath()
        layers = QgsProject.instance().mapLayers().values()

        # Creating Output instance
        output = Output(default_directory)
        output.generate_form(layers)

        if self.first_start:
            self.first_start = False
            self.dlg = Carto54Dialog()

            # Setting default values
            self.dlg.ipt_dest.setText(default_directory)

            # Config display table
            self.dlg.tw_display.setRowCount(len(output.fields()))
            self.fill_display_table(output)

            # Listening input changes
            self.dlg.ipt_dest.editingFinished.connect(lambda: output.set_directory(self.destination()))
            self.dlg.ipt_host.editingFinished.connect(lambda: output.set_host(self.host()))

            # Listening table items changes
            self.dlg.tw_display.itemChanged.connect(lambda item: self.handle_check(item, output))

            # Listening clicks on buttons
            self.dlg.btn_add_qp.clicked.connect(self.add_qp_row)
            self.dlg.btn_delete_qp.clicked.connect(self.delete_qp_row)
            self.dlg.btn_cancel.clicked.connect(self.dlg.close)
            self.dlg.btn_generate.clicked.connect(lambda: self.generate_output(output))

        # show the dialog
        self.dlg.show()


