from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys


class PaletteTableModel(QtCore.QAbstractTableModel):
    def __init__(self, colors=[[]], parent=None):
        super(PaletteTableModel, self).__init__(parent)
        self._colors = colors

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._colors)

    def columnCount(self, *args, **kwargs):
        return len(self._colors[0])

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=None):
        row = index.row()
        column = index.column()
        if role == QtCore.Qt.ToolTipRole:
            return self._colors[row][column].name()

        if role == QtCore.Qt.DecorationRole:
            value = self._colors[row][column]
            pixmap = QtGui.QPixmap(26, 26)
            pixmap.fill(value)
            icon = QtGui.QIcon(pixmap)
            return icon

        if role == QtCore.Qt.DisplayRole:
            value = self._colors[row][column]
            return value.name()

        if role == QtCore.Qt.EditRole:
            return self._colors[row][column].name()

    def setData(self, index, value, role=None):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            color = QtGui.QColor(value)
            if color.isValid():
                self._colors[row][column] = color
                self.dataChanged.emit(index, index)
                return True
        return False


class PaletteListModel(QtCore.QAbstractListModel):
    def __init__(self, colors=[], parent=None):
        super(PaletteListModel, self).__init__(parent)
        self._colors = colors

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._colors)

    def data(self, index, role=None):
        if role == QtCore.Qt.ToolTipRole:
            return self._colors[index.row()].name()

        if role == QtCore.Qt.DecorationRole:
            row = index.row()
            value = self._colors[row]
            pixmap = QtGui.QPixmap(26, 26)
            pixmap.fill(value)
            icon = QtGui.QIcon(pixmap)
            return icon

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            value = self._colors[row]
            return value.name()

        if role == QtCore.Qt.EditRole:
            return self._colors[index.row()].name()

    def headerData(self, section, orientation, role=None):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return 'Palette'
            else:
                return str(section)

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=None):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            color = QtGui.QColor(value)
            if color.isValid():
                self._colors[row] = color
                self.dataChanged.emit(index, index)
                return True
        return False

    def insertColumns(self, position, columns, parent=None, *args, **kwargs):
        pass

    def insertRows(self, position, rows, parent=None, *args, **kwargs):
        self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            self._colors.insert(position, QtGui.QColor("#000000"))
        self.endInsertRows()

        return True

    def removeRows(self, p_int, p_int_1, parent=None, *args, **kwargs):
        self.beginRemoveRows()

        self.endRemoveRows()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('cleanlooks')

    panel = QtWidgets.QWidget()
    panel.setGeometry(300, 40, 300, 300)
    # data = ['one', 'two', 'three', 'four', 'five']

    red = QtGui.QColor('#ff0000')
    green = QtGui.QColor('#00ff00')
    blue = QtGui.QColor('#0000ff')
    data = [red, green, blue]

    # model = PaletteListModel(data)
    # tabledata = [
    #     ['1', '2', '3', '4', '5'],
    #     ['11', '22', '33', '44', '55'],
    #     ['111', '222', '333', '444', '555'],
    #     ['1111', '222', '3333', '4444', '5555'],
    #     ['11111', '22222', '33333', '44444', '55555']
    #
    # ]
    rowcount = 4
    columncount = 6
    tabledata = [[QtGui.QColor('#ffff00') for i in range(columncount)] for j in range(rowcount)]
    model = PaletteTableModel(tabledata)

    listview = QtWidgets.QListView()
    listview.setModel(model)

    combobox = QtWidgets.QComboBox()
    combobox.setModel(model)

    treeview = QtWidgets.QTreeView()
    # treeview.setModel(model)

    tableview = QtWidgets.QTableView()
    tableview.setModel(model)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(listview)
    layout.addWidget(combobox)
    # layout.addWidget(treeview)
    layout.addWidget(tableview)
    panel.setLayout(layout)
    panel.show()

    # model.insertRows(0, 5, QtCore.QModelIndex())

    sys.exit(app.exec_())
