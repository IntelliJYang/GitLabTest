import time
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex, pyqtSignal
from PyQt5.QtGui import QColor

from Configure import constant

TPHEADER = ["GROUP", "TID", "LSL", "USL", "UNIT"]
OFFSET = len(TPHEADER)
VIEWHEADER = TPHEADER[:]
for i in xrange(constant.SLOTS):
    VIEWHEADER.append("SLOT{}".format(i + 1))
RESULTS = [i + OFFSET for i in xrange(constant.SLOTS)]


class KTotalTableModel(QAbstractTableModel):

    tp_failed_row_signal = pyqtSignal(int, name='failed_row_signal')

    def __init__(self, selected_row_signal):
        super(KTotalTableModel, self).__init__()

        # 2d array for store result
        self._result = []
        # 2d array for store test plan values
        self._items = []
        self._selected_row_signal = selected_row_signal

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._items)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(VIEWHEADER)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        column = index.column()
        cur_row_item = self._items[row]
        if role == Qt.DisplayRole:
            return cur_row_item[column]
        elif role == Qt.TextColorRole:
            if column in RESULTS:
                result = self._result[column - OFFSET][row]
                if result:
                    return QColor(Qt.blue)
                else:
                    return QColor(Qt.red)
            return QColor(Qt.black)
        return QVariant()

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
                try:
                    return VIEWHEADER[section]
                except:
                    pass
            else:
                return str(section)
        elif role == Qt.TextAlignmentRole:
            return int(Qt.AlignHCenter)

    def insertColumns(self, position, columns, parent=None, *args, **kwargs):
        col_type = kwargs.get('col_type', None)
        data = kwargs.get('data', None)

        if col_type == 'test_plan' and data:
            self._result = []
            self.beginResetModel()
            self.beginRemoveColumns(QModelIndex(), 0, 4)
            self.endRemoveColumns()
            self.beginInsertColumns(QModelIndex(), position, position + columns - 1)
            rows = len(data[0])
            placeholder = [''] * rows
            for site in range(constant.SLOTS):
                self._result.append(["" for row in range(rows)])

            for site in range(len(VIEWHEADER) - len(data)):
                data.append(placeholder)
            self._items = map(list, zip(*data))
            self.endInsertColumns()
            self.endResetModel()
            return True
        else:
            return False

    def setData(self, index, value, role=Qt.EditRole):

        if index.isValid():
            row = index.row()
            column = index.column()
            if role == Qt.EditRole:
                self._items[row][column + OFFSET] = value
                self._selected_row_signal.emit(row)
                return True
            if role == Qt.TextColorRole:
                self._result[column][row] = value
                if not value:
                    self.tp_failed_row_signal.emit(row)
                return True
        return False

    def clean_column(self, site):
        column = site + OFFSET
        for row in range(self.rowCount()):
            self._items[row][column] = ''
            self._result[site][row] = ""
        self._selected_row_signal.emit(0)

    def get_items(self):
        return self._items

    def get_one_row(self, row, slot_undertest):
        _row = self._items[row]
        total = []
        for item in _row[OFFSET:]:
            if item != "":
                total.append(item)
        if len(total) >= slot_undertest:
            return [row] + _row
        else:
            return None

    def get_one_row_result(self, row):
        result = []
        for slot in self._result:
            result.append(slot[row])
        return result



    def get_values(self):
        return self._result
