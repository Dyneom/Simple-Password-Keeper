
from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect

from PySide6.QtGui import QImage


from PySide6.QtCore import QSize, QTimer, QPropertyAnimation, QEasingCurve

import qtawesome

class Spk_Indicator(QWidget):

    IconSize = QSize(16, 16)
    HorizontalSpacing = 2

    def __init__(self, text:str, color:str ):
        super().__init__()


        self.text_label = QLabel(text.rjust(12))
        self.layout = QHBoxLayout()
        self.icon = QLabel()
        self.icon_name = "fa6s.circle"        
        self.last_color = color
        self.last_text = text.rjust(12) 

       
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)        
        self.icon.setPixmap(qtawesome.icon(self.icon_name,color=color).pixmap(self.IconSize))

        self.layout.addWidget(self.text_label)
        self.layout.addSpacing(self.HorizontalSpacing)       
        self.layout.addWidget(self.icon)


        self.opacity_effect = QGraphicsOpacityEffect(opacity=1)
        self.text_label.setGraphicsEffect(self.opacity_effect)
        self.icon.setGraphicsEffect(self.opacity_effect)

    def set(self,text:str,color:str, was_tmp = False):
        if self.last_color == color and self.last_text == text.rjust(12) and not was_tmp: return
        if not was_tmp : 
            self.last_color = color
            self.last_text = text.rjust(12) 

        self.fade_out_custom(text=text,color=color)

        

    def temp_message(self,text : str,color : str,time : int = 1) :
        self.fade_out_custom(text=text, color=color, time=time)
        
        
    def fade_out_custom(self,text,color,time = 0):
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)        
        self.fade_out.finished.connect(lambda : self.fade_in_custom(text=text,color=color, time = time))
        self.fade_out.start()

    def fade_in_custom(self,text,color,time = 0):        
        self.text_label.setText(text.rjust(12))
        self.icon.setPixmap(qtawesome.icon(self.icon_name,color=color).pixmap(self.IconSize))

        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(200)
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if time != 0 : self.fade_in_anim.finished.connect(lambda : self.change_back(time=time))
        self.fade_in_anim.start()
        

    def change_back(self,time):        
        self.timer = QTimer(self)        
        self.timer.singleShot(time*1000,lambda : self.set(self.last_text,self.last_color,was_tmp=True)) # * 1000 to convert milli -> sec


        