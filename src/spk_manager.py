from __future__ import annotations 
from hashlib import pbkdf2_hmac # sha256



from PySide6.QtGui import QAction, QIcon, QShortcut, QKeySequence, QCursor

from PySide6.QtWidgets import ( 
                            QGridLayout, QVBoxLayout, QWidget, 
                            QScrollArea, QToolBar, QMainWindow, 
                            QLineEdit, QSpacerItem, QMessageBox, 
                            QWidgetItem, QInputDialog,  QSizePolicy                                     
                            )

from PySide6.QtCore import QTimer, Qt



import uuid as uuid_manager
import argon2
import base64
from cryptography.fernet import Fernet
#TODO : Faire en sorte qu'un fichier / dossier ne soit pas faisable avec un uuid déjà utilisé !!!!!!!!!! 
#spk
import logs
import spk_file_manager
import spk_indicator
import spk_password
import spk_variables
import spk_search_field
import spk_folder

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

            stack[-1].addChild(spk_password.Password(vars,name,pw,uuid,parent=stack[-1]))            
        elif chr == chr2: # folder
            s = s[i+1:] 


            name_end = get_next(s,chr)
            name = s[:name_end]
            s = s[name_end+1:] 
            

            uuid_end = get_next(s,chr)          
            uuid = s[:uuid_end]
            s = s[uuid_end+1:]
            f = spk_folder.Folder(variables=vars,name=name,children=[],uuid=uuid,parent=stack[-1])
            stack[-1].addChild(f)            
            stack.append(f)
            
        elif chr == chr3: #end of a folder
            s = s[i+1:]
            stack.pop()
    


            

        


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
                
                self.logger.add("New password set")            
                
                            
                pw_hmain= base64.urlsafe_b64encode(pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), salt, iter))
                pw = "NO" 
                self.file_manager.fernet = Fernet(pw_hmain)
                self.init_passwords()
                return 

        hash = str(hash,encoding="utf8")
        result,p_w = self.ask_password("Input your password")    
        
        while result == 1 and not self.verify_password(hash=hash,password_hasher=ph,salt = salt,iter=iter,pw=p_w):
            result,p_w = self.ask_password("Wrong Password")            

        if result == 0 : 
            exit()
        
        if  result == 1 :
            self.init_passwords()

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
    
    def init_passwords(self):

        #VARIABLES 
        self.editing=False
        self.current_shown_fields = []
        self.current_field_edited=None
        self.current_field_button=None
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
        

        button_quit = QAction("Quit", self)        
        button_quit.triggered.connect(self.close)
        toolbar.addAction(button_quit) 

        button_save = QAction("Save", self)        
        button_save.triggered.connect(self.save)
        toolbar.addAction(button_save) 
      
        
        button_new_p = QAction("New password field", self)        
        button_new_p.triggered.connect(self.newPassword)
        toolbar.addAction(button_new_p) 

        button_new_f = QAction("New Folder", self)        
        button_new_f.triggered.connect(self.newFolder)
        toolbar.addAction(button_new_f) 
         
        
         

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

        debug_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        debug_shortcut.activated.connect(self.go_parent)

        #TIMERS
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda : self.save(isbackup=True))
        self.timer.start(60000) # every minute 

        self.last_mouse_pos = ()
        self.timer2 = QTimer(self)
        self.var.resetMousePos()
        self.timer2.timeout.connect(self.getMousePos)
        self.timer2.start(1000)

        #END -> loadPassword
        self.main_layout = main_layout 
        self.main_layout.addWidget(spk_search_field.SearchField(self.var),0,1)
        self.loadPasswords()          
       
    def save(self,isbackup : bool = False): # TODO : a popup when saving password : keep the same or change
        chr1,chr2,chr3,chr4 = self.var.character        
        c=self.scroll_layout.count()
        passwords= []        
        csv_to_encrypt = "" 
        


        def create_folder_string(folder,string) -> str:
            name = folder.getName()
            uuid = folder.uuid
            string += chr2+name+chr2+str(uuid)+chr2            
            for el in folder.getChildren(copy=False):
                if isinstance(el,spk_folder.Folder) : 
                    string=create_folder_string(el,string)                    
                elif isinstance(el,spk_password.Password):
                    string+=el.to_save_string()
            string+=chr3
            return string
        

        for w in self.var.root.getChildren():  
                                                     

                if isinstance(w,spk_password.Password) :     
                    csv_to_encrypt += w.to_save_string()
                
                elif isinstance(w,spk_folder.Folder):
                    csv_to_encrypt+=create_folder_string(folder=w,string="")
                #     prof = 1  
                #     print("Found folder")                  
                #     layers = [(w,prof)] # stack
                #     while len(layers) != 0:
                #         print("Profondeur :",prof, "layers: ",layers)
                #         f,current_prof = layers.pop()
                #         name = f.getName()
                #         uuid = f.uuid
                #         csv_to_encrypt += chr2+name+chr2+str(uuid)+chr2
                #         children = f.getChildren()
                #         if current_prof>prof:
                #             print("Error on prof",current_prof,prof)
                #         elif current_prof == prof :
                #             print("OK prof")
                #         else:
                #             prof -= 1
                #             csv_to_encrypt+=chr3

                #         if len(children) == 0 : 
                #             csv_to_encrypt+=chr3
                #             prof -= 1 
                #         else:
                #             for i in children:
                #                 if isinstance(i,spk_password.Password) :     
                #                     csv_to_encrypt += i.to_save_string()
                #                 elif isinstance(i,spk_folder.Folder):  
                #                     prof += 1                              
                #                     layers.append((i,prof)) 
                                                                   

                    
                
                    
                  
        
        self.file_manager.set_content(csv_to_encrypt) 
        self.file_manager.encrypt_content(is_backup= isbackup)
        self.file_manager.save(is_backup= isbackup)        
        if not isbackup : self.indicator.set("Saved","green") 
        else : self.indicator.temp_message("Backed up",('green', 200),1)

