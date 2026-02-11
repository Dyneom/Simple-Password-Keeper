from __future__ import annotations 
from hashlib import pbkdf2_hmac # sha256
import sys


from PySide6.QtGui import QAction, QFont, QIcon, QShortcut, QKeySequence, QCursor

from PySide6.QtWidgets import (QApplication, QCheckBox, 
                            QGridLayout,  QHBoxLayout, 
                            QStyleFactory, QVBoxLayout, 
                            QWidget, QScrollArea, QToolBar,
                            QMainWindow, QLineEdit, QSpacerItem,
                            QPushButton, QMessageBox, QWidgetItem, QInputDialog                        
                            )

from PySide6.QtCore import QTimer, QTime

import uuid as uuid_manager
import argon2
import base64
import json
from cryptography.fernet import Fernet

#spk
import logs
import spk_file_manager
import spk_theme


class SimplePasswordKeeper(QMainWindow):

    def normalize_parse(self,string):
        return string.strip()

    def set_theme(self,default,custom):
        if custom != "": return custom
        else : return default

    def __init__(self,dir,theme,settings: spk_theme.ConfigDicts):
        super().__init__()

        self.logger=logs.Logger(display=settings.to_settings("logs"),name="manager_log")
        self.theme = theme        
        self.settings = settings      

        
        self.file_manager = spk_file_manager.FileManager(key = "",file_dir="test_file.spk",settings=self.settings) # No key at this point of the file, the key is set after in self.verify_password
        salt = self.file_manager.get_salt()
        hash = self.file_manager.get_hash()
        

        
            
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

    def load_passwords(self):
        self.file_manager.load_encrypted_content()
        worked = self.file_manager.decrypt_content()
        if worked:
            pw_list = []
            content = self.file_manager.get_content()
            if content != "":
                content_list = content.split("ᓡ")
                pw_list = [ tuple(i.split("◃")) for i in content_list]
              
            self.create_scroll_area(pw_list)
   
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
        msg.setStyleSheet(self.theme.get("dialog_wrong_character").to_config())
        msg.setStandardButtons(QMessageBox.Ok)
        self.logger.add("Non standard characters (U+9667) or (U+5345). Couldn't save",self.logger.error)
        msg.exec()
        
    def ask_password(self,message :str,hide = True):
        dialog=QInputDialog(self) 
             
        if hide : dialog.setTextEchoMode(QLineEdit.EchoMode.NoEcho)
        dialog.setLabelText(message)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setCancelButtonText("Exit")
        dialog.setStyleSheet(theme.get("dialog_password_main").to_config())
        
        dialog.children()[0].setStyleSheet(theme.get("dialog_password_message").to_config())
        dialog.children()[1].setStyleSheet(theme.get("dialog_password_password").to_config())
        dialog.children()[2].setStyleSheet(theme.get("dialog_password_buttons").to_config())
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
        self.editing=False
        self.current_field_edited=None
        self.current_field_button=None

        window_widget=QWidget()
        main_layout = QGridLayout()

        self.setCentralWidget(window_widget)          
        window_widget.setLayout(main_layout)
        
        

        #TODO : make the theming system nicer and safer

        n=4

        toolbar = QToolBar("toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        

        button_quit = QAction("Quit", self)        
        button_quit.triggered.connect(self.close)
        toolbar.addAction(button_quit) 

        button_save = QAction("Save", self)        
        button_save.triggered.connect(self.save)
        toolbar.addAction(button_save) 
      
        
        button_new_p = QAction("New password", self)        
        button_new_p.triggered.connect(self.create_new_password)
        toolbar.addAction(button_new_p) 
        self.main_layout = main_layout  


        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save)

        debug_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        debug_shortcut.activated.connect(self.getMousePos)

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda : self.save(isbackup=True))
        self.timer.start(6000)

        self.last_mouse_pos = ()
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(lambda : self.getMousePos())
        self.timer2.start(1000)

        self.load_passwords()         
       
    def save(self,isbackup = False): # TODO : a popup when saving password : keep the same or change
        c=self.scroll_layout.count()
        passwords= []
        passwords_names= []
        for i in range(c):
            a=self.scroll_layout.itemAt(i)

            if isinstance(a,QWidgetItem):
                w=a.widget()                
                if w.password_name.text() in passwords_names: # doubles
                    self.logger.add("Two or more passwords have the same name", self.logger.warning)

                name : str = w.password_name.text()
                pw=w.password.text()
                passwords_names.append(name)       # for keeping track of double names
                passwords.append(( name, pw,w.uuid )) # for saving  
                
                if name.find("◃") != -1 or name.find("ᓡ") != -1 or pw.find("◃") != -1 or pw.find("ᓡ") != -1: # to keep the save for being unreadable
                    self.wrong_character_popup()
                    return   
                
        csv_to_encrypt = ""            
        for name, password, uuid in passwords : #not optimized
            csv_to_encrypt+=name+"◃"+password+"◃"+str(uuid)+"ᓡ"
        self.file_manager.set_content(csv_to_encrypt[:-1]) # remove "ᓡ" at the end
        self.file_manager.encrypt_content(is_backup= isbackup)
        self.file_manager.save(is_backup= isbackup)
        del passwords_names  
        
                        
        
           #◃ 
           #ᓡ
                 
    def create_new_password(self):
        
        new_pass_lay=self.create_password_layout(name="New password",password="")
        #self.scroll_layout.passwords.append((self.scroll_layout.passwords_order,new_pass_lay.password_name,new_pass_lay.password))
        #self.scroll_layout.passwords_order+=1
        try:
            stretch = self.scroll_layout.takeAt(self.scroll_layout.count() -1 )                   
            if isinstance(stretch,QSpacerItem) :             
                del stretch   
        except AttributeError:
            self.logger.add("Failed to remove stretch (if the main layout wasn't empty this is a bug)",self.logger.warning)      
        
        self.scroll_layout.addWidget(new_pass_lay) # addWidget
        self.scroll_layout.addStretch()
        self.logger.add("Created new password",self.logger.success)
            
    def delete_password(self,l,passw_uuid):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Confirmation")
        msg.setText("Are you sure you want to delete this password?")
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
                    a.widget().deleteLater() # shadow boxes if this line is changed
                    self.scroll_layout.removeItem(a)                    
                                 
                    self.logger.add(f"Successfully deleted the password ({tmp_uuid})",self.logger.success) 
                    self.scroll_layout.addStretch()                   
                    break                    
            except Exception as e:
                self.logger.add(f"Exception when deleting the password (position {i}): {e}",self.logger.error)        
        else:
            self.logger.add("No password was deleted",self.logger.warning)
       
    def create_password_layout(self,  name = "Test", password="Password", uuid = ""):
        password_uuid= uuid_manager.uuid4() if uuid == "" else uuid
        password_background=QWidget()
        password_background.setStyleSheet(self.theme.get("password_background").to_config())       
       
        
        password = QLineEdit(password)
        show_button     = QCheckBox("Show") 
        edit_button     = QCheckBox("Edit") 
        main_password_layout   = QVBoxLayout()
        top_password_layout = QHBoxLayout()
        password_name = QLineEdit(name)  
        supr_button = QPushButton("Del")
        
        password_name.setStyleSheet(self.theme.get("password_name").to_config())

        show_button.setTristate(False)
        show_button.setCheckable(True)
        show_button.setChecked(False)
        show_button.isChecked_=False 
        show_button.toggled.connect(lambda : self.change_echo(password,show_button))  
        show_button.setStyleSheet(self.theme.get("show_button").to_config())

        edit_button.setStyleSheet(self.theme.get("edit_button").to_config())

        edit_button.toggled.connect(lambda : self.change_edit(password,edit_button))
        edit_button.toggled_=False

        
        supr_button.setStyleSheet("QPushButton {"+self.theme.get("supr_button").to_config()+"} QPushButton:hover {"+self.theme.get("supr_button_hover").to_config()+"}")
        supr_button.setDefault(True)
                

        password.setEnabled(False)
        password.setClearButtonEnabled(False)        
        password.setEchoMode(QLineEdit.EchoMode.NoEcho)

        password.setStyleSheet(self.theme.get("password").to_config())
        password.textChanged.connect(lambda : self.password_verifier(password))
        

        top_password_layout.addWidget(password_name)
        top_password_layout.addWidget(show_button) 
        top_password_layout.addWidget(edit_button) 
        top_password_layout.addWidget(supr_button) 

        main_password_layout.addLayout(top_password_layout)
        main_password_layout.addWidget(password)   

             
        
        password_background.setLayout(main_password_layout)
        password_background.password_name=password_name
        password_background.password=password
        password_background.uuid=password_uuid
        supr_button.clicked.connect(lambda: self.delete_password(password_background,password_uuid))
        
        return password_background
       
    def change_echo(self, password_field  : QHBoxLayout, butt):  
        if butt.isChecked_==False :    
            password_field.setEchoMode(QLineEdit.EchoMode.Normal)              
            self.logger.add("The password is now displayed",self.logger.information)  
            butt.isChecked_=True    
        else : 
            password_field.setEchoMode(QLineEdit.EchoMode.NoEcho)
            self.logger.add("The password is now hidden",self.logger.information) 
            butt.isChecked_=False
 
    def change_edit(self, password_field  : QHBoxLayout, butt : QCheckBox): 
        
        if not butt.toggled_ and (not self.editing or self.current_field_edited==None or self.current_field_edited==password_field) :
            password_field.setEnabled(True) 
            butt.setChecked(True)    

            if self.current_field_edited==password_field : self.current_field_edited.setEnabled(False)

            self.current_field_edited=password_field
            self.current_field_button=butt
            butt.toggled_ = True 
            self.editing = True              
          
            
        elif not butt.toggled_ and self.current_field_edited!=password_field:
            if self.current_field_edited == None:
                self.logger.add("Ce n'est pas normal",self.logger.warning)
            elif self.current_field_edited.text()!="":
                password_field.setEnabled(True) 
                butt.setChecked(True)                        
                self.current_field_edited.setEnabled(False)
                if self.current_field_button!=None:self.current_field_button.setChecked(False)
                self.current_field_edited=password_field
                self.current_field_button=butt
                butt.toggled_ = True 
                self.editing = True 
            else:                
                butt.setChecked(False)
                self.current_field_button.setChecked(True)
                
        
        elif butt.toggled_ and self.current_field_edited.text()=="":
            password_field.setEnabled(False) 
            butt.setChecked(True)                         
            self.current_field_edited.setEnabled(True)
            
            self.current_field_edited = self.current_field_edited # pas de changement
            self.current_field_button = self.current_field_button # idem
            butt.toggled_ = False 
            self.editing = True              
            self.logger.add("The field is empty, the field will stay focused",self.logger.information)     



        elif butt.toggled_ :
            password_field.setEnabled(False) 
            butt.setChecked(False)                         
            self.current_field_edited.setEnabled(False)   

            self.current_field_edited=None
            self.current_field_button=None
            butt.toggled_ = False 
            self.editing = False 
            self.logger.add("Untoggled",self.logger.success)
            
        else:
            self.logger.add("There's something else ?",self.logger.warning)            

    def password_verifier(self, password_field  : QHBoxLayout):  
        #self.file_manager.make_backup()  # to much backups !!!
        if password_field.text()=="":
            password_field.setStyleSheet(self.theme.get("password_warning").to_config())
        else:
            password_field.setStyleSheet(self.theme.get("password").to_config())

    def create_scroll_area(self,content):
       
        w=QWidget()
        l=QVBoxLayout(w)        
        for el in content: 
            try:
                name, password, uuid = el  
                p_l=self.create_password_layout(name=name,password=password,uuid=uuid)             
                l.addWidget(p_l)
            except Exception as e:
                self.logger.add(f"THIS IS A BUG : Problem occured when trying to recreate the password layout, a password could be missing (Exception : {e})",self.logger.critical_error)
             
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(w)                # Scroll <- widget <- layout <- password layout 
        l.addStretch() 
        self.main_layout.addWidget(scroll, 0 , 1)  
        self.scroll_layout = l   
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
        global_pos = QCursor.pos()  
        if self.last_mouse_pos != ():
            if global_pos == self.last_mouse_pos[0]:
                self.last_mouse_pos = (global_pos,self.last_mouse_pos[1] + 1)
                if self.last_mouse_pos[1] + 1 > self.settings.to_settings("timeout_delay") :
                    self.logger.add(f"App timed out (timer was set to {self.settings.to_settings("timeout_delay")}s)",self.logger.information)
                    self.close()            
            else:
                self.last_mouse_pos = (global_pos,1)
        else : 
            self.last_mouse_pos = (global_pos,1)

       

    

