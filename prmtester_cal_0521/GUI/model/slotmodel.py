#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant, pyqtSignal
from PyQt5.QtGui import QColor

# Define the column of this model
STATUS, GROUP, TID, LSL, USL, UNIT, VALUE, DESCRIPTION, RESULT = range(9)

start = {u'group': u'TEST2', u'description': u'', u'to_pdca': True, u'high': u'', u'low': u'', u'tid': u'STEP1997',
         u'unit': u''}

finish = {u'tid': u'STEP1997', u'to_pdca': True, u'result': True, u'value': 2994.0}


class SlotTpTableModel(QAbstractTableModel):

    def __init__(self, select_row_signal):
        super(SlotTpTableModel, self).__init__()
        self.items = []
        self._select_row_signal = select_row_signal

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.items)

    def columnCount(self, parent=None, *args, **kwargs):
        return 8

    def data(self, index, role=Qt.DisplayRole):
        """
        :param index:
        :param role:
        :return:
        """
        if (not index.isValid() or
                not (0 <= index.row() < len(self.items))):
            return QVariant()
        item = self.items[index.row()]
        column = index.column()
        if role == Qt.DisplayRole:
            if column == GROUP:
                return item.get('group')
            elif column == TID:
                return item.get('tid')
            elif column == LSL:
                return item.get('low')
            elif column == USL:
                return item.get('high')
            elif column == UNIT:
                return item.get('unit')
            elif column == VALUE:
                return item.get('value')
            elif column == DESCRIPTION:
                return item.get('description')
            elif column == RESULT:
                return item.get('result')
            elif column == STATUS:
                if item.get('result') == 1:
                    return QVariant("Pass")
                elif item.get('result') == 2:
                    return QVariant("SKIP")
                else:
                    return QVariant("Fail")
        elif role == Qt.TextColorRole:
            if column == STATUS or column == VALUE:
                if item.get('result') == 1:
                    return QColor(Qt.green)
                elif item.get('result') == 2:
                    return QColor(Qt.yellow)
                else:
                    return QColor(Qt.red)
            return QColor(Qt.black)

    def headerData(self, section, orientation, role=None):
        """
        set the title of this model
        :param section:
        :param orientation:
        :param role:
        :return:
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == GROUP:
                    return QVariant("Group")
                elif section == TID:
                    return QVariant("TID")
                elif section == LSL:
                    return QVariant("LSL")
                elif section == USL:
                    return QVariant("USL")
                elif section == UNIT:
                    return QVariant("UNIT")
                elif section == VALUE:
                    return QVariant("VALUE")
                elif section == DESCRIPTION:
                    return QVariant("DESCRIPTION")
                elif section == RESULT:
                    return QVariant("RESULT")
                elif section == STATUS:
                    return QVariant("Status")

    def insertRows(self, position=1, rows=1, parent=None, *args, **kwargs):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        data = kwargs.get('data')
        self.items.append(dict(data))
        self.endInsertRows()
        self._select_row_signal.emit(self.rowCount() - 1)
        return True

    def clear(self):
        """
        clear the mode,clear self.item = list()
        :return:
        """
        self.beginResetModel()
        self.items = []
        self.endResetModel()