#save file 
#password : chr1, name , chr1, uuid, chr1 , password
#folder : chr2, name , chr2, uuid , chr2 , children        
                        
        
           
    def newPassword(self):
        
        new_pass_lay=spk_password.Password(self.var,name = "New Password",password_text = "",parent=self.var.current_node)
        
        # try:
        #     stretch = self.scroll_layout.takeAt(self.scroll_layout.count() -1 )                   
        #     if isinstance(stretch,QSpacerItem) :             
        #         del stretch   
        # except AttributeError:
        #     self.logger.add("Failed to remove stretch (if the main layout wasn't empty this is a bug)",self.logger.warning)      
        
        # self.scroll_layout.addWidget(new_pass_lay) # addWidget
        # self.scroll_layout.addStretch()
        self.var.current_node.getChildren(copy=False).insert(0,new_pass_lay)
        self.scroll_layout.insertWidget(0,new_pass_lay)        
        self.logger.add("Created new password",self.logger.success)
        self.indicator.set("Not saved","blue")
        self.indicator.temp_message("Created password","gold",1)
    
    def newFolder(self):        
        new_folder_lay=spk_folder.Folder(self.var,children=[],name = "New Folder",parent=self.var.current_node)       
        self.var.current_node.getChildren(copy=False).insert(0,new_folder_lay)       
        self.scroll_layout.insertWidget(0,new_folder_lay)
        self.logger.add("Created new folder",self.logger.success)
        self.indicator.set("Not saved","blue")
        self.indicator.temp_message("Created folder","gold",1)

    def deleteItem(self,passw_uuid : uuid_manager.UUID):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Confirmation")
        msg.setText("Are you sure you want to delete this item?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
   
        response = msg.exec()
        response = response==QMessageBox.Yes # /!\ Change of type
        if not response : return 

        #DELETING PART      
        
        #el_list=[self.scroll_layout.itemAt(i).widget().password_name.text() for i in range(self.scroll_layout.count()-1)]
        if isinstance(self.scroll_layout.itemAt(self.scroll_layout.count() -1),QSpacerItem):            
            self.scroll_layout.removeItem(self.scroll_layout.itemAt(self.scroll_layout.count() -1))

        for i in range(self.scroll_layout.count()):
            try:
                tmp_uuid=self.scroll_layout.itemAt(i).widget().uuid
                if tmp_uuid==passw_uuid :
                    self.logger.add(f"Deleting password in position {i} (uuid: {tmp_uuid})") 
                    a=self.scroll_layout.itemAt(i)
                    if isinstance(a.widget(),spk_password.Password) :                         
                        bl = a.widget().untoggleEditing()
                        a.widget().parent_folder.getChildren().remove(a.widget())
                        if bl : #if the password was edited
                            self.var.current_field_edited = None
                        if a.widget() in self.var.current_shown_fields :
                            self.var.current_shown_fields.remove(a)
                    elif isinstance(a.widget(),spk_folder.Folder):
                        a.widget().parent_folder.getChildren().remove(a.widget())
                        pass
                    if a.widget() in self.var.password_list:
                        self.var.password_list.remove(a.widget())
                        
                       

                       
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
        widget=QWidget()
        item_layout=QVBoxLayout(widget) 
        for el in self.var.current_node.getChildren():
            item_layout.addWidget(el)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)                # Scroll <- widget <- <- item layout
        item_layout.addStretch() 
        self.main_layout.addWidget(scroll, 1 , 1)  
        self.scroll_layout = item_layout 
        self.scroll2 = scroll  
        scroll.setStyleSheet(f"""QScrollBar:vertical {chr(123)} 
                                {self.var.theme.get("scroll_bar_background").to_config()}
                            {chr(125)}
                             QScrollBar::handle:vertical {chr(123)}
                                {self.var.theme.get("scroll_bar").to_config()}
                            {chr(125)}
                            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {chr(123)}
                               {self.var.theme.get("scroll_bar_buttons").to_config()}
                            {chr(125)}""")
        
        
        self.logger.add("Created scroll area",self.logger.success)  
        return scroll
        
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
        for pw in self.var.password_list:
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


        
      
