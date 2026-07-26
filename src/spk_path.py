from __future__ import annotations 
from hashlib import pbkdf2_hmac # sha256



from PySide6.QtGui import QAction, QIcon, QShortcut, QKeySequence, QCursor, QPainter, QPen, QColor

from PySide6.QtWidgets import ( 
                            QGridLayout, QVBoxLayout, QWidget, 
                            QScrollArea, QToolBar, QMainWindow, 
                            QLineEdit, QSpacerItem, QMessageBox, 
                            QWidgetItem, QInputDialog,  QSizePolicy  , QToolButton, QMenu, QLabel                              
                            )

from PySide6.QtCore import QTimer, Qt, QSocketNotifier, QPoint

import qtawesome
import time as func_timer
import uuid as uuid_manager
import argon2
import base64
import os 
import socket
import subprocess
from cryptography.fernet import Fernet
 
#spk
import spk_logs
import spk_file_manager
import spk_indicator
import spk_password
import spk_variables
import spk_search_field
import spk_folder
import spk_selection



class SpkPath(QLabel):

    def __init__(self,var,text = ""):
        super().__init__(text)
        self.var = var
        self.setStyleSheet(var.theme.get("path").to_config())

    def refresh(self):
        self.setText(self.var.current_node.getPath())
