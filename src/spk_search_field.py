from PySide6.QtGui import QAction, QFont, QIcon, QShortcut, QKeySequence, QCursor, QColor

from PySide6.QtWidgets import (QApplication, QCheckBox, 
                            QGridLayout,  QHBoxLayout, 
                            QStyleFactory, QVBoxLayout, 
                            QWidget, QScrollArea, QToolBar,
                            QMainWindow, QLineEdit, QSpacerItem,
                            QPushButton, QMessageBox, QWidgetItem, QInputDialog, QLabel, QSizePolicy,
                            QTextEdit         
                            )


class SearchField(QLineEdit):


    def __init__(self, var):
        super().__init__()
        self.var = var
        self.textChanged.connect(lambda : self.var.manager.search(self.text()))

    def clear(self):
        self.setText("")

  

    