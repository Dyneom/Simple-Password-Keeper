import uuid as uuid_manager

from PySide6.QtGui import QColor, QDrag, QPixmap

from PySide6.QtWidgets import (
                            QCheckBox, QHBoxLayout, QVBoxLayout, 
                            QWidget, QLineEdit, QPushButton,   
                            QTextEdit  
                            )

from PySide6.QtCore import Qt, QMimeData, QTimer
from rapidfuzz import process, fuzz



#spk
import logs
import spk_variables
import spk_password



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
        self.selected_check = QCheckBox() 
        if  not kwargs.get("isRoot"):                 
            self.folder_name = spk_password.PasswordName(name,lambda : ...)
        else:
            self.folder_name = QLineEdit(name)                
                 
        self.isShown = True
        self.config_height = int(self.var.theme.get("password_size").get("password_size"))

        self.children_list = children
        
        #FOLDER NAME
        self.folder_name.setStyleSheet(variables.theme.get("password_name").to_config())
        self.folder_name.textChanged.connect(self.onFolderNameChange)       
        
             
        #SELCTION CHECKMARK
        self.selected_check.setCheckable(True)
        self.selected_check.setChecked(False)
        self.selected_check.setStyleSheet(self.var.theme.get("show_button").to_config())
        self.selected_check.clicked.connect(lambda : self.var.selection.add(self))
        
     
             

        # BUILDING LAYOUT
        
        ## HORIZONTAL
        self.main_layout.addWidget(self.selected_check)
        self.main_layout.addWidget(self.folder_name)         
         

       
             
        
        self.setLayout(self.main_layout)        
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(self.var.theme.get("password_background").to_config())  
        self.setMaximumHeight(self.config_height)       
        
    def mouseMoveEvent(self, e):
       if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

    
    def copy(self,parent,memo,bypassParent):  #parent is the copy of the parent  
        if memo.get(id(self)) != None:
            print("Anti-copy working")
            return memo[id(self)]
        
        l = []   
        f = Folder(self.var,parent=parent,name=self.getName(),children=l,uuid = self.uuid,bypass_uuid_check=True,bypassParent=bypassParent)

        if parent == None:
            parent = self.var.root

             
        for el in self.children_list:
            p=el.copy(parent=f,memo=memo,bypassParent=False)
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
        if self == child:
            self.logger.add("A child cannot be its own parent", self.logger.error)
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
        
    def appear_selected(self):
        self.setStyleSheet(self.var.theme.get("password_background_selected").to_config())              
        self.selected_check.setChecked(True)        
    
    def appear_selected_drop(self):
        self.setStyleSheet(self.var.theme.get("folder_background_drop").to_config())              
              

    def appear_normal(self):
        self.setStyleSheet(self.var.theme.get("password_background").to_config()) 
        self.selected_check.setChecked(False) 

    def appear_normal_drop(self):
        if self.selected_check.isChecked():
            self.appear_selected()
        else:
            self.appear_normal()
        
             

    

    def mouseReleaseEvent(self, event):
        #self.var.selection.add(self)        
        return super().mouseReleaseEvent(event)    

    def delete(self):
        if self in self.parent_folder.children_list : 
            self.parent_folder.children_list.remove(self)
        for el in self.children_list:
            el.delete()        
        self.var.selection.remove(self)

    

    def mouseDoubleClickEvent(self,event): #enter the folder        
        QTimer.singleShot(100, self.handleDoubleClick) # to prevent a bug when also dragging
        

    def handleDoubleClick(self):
        if not self.var.dragActive:
            self.var.current_node = self
            self.var.manager.createArea()  
                
            


    def __bool__(self):
        return True
    

    def getPath(self):
        f = self
        path = f.getName()
        while f != self.var.root:
            f = f.parent_folder
            path = f.getName() + "/" + path
        return path
    

    def moveChild(self,index,child):
        if  child not in self.children_list:
            self.logger.add("Unable to move a child that doesn't exist")
            return
        self.children_list.remove(child)
        self.children_list.insert(index,child)

    
    