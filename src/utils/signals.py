from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QObject


class PropertySignals(QObject):
    """Properties can have a signal related to its value and another signal
    used to allow dynamic property changes in the GUI.
       Some properties may only need to emit their values in which case
    its more practical to use the default pyqtsignal."""
    status = pyqtSignal(object)             # The property status (any object | bool | int | float | string)
    info = pyqtSignal(str, str)             # The dynamic property handles related to the property


    def emit(self, value: bool|int|float, prop: str=None, prop_value: str=None):
        """Emits the value and the dynamic property that must be changed

        Parameters
        ----------
        value : bool | int | float
            Property status value
        prop : str, optional
            Dynamic property that must be informed to the GUI, by default None
        prop_value : str, optional
            Dynamic property value, by default None
        """
        self.status.emit(value)
        if prop and prop_value:
            self.info.emit(prop, prop_value)    

class MultiSignal(QObject):
    """Some variables may need to be transmitted also as a string"""
    value = pyqtSignal(object)
    string = pyqtSignal(object)
    value_float = pyqtSignal(float)

    def emit(self, value: bool|int|float, value2orstring: bool | str | int | float=None, convert2string: bool=True):
        """Emits the variable value and its string OR emits two different values, being the second any other string, int or float

        :param value: Variable value to be transmitted
        :type value: bool | int | float
        """
        self.value.emit(int(value))
        print(f'*********emitted: {int(value)}')
        self.value_float.emit(float(value))
        if value2orstring is None and convert2string:
            self.string.emit(str(value))

        if value2orstring is not None:
            self.string.emit(value2orstring)