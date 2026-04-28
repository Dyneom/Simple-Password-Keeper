import uuid as uuid_manager

from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
                            QCheckBox, QHBoxLayout, QVBoxLayout, 
                            QWidget, QLineEdit, QPushButton,   
                            QTextEdit 
                            )

from PySide6.QtCore import Qt
from rapidfuzz import process, fuzz



#spk
import logs
import spk_variables



class Folder(QWidget): 
    def __init__(self, variables : spk_variables.SpkVariables, parent, name = "New folder", children: list =[], uuid = "",bypass_uuid_check=False,**kwargs):
        
        super().__init__()
        
        self.uuid= uuid_manager.uuid4() if uuid == "" else uuid      

        while not bypass_uuid_check and self.uuid in variables.uuids:
            variables.global_logs.add(f"Cannot create the folder \"{name}\". The uuid already exists. It is a bug","error")  
            self.uuid= uuid_manager.uuid4() 
        variables.uuids.append(self.uuid)


        self.logger = logs.Logger(display=True,write_in_file=False,name="Folder ("+str(uuid)+")")
        self.var = variables
        self.parent_folder : Folder = parent
        if kwargs.get("isRoot"):
            self.parent_folder = self
        elif kwargs.get("bypassParent") == True:
            pass
        else:
            self.parent_folder = parent if isinstance(parent,Folder) else variables.root # only to go up
            self.parent_folder.addChild(self)
        
        self.main_layout   = QHBoxLayout()                     
        self.folder_name = QLineEdit(name)                
        self.supr_button = QPushButton("Del")          
        self.isShown = True
        self.config_height = int(self.var.theme.get("password_size").get("password_size"))

        self.children_list = children
        
        #FOLDER NAME
        self.folder_name.setStyleSheet(variables.theme.get("password_name").to_config())
        self.folder_name.textChanged.connect(self.onFolderNameChange)       
        
        #"SUPR BUTTON"        
        self.supr_button.setStyleSheet("QPushButton {"+self.var.theme.get("supr_button").to_config()+"} QPushButton:hover {"+self.var.theme.get("supr_button_hover").to_config()+"}")
        self.supr_button.setDefault(True)
        self.supr_button.clicked.connect(lambda : self.var.manager.deleteItem(self.uuid))
                

        # BUILDING LAYOUT
        
        ## HORIZONTAL
        self.main_layout.addWidget(self.folder_name)         
        self.main_layout.addWidget(self.supr_button) 

       
             
        
        self.setLayout(self.main_layout)        
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(self.var.theme.get("password_background").to_config())  
        self.setMaximumHeight(self.config_height)       
        
        

    
    def copy(self,parent,memo,bypassParent):  #parent is the copy of the parent  
        if memo.get(id(self)) != None:
            print("Anti-copy working")
            return memo[id(self)]
        
        l = []   
        f = Folder(self.var,parent=parent,name=self.getName(),children=l,uuid = self.uuid,bypass_uuid_check=True,bypassParent=bypassParent)

        if parent == None:
            parent = self.var.root

             
        for el in self.children_list:
            p=el.copy(parent=f)
            l.append(p) 

        memo[id(self)] = f

        return f


    def onFolderNameChange(self):
        self.var.resetMousePos()
        self.var.indicator.set("Not saved","blue")

    def onFolderFieldChange(self):          
        self.var.indicator.set("Not saved","blue")
        self.var.resetMousePos()        
        if self.getText()=="":
            self.folder_name.setStyleSheet(self.var.theme.get("password_warning").to_config())        
        else:
            self.folder_name.setStyleSheet(self.var.theme.get("password").to_config())

   
            
    
    def getName(self):
        return self.folder_name.text()        
    
    def isEmpty(self):
        return self.getText()==""
    
    def show(self):
        self.setHidden(False)

    def hide(self):
        self.setHidden(True)

    def find(self,word: str):
        if word == "": return True
        threshold = 80        
        name = process.extract(word.lower(), self.getName().lower().split(), scorer=fuzz.WRatio)        
        is_in_name = False        
        if len(name)> 0 : 
            is_in_name = name[0][1] > threshold          
        return is_in_name 
    
        
    def addChild(self,child):
        if child in self.children_list: 
            self.logger.add("Duplicating a child is not allowed", self.logger.warning)
            return
        self.children_list.append(child)

    def deleteChild(self,child,silent = True): #if not silent log will be dislayed
        if child in self.children_list : self.children_list.remove(child)
        elif not silent : self.logger.add("You are trying to remove a child which doesn't exist!", self.logger.warning)


    def getChildren(self, copy = True):        
        memo = {}
        if copy : 
            y=[]
            for el in self.children_list:
                y.append(el.copy(self,memo,True))              

        return self.children_list
    
    def setChildren(self, l, copy = True):
        if copy == True:
            l2 = []
            for el in l:
                l2.append(el.copy())

        self.children_list = l 
        
    def appear_normal(self):
        self.setStyleSheet(self.var.theme.get("password_background").to_config()) 

    def appear_selected(self):
        self.setStyleSheet(self.var.theme.get("password_background_selected").to_config()) 

    def mouseReleaseEvent(self, event):
        self.var.selection.add(self)        
        return super().mouseReleaseEvent(event)    

    def delete(self):
        if self in self.parent_folder.children_list : 
            self.parent_folder.children_list.remove(self)
        for el in self.children_list:
            el.delete()        
        self.var.selection.remove(self)

    

    def mouseDoubleClickEvent(self,event): #enter the folder
        self.var.current_node = self
        self.var.manager.createArea()           
        event.accept()