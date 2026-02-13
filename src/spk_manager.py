from __future__ import annotations 
from hashlib import pbkdf2_hmac # sha256



from PySide6.QtGui import QAction, QFont, QIcon, QShortcut, QKeySequence, QCursor, QColor

from PySide6.QtWidgets import (QApplication, QCheckBox, 
                            QGridLayout,  QHBoxLayout, 
                            QStyleFactory, QVBoxLayout, 
                            QWidget, QScrollArea, QToolBar,
                            QMainWindow, QLineEdit, QSpacerItem,
                            QPushButton, QMessageBox, QWidgetItem, QInputDialog, QLabel, QSizePolicy,
                            QTextEdit         
                            )

from PySide6.QtCore import QTimer

import uuid as uuid_manager
import argon2
import base64
import json
from cryptography.fernet import Fernet

#spk
import logs
import spk_file_manager
import spk_theme
import spk_indicator
import spk_password
import spk_variables


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
        self.file_manager.load_encrypted_content()
        worked = self.file_manager.decrypt_content()
        if worked:
            pw_list = []
            content = self.file_manager.get_content()
            if content != "":
                content_list = content.split("ᓡ")
                pw_list = [ tuple(i.split("◃")) for i in content_list]
              
            self.createScrollArea(pw_list)
   
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
        self.main_layout = main_layout  

        spacer =  QWidget()       
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        self.indicator =  spk_indicator.Spk_Indicator("Saved",color = "green")
        self.var.indicator = self.indicator
        toolbar.addWidget(self.indicator)


        #SHORTCUTS

        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save)

        debug_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        debug_shortcut.activated.connect(self.getMousePos)

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
        self.loadPasswords()         
       
    def save(self,isbackup : bool = False): # TODO : a popup when saving password : keep the same or change
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
                pw=w.getText()
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
        if not isbackup : self.indicator.set("Saved","green") 
        else : self.indicator.temp_message("Backed up",('green', 200),1)
        
                        
        
           #◃ 
           #ᓡ
                 
    def newPassword(self):
        
        new_pass_lay=spk_password.Password(self.var,name = "New Password",password_text = "")
        
        try:
            stretch = self.scroll_layout.takeAt(self.scroll_layout.count() -1 )                   
            if isinstance(stretch,QSpacerItem) :             
                del stretch   
        except AttributeError:
            self.logger.add("Failed to remove stretch (if the main layout wasn't empty this is a bug)",self.logger.warning)      
        
        self.scroll_layout.addWidget(new_pass_lay) # addWidget
        self.scroll_layout.addStretch()
        self.logger.add("Created new password",self.logger.success)
            
    def deletePassword(self,passw_uuid : uuid_manager.UUID):
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
                    if isinstance(a.widget(),spk_password.Password) : 
                        bl = a.widget().untoggleEditing()
                        if bl : #if the password was edited
                            self.var.current_field_edited = None
                        #a.widget().
                    a.widget().deleteLater() # shadow boxes if this line is changed
                    self.scroll_layout.removeItem(a)                    
                                 
                    self.logger.add(f"Successfully deleted the password ({tmp_uuid})",self.logger.success) 
                    self.scroll_layout.addStretch()                   
                    break                    
            except Exception as e:
                self.logger.add(f"Exception when deleting the password (position {i}): {e}",self.logger.error)        
        else:
            self.logger.add("No password was deleted",self.logger.warning)

    def createScrollArea(self,content):
       
        w=QWidget()
        l=QVBoxLayout(w)        
        for el in content: 
            try:
                name, password, uuid = el  
                p_l=spk_password.Password(self.var,name=name,password_text=password,uuid=uuid)            
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
      
