import spk_variables
import spk_folder
import spk_password

from PySide6.QtWidgets import QMessageBox

class Selection():
    def __init__(self,variables : spk_variables.SpkVariables):
        self.selected = []
        self.var = variables
        self.var.selection = self
        
    def invertSelection(self):
        new_selection = []
        for el in self.var.current_node.getChildren():
            if el not in self.selected:
                new_selection.append(el)

        self.selected = new_selection
        return self.selected

    def getSelection(self,copy = True): #for now copy doesn't work
        if copy : return self.selected
        return self.selected    

    def setSelection(self,new_selection): #for now the copy doesn't work
        self.selected = new_selection

    def add(self,element,remove = True): # if remove is set to True, if the element is already in the list, it will be removed
        if element not in self.selected : 
            self.selected.append(element)
            if isinstance(element,(spk_password.Password,spk_folder.Folder)):
                element.appear_selected()

            return
        if remove: 
            self.selected.remove(element) 
            if isinstance(element,(spk_password.Password,spk_folder.Folder)):
                element.appear_normal()


    def remove(self,element): #silent
        #while element in self.selected: #while should do the same as an if
        #    self.selected.remove(element) 
        pass

    def delete_selection(self) :    #will delete the item with the deleteItem function (see manager)
        if len(self.selected)>0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Confirmation")
            msg.setText(f"Are you sure you want to delete these items ({len(self.selected)} in total)?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
            response = msg.exec()
            response = response==QMessageBox.Yes # /!\ Change of type
            if not response : return 
        l = []
        for el in self.selected:
            if isinstance(el,(spk_password.Password,spk_folder.Folder)):
                l.append(el.uuid)

        for uu in l:
            self.var.manager.deleteItem(uu,True,from_selection = True)    

        self.selected.clear()    
                


       

    def reset(self): 
        for el in self.selected:
            if isinstance(el,(spk_password.Password,spk_folder.Folder)):
                el.appear_normal()       
        self.selected.clear()

    def selectAll(self):        
        self.selected = self.var.current_node.getChildren()
        for el in self.selected:
            if isinstance(el,(spk_password.Password,spk_folder.Folder)):
                el.appear_selected()

    
    