if __name__ == "__main__":
    global_logs = logs.Logger(display=True,write_in_file=False,name = "global")
    with open("spk_settings.json") as json_settings_file:        
        settings_c=json.load(json_settings_file)
        
    valid_args = ["backup_directory","dump_directory",
                "file_directory","file_name","config_file",
                "backups_silent","logs"]
    for u_ in valid_args:
        if not u_ in settings_c:
            global_logs.add(f"Missing argument in config, the valid args are {valid_args}",global_logs.warning)
    
    default_settings  = {
    "backup_directory" : ".spkbackups",
    "dump_directory"   : ".spkdumps",
    "backup_file" : "spk_backup_file.backup",
    "file_directory"   : "",
    "file_name"        : "spk_test_file",
    "config_file"    : "spk.conf",
    "backups_silent" : True,
    "logs" : True,
    "timeout_delay" : 60    
    }

    settings = spk_theme.ConfigDicts(settings_c,default=default_settings)
      
    theme = spk_theme.SpkTheme("spk.conf",settings=settings)    
    font = QFont(theme.get("font").get("font"))    
    font.setPixelSize(int(theme.get("font").get("size")))
    
    app = QApplication()  
    app.setFont(font)
    spk_app = SimplePasswordKeeper(dir="",theme=theme,settings=settings) 
    app.setStyle(QStyleFactory.create(theme.get("global").get("global")))
    spk_app.setStyleSheet(theme.get("background").to_config())     
    
    spk_app.show()
    sys.exit(app.exec())
   


#BUG: deleting a password while modifing it!!!
#BUG: empty setting file makes an error


# TODO LIST:
# - ~~change the theming system~~    
# - ~~make the user able to save with another password~~
# - import passwords
# - export passwords (copy the file :) ) 
# - ~~change the salts -> write in file~~
# - make the user able to change the saving directory -> json file
# - json settings file
# - ~~make BACKUPS~~
# - make a main file | make it able to run with argparse
# timeout 
# save the file when closing the app
# Ctrl + F ?
# Sort / Minecraft world sort ?



