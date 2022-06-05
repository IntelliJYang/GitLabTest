import sys
from PyQt5.QtWidgets import QTableView, QFrame, QAbstractScrollArea, QAbstractItemView, QApplication
from PyQt5.QtCore import Qt, QFile
from GUI.resources import resources


class KTableView(QTableView):
    def __init__(self, parent=None):
        super(KTableView, self).__init__(parent)
        self.all_info = list()
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)

        self.load_style_sheet("qtableview")

    def set_columns_width(self, width_list=None):
        if width_list is None:
            width_list = [120, 250, 50, 50, 50]
        for i in range(len(width_list)):
            self.setColumnWidth(i, width_list[i])

    def load_style_sheet(self, sheet_name):

        qss_file = QFile(":/qss/%s.qss" % sheet_name.lower())
        qss_file.open(QFile.ReadOnly)
        style_sheet = qss_file.readAll()
        if sys.version_info < (3, 0):
            # Python v2.
            style_sheet = unicode(style_sheet, encoding='utf8')
        else:
            # Python v3.
            style_sheet = str(style_sheet)
        self.setStyleSheet(style_sheet)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = KTableView()
    view.set_columns_width()
    view.show()
    view.setGeometry(500, 50, 600, 480)
    sys.exit(app.exec_())
