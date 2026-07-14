from __future__ import annotations 
from hashlib import pbkdf2_hmac # sha256



from PySide6.QtGui import QAction, QIcon, QShortcut, QKeySequence, QCursor, QPainter, QPen, QColor

from PySide6.QtWidgets import ( 
                            QGridLayout, QVBoxLayout, QWidget, 
                            QScrollArea, QToolBar, QMainWindow, 
                            QLineEdit, QSpacerItem, QMessageBox, 
                            QWidgetItem, QInputDialog,  QSizePolicy  , QToolButton, QMenu                                
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
import logs
import spk_file_manager
import spk_indicator
import spk_password
import spk_variables
import spk_search_field
import spk_folder
import spk_selection
import spk_path

def contains(string:str, l: list[str]) -> bool:
    for i in l:
        if string.find(i)!=-1: return True
    return False

class WrongFileSyntax(Exception): pass

def get_next(s : str, chars): 
    if chars == []:
        raise ValueError("The character array is empty")
    if len(chars) == 1:
        v = s.find(chars[0])
        if v == -1:
            raise WrongFileSyntax(f"The end of the file was reached without finding {chars[0]}")
        return v
    if isinstance(chars,str):
        v = s.find(chars)
        if v == -1:
            raise WrongFileSyntax(f"The end of the file was reached without finding {chars}")
        return v
    


    u = []
    for c in chars:
        u.append((s.find(c),c))
    max_v = -2 # will be replaced even if the first value wasn't found 
    min_val = (-1,u[0][1]) #val, char
    for i in range(0,len(u)):
        if u[i][0] > max_v:
            max_v = u[i][0]
        if min_val[0] == -1 or (u[i][0] < min_val[0] and u[i][0] != -1):
            min_val = u[i]

        
    if max_v == -1:    
        raise WrongFileSyntax(f"The end of the file was reached without finding any of {chars}")
    elif max_v == -2:
        raise Exception("This shouldn't happen. The str.find should return at least -1 not -2 or less")
    if min_val[0] == -1:
        raise WrongFileSyntax(f"The end of the file was reached without finding any of {chars}. You shouldn't see this error if the code worked")

    return min_val

def save_to_layout(s:str,vars: spk_variables.SpkVariables): # input is the decrypted save, output is the root with all the passwords and folders in it
    chr1,chr2,chr3,chr4 = vars.character
    
    root = vars.root
    stack = [root]
    while stack != [] and s != "":
        i,chr = get_next(s,[chr1,chr2,chr3]) # must handle the error 
        if chr == chr1: #password

            s = s[i+1:] 

            name_end = get_next(s,chr)
            name = s[:name_end]
            s = s[name_end+1:] 

            uuid_end = get_next(s,chr)          
            uuid = s[:uuid_end]
            s = s[uuid_end+1:]

            if s != "":
                pw_end,_ = get_next(s,[chr1,chr2,chr3])          
                pw = s[:max(0,pw_end-1)]
                s = s[pw_end:]
            else:
                pw = ""

            spk_password.Password(vars,parent=stack[-1],name=name,password_text=pw,uuid=uuid)           
        elif chr == chr2: # folder
            s = s[i+1:] 


            name_end = get_next(s,chr)
            name = s[:name_end]
            s = s[name_end+1:] 
            

            uuid_end = get_next(s,chr)          
            uuid = s[:uuid_end]
            s = s[uuid_end+1:]
            f = spk_folder.Folder(variables=vars,parent=stack[-1],name=name,children=[],uuid=uuid)
                      
            stack.append(f)
            
        elif chr == chr3: #end of a folder
            s = s[i+1:]
            stack.pop()
    


class DragAndScroll(QWidget):
    #to test with 0 and 1 item
    LINE_THICKNESS = 3
    LINE_COLOR = QColor("#7e5e5e")
    def __init__(self,lay,var):
        super().__init__()
        self.lay : QVBoxLayout = self.layout()     
        self.var = var
        self.y_list : list | None = None
        self.y_middle_list : list | None = None
        self.setAcceptDrops(True)
        self.target_y = None
        self.target_y_item = None
        
        self.current_folder_drop = None

    def dragEnterEvent(self, e):
        self.var.dragActive = True
        e.accept()
        self.createYlist()
        

        
        

    def dropEvent(self, e):        
        pos = e.pos()
        widget = e.source()

     

        #handle the drop
        self.layout().update()
        if self.target_y and self.target_y_item != widget and self.var.current_node != widget: #the last expr is to prevent a bug with double-clicking and dragging a the same time (second click) 
            
            #remove the initial item from the list, insert it at the right place
            #finding the index of self.target_y_item in layout
            after_widget = False
            for n in range(self.lay.count()):
                w = self.lay.itemAt(n).widget()
                if w == self.target_y_item:
                    if after_widget:
                        index = n - 1
                    else: # after_widget==False:
                        index = n 
                    break
                elif w == widget:
                    after_widget = True
            else:
                index = self.lay.count() - 2

            self.lay.removeWidget(widget)
            self.layout().update()
            self.lay.insertWidget(index,widget)
            self.layout().update()

            after_widget = False
            for i,item in enumerate(self.var.current_node.getChildren(copy=False)):                
                if item == self.target_y_item:
                    if after_widget:
                        index = i - 1
                    else: # after_widget==False:
                        index = i 
                    break
                elif item == widget:
                    after_widget = True
            else:
                index = -1

            
            self.var.current_node.moveChild(index,widget)  
            
        
        elif self.current_folder_drop and self.current_folder_drop != widget and self.current_folder_drop != self.var.current_node:
            self.lay.removeWidget(widget)                        
            widget.setParent(self.current_folder_drop)   
            
            if isinstance(widget,spk_folder.Folder):
                widget.parent_folder = self.current_folder_drop         
            self.var.current_node.deleteChild(widget,silent= False)            
            self.current_folder_drop.addChild(widget)
            self.lay.update()
            

            
            

        #clear 
        self.clearDrawings()
        
        self.var.dragActive = False  
        self.y_list = None
        e.accept()

    def clearDrawings(self):
        self.target_y = None
        self.target_y_item = None
        self.update()
        if self.current_folder_drop:
            self.current_folder_drop.appear_normal()

    def dragLeaveEvent(self, event):          
        self.var.dragActive = False  
        self.y_list = None
        event.accept()

    def dragMoveEvent(self,event):        
        self.findDropPos(event.position().toPoint().y())
        event.accept()

    def findDropPos(self,y_pos):
        if self.y_list == []: return
        #finding min in y distance in self.y_list
        pos,mitem = self.y_list[0] # m is not the real min distance at the moment
        m = abs(pos - y_pos)
        for i in range(1,len(self.y_list)):
            y,it = self.y_list[i]
            if abs(y-y_pos) < m:
                m = abs(y-y_pos)
                pos = y
                mitem = it

        #finding min in y distance in self.y_middle_list
        pos_middle,mitem_middle = self.y_list[0] # m_middle is not the real min distance at the moment
        m_middle = abs(pos_middle - y_pos)
        for i in range(1,len(self.y_middle_list)):
            y,it = self.y_middle_list[i]
            if abs(y-y_pos) < m_middle:
                m_middle = abs(y-y_pos)             
                mitem_middle = it

        if isinstance(mitem_middle,spk_folder.Folder) and m_middle<=3/8*mitem_middle.size().height():
            self.target_y = None
            self.target_y_item = None
            self.update()
            if self.current_folder_drop!=mitem_middle: 
                if self.current_folder_drop: self.current_folder_drop.appear_normal()
                self.current_folder_drop = mitem_middle
                mitem_middle.appear_selected_drop()            
            return
        if self.current_folder_drop:            
            self.current_folder_drop.appear_normal_drop()
            self.current_folder_drop = None
        self.target_y = pos - 3
        self.target_y_item = mitem
        self.update()
        return


        
        

    def paintEvent(self, event):        
        
        super().paintEvent(event)  
        if self.target_y != None:      
            painter = QPainter(self)
            pen = QPen(self.LINE_COLOR)
            pen.setWidth(self.LINE_THICKNESS)
            painter.setPen(pen)
            margin = self.lay.contentsMargins()
            x1 = margin.left()
            x2 = self.width() - margin.right()
            painter.drawLine(QPoint(x1, self.target_y), QPoint(x2, self.target_y))
            painter.end()                


    

    def createYlist(self):
        self.y_list = [(a.y(),a) for a in self.var.current_node.getChildren(copy=False)]
        if self.y_list != []:
            _1,_2 = self.y_list[0]
            # finding max height
            for i in range(1,len(self.y_list)):
                if _1 < self.y_list[i][0]:
                    _1,_2 = self.y_list[i]

            self.y_list.append((_1+_2.size().height()+6,_2.size().height()))
        self.y_middle_list = [(a.y()+a.size().height()//2,a) for a in self.var.current_node.getChildren(copy=False)]






class SimplePasswordKeeper(QMainWindow):


    def __init__(self,dir,var : spk_variables.SpkVariables):
        super().__init__()

        self.logger=logs.Logger(display=var.settings.to_settings("logs"),name="manager_log")
        self.theme = var.theme        
        self.settings = var.settings      

        
        self.file_manager = spk_file_manager.FileManager(key = "",file_dir="test_file.spk",settings=self.settings) # No key at this point of the file, the key is set after in self.verify_password
        salt = self.file_manager.get_salt()
        hash = self.file_manager.get_hash()
        
        self.var = var
        
            
        iter = 5_000_000
        ph = argon2.PasswordHasher(time_cost=10,memory_cost=1000,hash_len=32)  
        should_exit = False
        if hash == None :
            while should_exit == False: #false endless loop
                result,pw = self.ask_password("Choose a password", hide = False)  
                if result == 0 : exit()
                if len(pw) < 5: continue
                pw_h=pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), salt, iter)          
                self.file_manager.set_hash(ph.hash(password=pw_h,salt=salt))
                
                            
                
                            
                pw_hmain= base64.urlsafe_b64encode(pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), salt, iter))
                pw = "NO" 
                self.file_manager.fernet = Fernet(pw_hmain)
                self.initApp()
                return 

        hash = str(hash,encoding="utf8")
        result,p_w = self.ask_password("Input your password")    
        
        while result == 1 and not self.verify_password(hash=hash,password_hasher=ph,salt = salt,iter=iter,pw=p_w):
            result,p_w = self.ask_password("Wrong Password")            

        if result == 0 : 
            exit()
        
        if  result == 1 :
            self.initApp()

        self.logger.add(f"Init finished | Launching app (result : {result})",self.logger.success)
 
    def loadPasswords(self):
        chr1,chr2,chr3,chr4 = self.var.character
        self.file_manager.load_encrypted_content()
        worked = self.file_manager.decrypt_content()
        if worked:
            pw_list = []
            content = self.file_manager.get_content()
            if content != "":                
                try:
                    save_to_layout(content,self.var)    #automaticaly set it to root               
                except NotADirectoryError as e:
                    self.logger.add(f"THIS IS A BUG : Problem occured when trying to recreate the password layout, a password could be missing (Exception : {e})",self.logger.critical_error) #you can add "when extracting : {content}" to know what makes the error (it isn't done due to security reasons)
                                  
            self.createArea()
   
    def verify_password(self,hash,password_hasher,salt,iter,pw) -> bool:
        try:
            pw_h=pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), salt, iter)            
            password_hasher.verify(hash,pw_h) 
            #If no exception was raised
            pw_hmain= base64.urlsafe_b64encode(pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), salt, iter))
            pw = "NO" 
            self.file_manager.fernet = Fernet(pw_hmain)
            return True
        except argon2.exceptions.VerifyMismatchError :
            return False    

    def wrong_character_popup(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)        
        msg.setWindowTitle("U r dumb")
        msg.setText("You are using non-standard characters in your password (U+9667) or (U+5345). Please delete those")
        msg.setStyleSheet(self.var.theme.get("dialog_wrong_character").to_config())
        msg.setStandardButtons(QMessageBox.Ok)
        self.logger.add("Non standard characters (U+9667) or (U+5345). Couldn't save",self.logger.error)
        msg.exec()
        
    def ask_password(self,message :str,hide = True):
        dialog=QInputDialog(self) 
             
        if hide : dialog.setTextEchoMode(QLineEdit.EchoMode.NoEcho)
        dialog.setLabelText(message)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setCancelButtonText("Exit")
        dialog.setStyleSheet(self.theme.get("dialog_password_main").to_config())
        
        dialog.children()[0].setStyleSheet(self.theme.get("dialog_password_message").to_config())
        dialog.children()[1].setStyleSheet(self.theme.get("dialog_password_password").to_config())
        dialog.children()[2].setStyleSheet(self.theme.get("dialog_password_buttons").to_config())
        dialog.children()[2].children()[1].setIcon(QIcon()) # YES
        dialog.children()[2].children()[2].setIcon(QIcon()) # NO
      
           
        result  = dialog.exec()
        
        if isinstance(dialog.children()[0],QLineEdit):            
            pw = dialog.children()[0].text()
        elif isinstance(dialog.children()[1],QLineEdit):     #the order changes if the hide is at true or not        
            pw = dialog.children()[1].text()
        else: 
            self.logger.add("Failed to read password",self.logger.shutdown_error)
            exit(1)     
        
        return result,pw
    
    def initApp(self):

        #SELECTION

        spk_selection.Selection(self.var)

        #VARIABLES 
        self.editing=False
        self.current_shown_fields = []
        
        
        self.minimum_password_field_height = 30

        #WINDOW 
        window_widget=QWidget()
        main_layout = QGridLayout()

        self.setCentralWidget(window_widget)          
        window_widget.setLayout(main_layout)      

        
        #TOOLBAR
        toolbar = QToolBar("toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        

        menu = QMenu(self)
        menu.addAction("Settings", lambda: print("Settings"))
        menu.addAction("Help", lambda: print("Help"))        
        menu.addAction("Change password", self.changePassword)     
        menu.addAction("Quit", self.close)

        
        btn = QToolButton(self)
        btn.setText("⋮")          
        btn.setMenu(menu)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setIcon(qtawesome.icon("fa6s.ellipsis-vertical",color="white"))   

        toolbar.addWidget(btn)
        

        button_save = QAction("Save", self)   
        button_save.setIcon(qtawesome.icon("fa6s.floppy-disk",color="white"))  
        button_save.triggered.connect(self.save)
        toolbar.addAction(button_save) 
      
        
        button_new_p = QAction("New password field", self)    
        button_new_p.setIcon(qtawesome.icon("fa6s.plus",color="white"))     
        button_new_p.triggered.connect(self.newPassword)
        toolbar.addAction(button_new_p) 

        button_new_f = QAction("New Folder", self)  
        button_new_f.setIcon(qtawesome.icon("fa6s.folder-plus",color="white"))  
        button_new_f.triggered.connect(self.newFolder)
        toolbar.addAction(button_new_f) 

        go_parent_button = QAction("Go to parent folder", self)  
        go_parent_button.setIcon(qtawesome.icon("fa6s.arrow-up",color="white"))  
        go_parent_button.triggered.connect(self.go_parent)
        toolbar.addAction(go_parent_button)

        
         
        
         

        spacer =  QWidget()       
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        self.indicator =  spk_indicator.Spk_Indicator("Saved",color = "green")
        self.var.indicator = self.indicator
        toolbar.addWidget(self.indicator)


        #SHORTCUTS

        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save)

        new_password_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_password_shortcut.activated.connect(self.newPassword)

        new_folder_shortcut = QShortcut(QKeySequence("Ctrl+SHIFT+N"), self)
        new_folder_shortcut.activated.connect(self.newFolder)

        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

        select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        select_all_shortcut.activated.connect(self.var.selection.selectAll)   

        delete_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        delete_shortcut.activated.connect(self.var.selection.delete_selection)

        

        #TIMERS
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda : self.save(isbackup=True))
        self.timer.start(60000) # every minute 

        self.last_mouse_pos = ()
        self.timer2 = QTimer(self)
        self.var.resetMousePos()
        self.timer2.timeout.connect(self.getMousePos)
        self.timer2.start(1000)

        #SOCKET
        self.init_socket()

        #END -> loadPassword
        self.main_layout = main_layout 
        self.spk_path = spk_path.SpkPath(self.var)
        self.main_layout.addWidget(spk_search_field.SearchField(self.var),1,1)
        self.main_layout.addWidget(self.spk_path,0,1)
        
        self.loadPasswords()          
       
    def save(self,isbackup : bool = False): # TODO : a popup when saving password : keep the same or change
        t = func_timer.time()
        chr1,chr2,chr3,chr4 = self.var.character        
        c=self.scroll_layout.count()
        passwords= []        
        csv_to_encrypt = "" 
        


        def create_folder_string(folder,string) -> str:
            try:
                name = folder.getName()
                uuid = folder.uuid
                string += chr2+name+chr2+str(uuid)+chr2            
                for el in folder.getChildren(copy=False):
                    if isinstance(el,spk_folder.Folder) : 
                        string=create_folder_string(el,string)                    
                    elif isinstance(el,spk_password.Password):
                        string+=el.to_save_string()
                string+=chr3
            except Exception as e:
                self.logger.add("Failed to save a folder",self.logger.error)
            return string
        
        
        for w in self.var.root.getChildren(copy=False):                                                  

                if isinstance(w,spk_password.Password):     
                    csv_to_encrypt += w.to_save_string()
                
                elif isinstance(w,spk_folder.Folder):                    
                    csv_to_encrypt+=create_folder_string(folder=w,string="")
                    
                                                                      
        self.file_manager.set_content(csv_to_encrypt) 
        self.file_manager.encrypt_content(is_backup= isbackup)
        self.file_manager.save(is_backup= isbackup)        
        if not isbackup : self.indicator.set("Saved","green") 
        else : self.indicator.temp_message("Backed up",('green', 200),1)
        self.logger.add(f"Saved in {func_timer.time()-t}s")

