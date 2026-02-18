from PySide6.QtGui import QAction, QFont, QIcon, QShortcut, QKeySequence, QCursor, QColor

from PySide6.QtWidgets import (QApplication, QCheckBox, 
                            QGridLayout,  QHBoxLayout, 
                            QStyleFactory, QVBoxLayout, 
                            QWidget, QScrollArea, QToolBar,
                            QMainWindow, QLineEdit, QSpacerItem,
                            QPushButton, QMessageBox, QWidgetItem, QInputDialog, QLabel, QSizePolicy,
                            QTextEdit                                 
                            )

from PySide6.QtCore import QSize

import qtawesome

class SearchField(QWidget):

    IconSize = QSize(16, 16)
    HorizontalSpacing = 2

    def __init__(self, var):
        super().__init__()
        self.var = var
        self.setStyleSheet(self.var.theme.get("search").to_config())


        self.search = QLineEdit()
        self.layout = QHBoxLayout()
        self.icon = QLabel()
        self.icon_name = "fa6s.magnifying-glass"

        

        self.icon.setPixmap(qtawesome.icon(self.icon_name,color="white").pixmap(self.IconSize))

        self.layout.setContentsMargins(0, 0, 0, 0)        
        self.layout.addWidget(self.icon)
        self.layout.addSpacing(self.HorizontalSpacing)       
        self.layout.addWidget(self.search)

        self.setLayout(self.layout) 

        self.search.textChanged.connect(lambda : self.var.manager.search(self.search.text()))


    def clear(self):
        self.setText("")


  

    