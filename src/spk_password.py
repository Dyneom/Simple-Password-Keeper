import uuid as uuid_manager

from PySide6.QtGui import QColor, QDrag, QPixmap, QPainter, QPen

from PySide6.QtWidgets import (
                            QCheckBox, QHBoxLayout, QVBoxLayout, 
                            QWidget, QLineEdit, QPushButton,   
                            QTextEdit
                            )

from PySide6.QtCore import Qt, QTimer, QMimeData, QPoint
from rapidfuzz import process, fuzz

import qtawesome
#spk
import logs
import spk_variables
import spk_folder


def contains(string:str, l: list[str]) -> bool:
    for i in l:
        if string.find(i)!=-1: return True
    return False

class PasswordName(QLineEdit):
    def __init__(self,text,func_mouse_release):        
        super().__init__(text)
        self.func_mouse_release = func_mouse_release # to select the password
        self.setReadOnly(True)
        self.timer : QTimer = None


    def mouseDoubleClickEvent(self, arg__1):       
        if self.isReadOnly():
            if isinstance(self.timer,QTimer):                
                self.timer.stop() # stop the timer to cancel the selection
                              
            self.setReadOnly(False)
            self.selectAll()

        

    def mouseReleaseEvent(self, arg__1):        
        if self.isReadOnly(): 
            interval = 100 
            self.timer = QTimer(self)        
            self.timer.timeout.connect(self.func_mouse_release)
            self.timer.setInterval(interval) #cannot stop it if it is a singleshot 

            self.timer_stopper = QTimer(self) 
            
            self.timer_stopper.singleShot(interval*1.5,self.timer.stop) #stop the timer automaticaly before it runs twice

            self.timer.start()            

        return super().mouseReleaseEvent(arg__1)
      
    
    def focusOutEvent(self, arg__1):
        self.setReadOnly(True)
        return super().focusOutEvent(arg__1)
    
    def keyPressEvent(self, arg__1):
        if arg__1.key() == 16777220: #enter key:
            self.setReadOnly(True) 
            self.setSelection(0,0)
                 
        return super().keyPressEvent(arg__1)

class Push(QPushButton):  
    def __init__(self,action_func)  :
        super().__init__()
        self.action = action_func
    def keyPressEvent(self, arg__1):
        if arg__1.key() == 16777220: 
            self.action()
        return super().keyPressEvent(arg__1)

