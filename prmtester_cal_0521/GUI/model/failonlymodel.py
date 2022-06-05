#!/usr/bin/python

__author__ = "JinHui Huang"
__copyright__ = "Copyright 2019, PRMeasurement Inc."
__email__ = "jinhui.huang@prmeasure.com"

import time
from Configure import constant
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, QModelIndex
from collections import OrderedDict

TPHEADER = ["INDEX", "GROUP", "TID", "LSL", "USL", "UNIT"]
OFFSET = len(TPHEADER)
VIEWHEADER = TPHEADER[:]
for i in xrange(constant.SLOTS):
    VIEWHEADER.append("SLOT{}".format(i + 1))
RESULTS = [i + OFFSET for i in xrange(constant.SLOTS)]


class FailOnlyModel(QAbstractTableModel):
    def __init__(self, select_row_signal):
        super(FailOnlyModel, self).__init__()
        self._selected_row_signal = select_row_signal
        self._fail_items = []
        self._fail_results = []
        self._fail_row = OrderedDict()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._fail_items)

    def data(self, index, role=Qt.DisplayRole):
        if (not index.isValid() or
                not (0 <= index.row() < len(self._fail_items))):
            return QVariant()
        row = index.row()
        item = self._fail_items[row]
        column = index.column()
        # if role == Qt.DisplayRole:
        #     if column == 0:
        #         return item.get('index')
        #     elif column == 1:
        #         return item.get('group')
        #     elif column == 2:
        #         return item.get('tid')
        #     elif column == 3:
        #         return item.get('low')
        #     elif column == 4:
        #         return item.get('high')
        #     elif column == 5:
        #         return item.get('unit')
        #     elif column in range(6, 100):
        #         return item.get(str(column - 6))
        # elif role == Qt.TextColorRole:
        #     if column > 5:
        #         return QColor(Qt.red)
        #     else:
        #         return QColor(Qt.black)
        if role == Qt.DisplayRole:
            return item[column]
        elif role == Qt.TextColorRole:
            r = self._fail_results[row]
            if column > 5:
                if r[column - 6]:
                    return QColor(Qt.blue)
                else:
                    return QColor(Qt.red)
            else:
                return QColor(Qt.black)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(VIEWHEADER)

    def headerData(self, section, qt_orientation, role=None):
        """
        Returns the data for the given role and section in the header with the specified orientation.
        :param section:
        :param qt_orientation:
        :param role:
        :return:
        """

        if role == Qt.DisplayRole:
            if qt_orientation == Qt.Horizontal:
                return VIEWHEADER[section]
            else:
                return str(section)
        elif role == Qt.TextAlignmentRole:
            return int(Qt.AlignHCenter)

    def insert_fail_result(self, row, site, value, result, cur_row_dict):
        row_key = format(row, '05d')
        index = self._fail_row.get(row_key, None)
        if index is not None:
            self._fail_items[index][str(site)] = value
        else:
            self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
            self._fail_items.append(cur_row_dict)
            self._fail_row.update({row_key: len(self._fail_items) - 1})
            self._fail_items[len(self._fail_items) - 1]['index'] = row
            self._fail_items[len(self._fail_items) - 1][str(site)] = value
            self.endInsertRows()
        self._selected_row_signal.emit(self.rowCount() - 1)
        return True

    def insert_fail_row(self, data_list, r):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._fail_results.append(r)
        self._fail_items.append(data_list)
        self.endInsertRows()


    # def insert_fail_recode(self, result_dict):
    #     pass

    def clean_column(self, site):
        self.beginResetModel()
        self._fail_items = []
        self._fail_results = []
        self._fail_row.clear()
        self.endResetModel()
        self._selected_row_signal.emit(0)