#save file 
#password : chr1, name , chr1, uuid, chr1 , password
#folder : chr2, name , chr2, uuid , chr2 , children        
                        
        
           
    def newPassword(self):
        
        new_pass_lay=spk_password.Password(self.var,name = "New Password",password_text = "",parent=self.var.current_node)          
        self.scroll_layout.insertWidget(0,new_pass_lay)        
        self.logger.add("Created new password",self.logger.success)
        self.indicator.set("Not saved","blue")
        self.indicator.temp_message("Created password","gold",1)
    
    def newFolder(self):        
        new_folder_lay=spk_folder.Folder(self.var,parent=self.var.current_node,children=[],name = "New Folder")              
        self.scroll_layout.insertWidget(0,new_folder_lay)
        self.logger.add("Created new folder",self.logger.success)
        self.indicator.set("Not saved","blue")
        self.indicator.temp_message("Created folder","gold",1)

    def deleteItem(self,passw_uuid : uuid_manager.UUID,no_pop_up=False,from_selection = False):
        #POP-UP
        if not no_pop_up:    
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Confirmation")
            msg.setText("Are you sure you want to delete this item?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
            response = msg.exec() 
            response = response==QMessageBox.Yes # /!\ Change of type
            if not response : return 

        #DELETING PART         
        
        if isinstance(self.scroll_layout.itemAt(self.scroll_layout.count() -1),QSpacerItem):            
            self.scroll_layout.removeItem(self.scroll_layout.itemAt(self.scroll_layout.count() -1))

        for i in range(self.scroll_layout.count()):
            try:
                tmp_uuid=self.scroll_layout.itemAt(i).widget().uuid
                if tmp_uuid==passw_uuid :
                    self.logger.add(f"Deleting password in position {i} (uuid: {tmp_uuid})") 
                    a=self.scroll_layout.itemAt(i)
                    if isinstance(a.widget(),spk_password.Password) :                         
                        a.widget().delete()
                    elif isinstance(a.widget(),spk_folder.Folder):
                        a.widget().delete()
                        pass
                    
                    a.widget().deleteLater() # shadow boxes if this line is changed
                    self.scroll_layout.removeItem(a) 
                    
                                 
                    self.logger.add(f"Successfully deleted the item ({tmp_uuid})",self.logger.success) 
                    self.scroll_layout.addStretch()                   
                    break                    
            except Exception as e:
                self.logger.add(f"Exception when deleting the password (position {i}): {e}",self.logger.error)        
        else:
            self.logger.add("No password were deleted",self.logger.warning)
        self.indicator.set("Not saved","blue")
        self.indicator.temp_message("Deleted password","orange",1)

    def createArea(self): 
        
        widget=DragAndScroll(None,self.var)
        item_layout=QVBoxLayout(widget) 
        widget.lay = item_layout
        for el in self.var.current_node.getChildren(copy=False):
            item_layout.addWidget(el)

        scroll = QScrollArea()
        
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)                # Scroll <- widget <- <- item layout
        item_layout.addStretch() 
        self.main_layout.addWidget(scroll, 2 , 1)  
        self.scroll_layout = item_layout   


        scroll.setStyleSheet(f"""QScrollBar:vertical {chr(123)} 
                                {self.var.theme.get("scroll_bar_background").to_config()}
                            {chr(125)}
                             QScrollBar::handle:vertical {chr(123)}
                                {self.var.theme.get("scroll_bar").to_config()}
                            {chr(125)}
                            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {chr(123)}
                               {self.var.theme.get("scroll_bar_buttons").to_config()}
                            {chr(125)}""")
        
        
        self.logger.add("Created scroll area"+" "+self.var.current_node.getPath(),self.logger.success)  
        self.var.selection.reset() 
        self.spk_path.refresh()
        return scroll

    #utils   
    def close(self):
        self.save()
        exit()

    def closeEvent(self, event):
        self.save()
        self.logger.add("Closing app, saving...")
        event.accept()

    def getMousePos(self):
        global_pos =  QCursor.pos()  
        if self.var.last_mouse_pos != ():
            if global_pos == self.var.last_mouse_pos[0]:
                self.var.last_mouse_pos = (global_pos,self.var.last_mouse_pos[1] + 1)
                if self.var.last_mouse_pos[1] + 1 > self.settings.to_settings("timeout_delay") : # delay check
                    self.logger.add(f"App timed out (timer was set to {self.settings.to_settings("timeout_delay")}s)",self.logger.information)
                    self.close()
                return              
        self.var.resetMousePos()
        return
      
    def resizeEvent(self, event): #resize the current field  
        for pw in self.var.current_shown_fields:  
            pw.resize()

    def search(self, word :str):
        for pw in self.var.current_node.getChildren(copy=False):
            found: bool = pw.find(word)
            if found :                 
                pw.show()
            else:                
                pw.hide()

    def go_parent(self):  
        if self.var.current_node != self.var.root:      
            self.var.current_node = self.var.current_node.parent_folder
            
            self.createArea()
        #self.current_node = 

    def init_socket(self,SOCKET_PATH = "/home/matheo/projectsL/simple_password_keeper/src/spk.sock"):        
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)        
    
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.setblocking(False)
        server.bind(SOCKET_PATH)
        server.listen()

        def on_new_connection():
            print("Received message")                       
            conn, _ = server.accept()
            data = conn.recv(4096)
            if data:
                print("Data is ", data.decode())
                if data.decode() == "Exec":
                    self.writePassword()
            conn.close()
        

        # QSocketNotifier surveille le file descriptor
        notifier = QSocketNotifier(server.fileno(), QSocketNotifier.Type.Read,self)
        notifier.activated.connect(on_new_connection)
        
    def writePassword(self):
        print("Trying to write")
        if self.var.passwordToCopy:  
            if len(self.var.passwordToCopy.getText())<1000:
                subprocess.run(["zsh","-c","hyprctl keyword '$LAPTOP_KB_ENABLED' \"false\" -r"])       
                writer = subprocess.run(["zsh", "-c", f"sleep 0.2 && ydotool type --key-delay 0 {self.var.passwordToCopy.getText()}"])
                subprocess.run(["zsh","-c","hyprctl keyword '$LAPTOP_KB_ENABLED' \"true\" -r"])       

            else:
                writer = subprocess.run(["zsh", "-c", f"sleep 0.1 && ydotool type --key-delay 2 {self.var.passwordToCopy.getText()}"])

            if writer.returncode != 0 :
                self.logger.add("Couldn't write the password check if the ydotool deamon is active",self.logger.error)
            else:
                print("Success")
        else:
            print(self.var.passwordToCopy)


    def changePassword(self,message = "Hello, to what do you want to change your password?" ):
        hash_func = pbkdf2_hmac
        result = 1
        pw = ""      
        salt = os.urandom(256)
        iter = 5_000_000
        l = 5   # min password length
        while result == 1 and len(pw) < l:
            result, pw = self.ask_password(message,hide = False) 
            message = f"The lenght of the password must be at least equal to {l}"
        if result == 0: return False # not set
        ph = argon2.PasswordHasher(time_cost=10,memory_cost=1000,hash_len=32) 
        sha_256 = hash_func('sha256', bytes(pw,encoding='utf8'), salt, iter)         
        self.file_manager.setFernet(base64.urlsafe_b64encode(sha_256))
        self.file_manager.set_hash(ph.hash(password=sha_256,salt=salt))  
        self.file_manager.salt = salt      
        self.logger.add("New password set")
        return True