class Password(QWidget): 
    def __init__(self, variables : spk_variables.SpkVariables,parent, name = "Test", password_text="Password", uuid = "",bypass_uuid_check=False,**kwargs):
        
        super().__init__()

        self.uuid= uuid_manager.uuid4() if uuid == "" else uuid 
        while not bypass_uuid_check and self.uuid in variables.uuids:
            variables.global_logs.add(f"Cannot create the password \"{name}\". The uuid already exists","error")  
            self.uuid= uuid_manager.uuid4() 
        variables.uuids.append(self.uuid)
            
        self.logger = logs.Logger(display=True,write_in_file=False,name="Password ("+str(uuid)+")")
        self.var = variables

        self.password_field = QTextEdit()        
        self.main_password_layout   = QVBoxLayout()       
        self.top_password_layout = QHBoxLayout()             
        self.password_name = PasswordName(name,lambda : ...)    
                  
        
        self.push = Push(self.onEchoChange)       
        self.copy_button =  QPushButton()
        self.selected_check = QCheckBox()
        
        
        self.isEdited = False
        self.isShown = False
        self.config_height = int(self.var.theme.get("password_size").get("password_size"))
        if kwargs.get("bypassParent") != True:
            self.parent_folder = parent if isinstance(parent,spk_folder.Folder) else variables.root       
            self.parent_folder.addChild(self)
        
        #PASSWORD NAME
        self.password_name.setStyleSheet(variables.theme.get("password_name").to_config())
        self.password_name.textChanged.connect(self.onPasswordNameChange)

        #PASSWORD FIELD
        pcolor = self.password_field.textColor()
        pcolor = QColor(self.var.theme.get("password_background").get("color"))
        
        pcolor.setAlpha(int(self.var.theme.get("password_color_alpha").get("password_color_alpha")))
        self.pcolor = pcolor
        self.password_field.setTextColor(pcolor)
        self.password_field.setText(password_text)        
        self.password_field.setHidden(False) 
        self.password_field.setFixedHeight(0)
        self.password_field.setEnabled(False) # read only
        self.password_field.setStyleSheet(self.var.theme.get("password").to_config())
        self.password_field.textChanged.connect(self.onPasswordFieldChange)
        

        #ARROW BUTTON
        self.push.setIcon(qtawesome.icon("fa6s.angle-down",color="white"))         
        self.push.setCheckable(True)
        self.push.setChecked(False)        
        self.push.toggled.connect( self.onEchoChange)
        self.push.setStyleSheet(self.var.theme.get("show_button").to_config())
        
        #COPY BUTTON
        self.copy_button.setIcon(qtawesome.icon("fa6s.angle-left",color="white")) 
        self.copy_button.setCheckable(True)
        self.copy_button.setChecked(False)
        self.copy_button.toggled.connect(self.switchCopy)          
        self.copy_button.setStyleSheet(self.var.theme.get("show_button").to_config())

        #SELCTION CHECKMARK
        self.selected_check.setCheckable(True)
        self.selected_check.setChecked(False)
        self.selected_check.setStyleSheet(self.var.theme.get("show_button").to_config())
        self.selected_check.clicked.connect(lambda : self.var.selection.add(self))
        

        # BUILDING LAYOUT
        
        ## HORIZONTAL
        self.top_password_layout.addWidget(self.selected_check)
        self.top_password_layout.addWidget(self.password_name) 
        self.top_password_layout.addWidget(self.push) 
        self.top_password_layout.addWidget(self.copy_button) 
        
        

        ## VERTICAL
        self.main_password_layout.addLayout(self.top_password_layout)
        self.main_password_layout.addWidget(self.password_field)   
             
        
        self.setLayout(self.main_password_layout)        
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(self.var.theme.get("password_background").to_config())  
        self.setMaximumHeight(self.config_height)        
        

        

    def onEchoChange(self):         
        if self.isShown == False :                
            self.resize() 
            self.logger.add("The password is now displayed",self.logger.information)              
            self.isShown = True  
            self.var.current_shown_fields.append(self.password_field)
            self.setMaximumHeight(1000000)
            self.push.setIcon(qtawesome.icon("fa6s.angle-up",color="white"))  
            self.password_field.setEnabled(True)
                     
        else :         
            
            self.resize(0)                      
            self.logger.add("The password is now hidden",self.logger.information) 
            self.isShown = False
            self.setMaximumHeight(self.config_height)
            if self in self.var.current_shown_fields : self.var.current_shown_fields.remove(self) # it should be 
            self.push.setIcon(qtawesome.icon("fa6s.angle-down",color="white"))  
            self.password_field.setEnabled(False)

    
    def onPasswordNameChange(self):        
        self.var.resetMousePos()        
        self.var.manager.file_encryption_manager.setSaved(False)    

    def onPasswordFieldChange(self):         
        self.var.manager.file_encryption_manager.setSaved(False)    
        self.var.resetMousePos()
        self.resize()
        if self.getText()=="":
            self.password_field.setStyleSheet(self.var.theme.get("password_warning").to_config())        
        else:
            self.password_field.setStyleSheet(self.var.theme.get("password").to_config())
    

    def resize(self,target_height = -1,no_flick = False):
        if target_height == -1 :  target_height = max(self.password_field.document().size().height()+self.password_field.contentsMargins().top()+self.password_field.contentsMargins().bottom(),self.var.minimum_password_field_height )  
        if target_height >= 0 and target_height != self.password_field.height(): 
            self.var.manager.setUpdatesEnabled(False) 
            self.password_field.setFixedHeight(target_height)                             
            self.var.manager.setUpdatesEnabled(True)
            self.password_field.setTextColor(self.pcolor)

    def getText(self):
        return self.password_field.toPlainText()
        #return self.password_field.toHtml() #maybe in the future 
    
    def isEmpty(self):
        return self.getText()==""
    
    def show(self):
        self.setHidden(False)

    def hide(self):
        self.setHidden(True)

    def find(self,word: str):
        if word == "": return True
        threshold = 80        
        name = process.extract(word.lower(), self.password_name.text().lower().split(), scorer=fuzz.WRatio)
        pw = process.extract(word.lower(), self.getText().lower().split(), scorer=fuzz.WRatio)
        is_in_name = False
        is_in_pw = False
        if len(name)> 0 : is_in_name = name[0][1]> threshold
        elif len(pw)> 0 : is_in_pw = pw[0][1]> threshold        
        return is_in_name or is_in_pw
    
    def appear_selected(self):
        self.setStyleSheet(self.var.theme.get("password_background_selected").to_config())              
        self.selected_check.setChecked(True)        

    def appear_normal(self):
        self.setStyleSheet(self.var.theme.get("password_background").to_config()) 
        self.selected_check.setChecked(False)        


    #does nothing for now
    def mouseReleaseEvent(self, event):
        
        #self.var.selection.add(self) 

        return super().mouseReleaseEvent(event)

    def copy(self,parent,memo,bypassParent):
        if memo.get(id(self)) != None:
            print("Anti-copy working (pw)")            
            return memo[id(self)]
        
        if parent == None  :
            parent = self.var.root
        f = Password(self.var,parent=parent,name=self.password_name.text(),password_text=self.getText(),uuid = self.uuid,bypass_uuid_check=True,bypassParent=bypassParent)
        return f

    def delete(self):
        if self in self.parent_folder.children_list:
            self.parent_folder.children_list.remove(self)        
        if self in self.var.current_shown_fields:
            self.var.current_shown_fields.remove(self)
        self.var.selection.remove(self)
        self.var.manager.file_encryption_manager.setSaved(False)    
      
    def to_save_string(self): # create a string which will be used to save the password info (see spk_manager.save)
        chr1,chr2,_,_ = self.var.character
        name : str = self.password_name.text()
        pw=self.getText()
        uuid = self.uuid

        
        if contains(name,self.var.character) or contains(pw,self.var.character): # avoid corruption
            self.wrong_character_popup()
            self.logger.add(f"The password named {name} wasn't saved due to an unauthorised character",self.logger.critical_error)
            return ""
        else:
            return chr1+name+ chr1+str(uuid) +chr1+pw
        #save file 
        #password : chr1, name , chr1, uuid, chr1 , password
        #folder : chr2, name , chr2, uuid , chr2 , children

    def mouseMoveEvent(self, e):
       if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

    def __bool__(self):
        return True

    def toCopy(self): #func to set the current password as the password to copy
        print("Set to copy !")
        if self.var.passwordToCopy : self.var.passwordToCopy.unCopy()
        self.var.passwordToCopy = self


    def unCopy(self): #func to untoggle copy 
        self.copy_button.setChecked(False)
        self.var.passwordToCopy = None

    def switchCopy(self):
        if self.copy_button.isChecked :
            self.toCopy()
        else:
            self.var.passwordToCopy = None


    

