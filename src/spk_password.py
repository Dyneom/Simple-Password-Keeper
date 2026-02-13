import uuid as uuid_manager

from PySide6.QtGui import QColor, QCursor

from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QVBoxLayout, 
                               QWidget, QLineEdit, 
                               QPushButton,   QTextEdit   , QSizePolicy      
                            )

from PySide6.QtCore import Qt, QTimer
#spk
import logs
import spk_variables

class Password(QWidget): 
    def __init__(self, variables : spk_variables.SpkVariables, name = "Test", password_text="Password", uuid = ""):
        
        super().__init__()

        self.uuid= uuid_manager.uuid4() if uuid == "" else uuid        
        self.logger = logs.Logger(display=True,write_in_file=False,name="Password ("+str(uuid)+")")
        self.var = variables
        self.password_field = QTextEdit()        
        self.main_password_layout   = QVBoxLayout()       
        self.top_password_layout = QHBoxLayout()             
        self.password_name = QLineEdit(name)              
        self.show_button     = QCheckBox("Show")          
        self.edit_button     = QCheckBox("Edit")          
        self.supr_button = QPushButton("Del")  
        self.isEdited = False
        self.isShown = False

                  
        
        #PASSWORD NAME
        self.password_name.setStyleSheet(variables.theme.get("password_name").to_config())
        self.password_name.textChanged.connect(self.onPasswordNameChange)

        #PASSWORD FIELD
        pcolor = self.password_field.textColor()
        pcolor = QColor(self.var.theme.get("password_background").get("color"))
        
        pcolor.setAlpha(190)
        self.password_field.setTextColor(pcolor)
        self.password_field.setText(password_text)        
        self.password_field.setHidden(False) 
        self.password_field.setFixedHeight(0)
        self.password_field.setEnabled(False) # read only
        self.password_field.setStyleSheet(self.var.theme.get("password").to_config())
        self.password_field.textChanged.connect(self.onPasswordFieldChange)
                

        #"SHOW" BUTTON
        self.show_button.setTristate(False)
        self.show_button.setCheckable(True)
        self.show_button.setChecked(False)
        self.show_button.isChecked_=False 
        self.show_button.toggled.connect( self.onEchoChange)
        self.show_button.setStyleSheet(self.var.theme.get("show_button").to_config())


        # "EDIT BUTTON"
        self.edit_button.toggled_=False
        self.edit_button.toggled.connect(self.onEditChange)
        self.edit_button.setStyleSheet(self.var.theme.get("edit_button").to_config())

        
        #"SUPR BUTTON"        
        self.supr_button.setStyleSheet("QPushButton {"+self.var.theme.get("supr_button").to_config()+"} QPushButton:hover {"+self.var.theme.get("supr_button_hover").to_config()+"}")
        self.supr_button.setDefault(True)
        self.supr_button.clicked.connect(lambda : self.var.manager.deletePassword(self.uuid))
                

        # BUILDING LAYOUT
        
        ## HORIZONTAL
        self.top_password_layout.addWidget(self.password_name) 
        self.top_password_layout.addWidget(self.show_button) 
        self.top_password_layout.addWidget(self.edit_button) 
        self.top_password_layout.addWidget(self.supr_button) 

        ## VERTICAL
        self.main_password_layout.addLayout(self.top_password_layout)
        self.main_password_layout.addWidget(self.password_field)   
             
        
        self.setLayout(self.main_password_layout)        
        #self.var.password_list = []
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(self.var.theme.get("password_background").to_config())  


        
        
        
    
    def onEchoChange(self):         
        if self.isShown == False :         
               
            self.resize()
 
            self.logger.add("The password is now displayed",self.logger.information)              
            self.isShown = True  
            self.var.current_shown_fields.append(self.password_field)

                     
        else :         
            
            self.resize(0)                      
            self.logger.add("The password is now hidden",self.logger.information) 
            self.isShown = False
            if self in self.var.current_shown_fields : self.var.current_shown_fields.remove(self) # it should be 
 
    def onEditChange(self): 
        
        if not self.isEdited:
            if self.var.current_field_edited == None or not self.var.current_field_edited.isEmpty():
                if self.var.current_field_edited != None : self.var.current_field_edited.untoggleEditing()
                self.toggleEditing()
                self.var.current_field_edited = self
            else: # the current field is empty
                self.untoggleEditing() # to set the "Edit" button to false
                self.var.indicator.temp_message("Empty field","red",1)

        else : # self.isEdited == True
            if self.var.current_field_edited == self and self.isEmpty():
                self.var.indicator.temp_message("Empty field","red",1)
                self.edit_button.setChecked(True)
            else:
                self.untoggleEditing()
                self.var.current_field_edited = None

    def onPasswordNameChange(self):
        self.var.resetMousePos()
        self.var.indicator.set("Not saved","blue")

    def onPasswordFieldChange(self):          
        self.var.indicator.set("Not saved","blue")
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


        
            
            
           
           
        

    def untoggleEditing(self): 
        wasEdited = self.isEdited
        self.isEdited = False         
        self.password_field.setEnabled(False)
        self.edit_button.setChecked(False)
        return True
        


    def toggleEditing(self):
        self.isEdited = True
        self.password_field.setEnabled(True)
        self.edit_button.setChecked(True)

        #Show password        
        self.show_button.setChecked(True) # will call onEchoChange
        


    def getText(self):
        return self.password_field.toPlainText()
        #return self.password_field.toHtml() #maybe in the future 
    
    def isEmpty(self):
        return self.getText()==""

