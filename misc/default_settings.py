import string
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QMessageBox, QCheckBox, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QToolButton
from PyQt6.QtCore import pyqtSignal, Qt

from configparser import ConfigParser
import sys
import os

def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # No executável, sys._MEIPASS é a raiz da pasta temporária
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # No desenvolvimento, a base é a pasta raiz do projeto (onde está o main4.py)
        # Como este arquivo está em misc, pegamos o pai dele
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    return os.path.normpath(os.path.join(base_path, relative_path))

path_to_ui = resource_path('assets/ui/default_select.ui')                # Path to login UI

class LoadConfigForm(QDialog):

    _signal_selected_list = pyqtSignal(object)

    def __init__(self, message: str):
        super(LoadConfigForm, self).__init__()

        # Loads Ui file
        uic.loadUi(path_to_ui, self)    # type: ignore

        # Creates UI intellisense
        self.cbIpAddress: QCheckBox = self.findChild(QCheckBox, 'cbIpAddress')

        self.cbBacklash: QCheckBox = self.findChild(QCheckBox, 'cbBacklash')

        self.cbPosMax: QCheckBox = self.findChild(QCheckBox, 'cbPosMax')

        self.cbPark: QCheckBox = self.findChild(QCheckBox, 'cbPark')

        self.cbMaxSpeed: QCheckBox = self.findChild(QCheckBox, 'cbMaxSpeed')

        self.cbNormalSpeed: QCheckBox = self.findChild(QCheckBox, 'cbNormalSpeed')

        self.cbMinSpeed: QCheckBox = self.findChild(QCheckBox, 'cbMinSpeed')

        self.cbAcceleration: QCheckBox = self.findChild(QCheckBox, 'cbAcceleration')

        self.cbDeceleration: QCheckBox = self.findChild(QCheckBox, 'cbDeceleration')

        self.cbIdleCurrent: QCheckBox = self.findChild(QCheckBox, 'cbIdleCurrent')

        self.cbRunCurrent: QCheckBox = self.findChild(QCheckBox, 'cbRunCurrent')

        self.cbAccCurrent: QCheckBox = self.findChild(QCheckBox, 'cbAccCurrent')

        self.cbServerIP: QCheckBox = self.findChild(QCheckBox, 'cbServerIP')

        self.cbPortPub: QCheckBox = self.findChild(QCheckBox, 'cbPortPub')

        self.cbPortRep: QCheckBox = self.findChild(QCheckBox, 'cbPortRep')

        self.cbSubMask: QCheckBox = self.findChild(QCheckBox, 'cbSubMask')

        self.cbGatewayIP: QCheckBox = self.findChild(QCheckBox, 'cbGatwayIP')

        self.buttonBox: QDialogButtonBox = self.findChild(QDialogButtonBox, 'buttonBox')

        self.lblInfo: QLabel = self.findChild(QLabel, 'lblInfo')

        self.btnSelectParameters: QToolButton = self.findChild(QToolButton, 'btnSelectParameters')

        self.btnRemoveParameters: QToolButton = self.findChild(QToolButton, 'btnRemoveParameters')

        self.btnAddAll: QToolButton = self.findChild(QToolButton, 'btnAddAll')

        self.btnSelectParameters.clicked.connect(self._add_selected_items)
        self.btnRemoveParameters.clicked.connect(self._remove_all_parameters)
        self.btnAddAll.clicked.connect(self._add_all_parameters)

        # List widgets
        self.listParameters: QListWidget = self.findChild(QListWidget, 'listParameters')
        self.listSelectedParameters: QListWidget = self.findChild(QListWidget, 'listSelectedParameters')

        self.listParameters.doubleClicked.connect(self._add_selected_items)
        self.listSelectedParameters.itemChanged.connect(self._validate_selected_param)
        self.listSelectedParameters.doubleClicked.connect(self._remove_parameter)


        # for i in range(self.listParameters.count()):
        #     item = self.listParameters.item(i)
        #     for setting in ConfigurableSettings:
                
        #     item.setData(Qt.ItemDataRole.UserRole, )

        
        self.check_list = (self.cbIpAddress, self.cbBacklash, self.cbPosMax, self.cbPark,
                           self.cbMaxSpeed, self.cbNormalSpeed, self.cbMinSpeed, self.cbAcceleration,
                           self.cbDeceleration, self.cbIdleCurrent, self.cbRunCurrent, self.cbAccCurrent,
                           self.cbServerIP, self.cbPortPub, self.cbPortRep, self.cbSubMask, self.cbGatewayIP)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.lblInfo.setText(f"Selected parameters will be changed to its {message} value   ")
        self.setWindowTitle(message)

        #Variables
        self.selected_items=[]

    def accept(self):
        # for c in self.check_list:
        #     if c.isChecked():
        #         self.selected_items.append(c.property('TAG'))   # Gets the TAG for each selected item
        
        # for sel in self.selected_items:
        #     print(f"{sel} selected")

        # self._signal_selected_list.emit(self.selected_items)

        for i in range(self.listSelectedParameters.count()):
            item = self.listSelectedParameters.item(i)
            if item is not None:
                self.selected_items.append(item.statusTip())
        
        self._signal_selected_list.emit(self.selected_items)

        for sel in self.selected_items:
            print(f"{sel} selected")
        
        return super().accept()
    
    def _add_all_parameters(self):
        self.listParameters.selectAll()
        self._add_selected_items()
        self.listParameters.clearSelection()

    def _add_selected_items(self):

        selected_items = self.listParameters.selectedItems()

        for item in selected_items:
            item_clone = item.clone()
            if item_clone is not None:
                self.listSelectedParameters.addItem(item_clone)
                self._validate_selected_param(item_clone)


    def _validate_selected_param(self, item: QListWidgetItem):
        """Avoids duplicated parameters being put on the selected param list

        :param item: Item added to the list
        :type item: QListWidgetItem
        """
        
        items = self.listSelectedParameters.findItems(item.text(), Qt.MatchFlag.MatchExactly)
        # If more than one instance of the item is present on the list removes the last instance
        if len(items) > 1:
            temp = self.listSelectedParameters.takeItem(self.listSelectedParameters.row(item))
            if temp is not None:
                del temp
                # item = self.listSelectedParameters.takeItem(self.listSelectedParameters.row(item))
                # del item

    def _remove_all_parameters(self):
        self.listSelectedParameters.clear()
    
    def _remove_parameter(self):
        selected_item = self.listSelectedParameters.selectedIndexes()[0]
        item = self.listSelectedParameters.takeItem(selected_item.row())
        del item