
from PySide6.QtGui import QIcon

from PySide6.QtWidgets import QLineEdit, QMessageBox, QInputDialog, QFileDialog 
from hashlib import pbkdf2_hmac # for sha256

import argon2
import base64
import os 

#spk
import spk_logs
import spk_file_manager
import spk_password
import spk_folder


class WrongFileSyntax(Exception): pass

#handle the decryption prompts and the convertion to existing classes
class Spk_Encryption(spk_file_manager.FileManager):

    sha_256_iter = 5_000_000
    def __init__(self,var,file_dir):
        self.var = var
        super().__init__(self.var,file_dir)
        self.logger = spk_logs.Logger(self.var,True,False,f"Encryption {file_dir}")
        self.isSaved = False

    def ask_password(self,message :str,hide = True):
        dialog=QInputDialog(self.var.manager) 
             
        if hide : dialog.setTextEchoMode(QLineEdit.EchoMode.NoEcho)
        dialog.setLabelText(message)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setCancelButtonText("Exit")
        dialog.setStyleSheet(self.var.theme.get("dialog_password_main").to_config())
        
        dialog.children()[0].setStyleSheet(self.var.theme.get("dialog_password_message").to_config())
        dialog.children()[1].setStyleSheet(self.var.theme.get("dialog_password_password").to_config())
        dialog.children()[2].setStyleSheet(self.var.theme.get("dialog_password_buttons").to_config())
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
    

    def changePassword(self,message = "Hello, to what do you want to change your password?" ): #True is the password was changed else False
        self.logger.add("Trying to change password",self.logger.verbose)
        hash_func = pbkdf2_hmac
        result = 1
        pw = ""      
        self.gen_salt() #salt change
        
        l = 5   # min password length
        while result == 1 and len(pw) < l:
            result, pw = self.ask_password(message,hide = False) 
            message = f"The lenght of the password must be at least equal to {l}"
        if result == 0: return False # not set
        ph = argon2.PasswordHasher(time_cost=10,memory_cost=1000,hash_len=32) 
        sha_256 = hash_func('sha256', bytes(pw,encoding='utf8'), self.salt, self.sha_256_iter)         
        self.setFernet(base64.urlsafe_b64encode(sha_256)) 
        self.set_hash(ph.hash(password=sha_256,salt=self.salt))  # change the hash
        
        self.logger.add("New password set")
        return True
    

    def message_popup(self,title,message,error_level = spk_logs.Logger.information):        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)        
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet(self.var.theme.get("dialog").to_config())
        msg.setStandardButtons(QMessageBox.Ok)
        self.logger.add("Prompt: " + message,error_level)
        msg.exec()
    
    def handle_password_at_start(self): #if the file exists : returns True if the file was valid, else returns False; if the file doesn't exist: can return False if the user choose to abort
        self.logger.add("Handleling password prompt",self.logger.verbose)
        if self.reason and self.hash == None:
            if self.reason == "Creation":
                return self.changePassword()
            elif self.reason == "Wrong syntax":
                self.message_popup("Invalid file","The syntax of the given file is wrong",self.logger.error)
                return False
            
        # the file exists and is correct -> file decryption

        self.hash = str(self.hash,encoding="utf8")
        result,p_w = self.ask_password("Input your password")    
        ph = argon2.PasswordHasher(time_cost=10,memory_cost=1000,hash_len=32)
        while result == 1 and not self.verify_password(password_hasher=ph,pw=p_w):
            result,p_w = self.ask_password("Wrong Password") 

        if result == 1:return True
        return False

    def verify_password(self,password_hasher,pw) -> bool:
        try:
            pw_h=pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), self.salt, self.sha_256_iter)            
            password_hasher.verify(self.hash,pw_h) 
            #If no exception was raised
            pw_hmain= base64.urlsafe_b64encode(pbkdf2_hmac('sha256', bytes(pw,encoding='utf8'), self.salt, self.sha_256_iter))
            pw = "NO" 
            
            self.setFernet(pw_hmain)
            return True
        except argon2.exceptions.VerifyMismatchError :
            return False      

    def createPasswordTree(self,change_uuid = False,load_content = True):
        chr1,chr2,chr3,chr4 = self.var.character
        if load_content:
            self.load_encrypted_content()
            worked = self.decrypt_content()
        else:
            worked = True
        if worked:
            pw_list = []
            content = self.get_content()
            if content != "":                
                try:
                    self.save_to_layout(change_uuid=change_uuid)    #automaticaly set it to root               
                except NotADirectoryError as e:
                    self.logger.add(f"THIS IS A BUG : Problem occured when trying to recreate the password layout, a password could be missing (Exception : {e})",self.logger.critical_error) #you can add "when extracting : {content}" to know what makes the error (it isn't done due to security reasons)
   
    def save_to_layout(self,change_uuid = False ): # input is the decrypted save, output is the root with all the passwords and folders in it
        chr1,chr2,chr3,chr4 = self.var.character
        s = self.content
        root = self.var.root
        stack = [root]
        while stack != [] and s != "":
            i,chr = self.get_next(s,[chr1,chr2,chr3]) # must handle the error 
            if chr == chr1: #password

                s = s[i+1:] 

                name_end = self.get_next(s,chr)
                name = s[:name_end]
                s = s[name_end+1:] 

                uuid_end = self.get_next(s,chr)          
                uuid = s[:uuid_end] if not change_uuid else ""
                s = s[uuid_end+1:]

                if s != "":
                    pw_end,_ = self.get_next(s,[chr1,chr2,chr3])          
                    pw = s[:max(0,pw_end-1)]
                    s = s[pw_end:]
                else:
                    pw = ""

                spk_password.Password(self.var,parent=stack[-1],name=name,password_text=pw,uuid=uuid)           
            elif chr == chr2: # folder
                s = s[i+1:] 


                name_end = self.get_next(s,chr)
                name = s[:name_end]
                s = s[name_end+1:] 
                

                uuid_end = self.get_next(s,chr)          
                uuid = s[:uuid_end] if not change_uuid else ""
                s = s[uuid_end+1:]
                f = spk_folder.Folder(variables=self.var,parent=stack[-1],name=name,children=[],uuid=uuid)
                        
                stack.append(f)
                
            elif chr == chr3: #end of a folder
                s = s[i+1:]
                stack.pop()

    def get_next(self,s : str, chars): 
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

            
    def import_passwords(self): # work in progress...
        self.logger.add("Trying to import passwords",self.logger.information)
        if not self.close_save_prompt(): return
        self.var.manager.save()
        file_name = QFileDialog().getOpenFileName(self.var.manager,"Import passwords",os.getcwd(), "Spk Files (*.spk)")
        
        if len(file_name) == 0 or file_name[0] == "": return
        file1 = file_name[0]
        if self.file_dir[0] == "/": #abs path
            file2 = self.file_dir
        else: #relative path
            file2 = os.getcwd() + "/" + self.file_dir   

        

        if file1 == file2 : 
            return False

        
        file1_encry = Spk_Encryption(self.var,file1)
        return_val = file1_encry.handle_password_at_start()
        if return_val == False:
            return False
        #at this point: worked
        file1_encry.decrypt_content()
        content1 = file1_encry.get_content() # considers the content as valid (TODO: a checker) 
        
        content2 = self.get_content()
        self.set_content(content1 + content2)        
        self.var.root.setChildren([],copy=False) #reset the children
        self.createPasswordTree(True, False)
        self.var.current_node = self.var.root # set the view to root        
        self.var.manager.createArea() # updates the layout
        

       
        #self.file_manager.set_content( content1 + content2)

    def save_prompt(self) -> bool: #returns True if the user choose to save
        self.logger.add("Asking the user to save")
        msg = QMessageBox()
        #msg.setIcon(QMessageBox.Question)        
        msg.setWindowTitle("Save?")
        msg.setText("Do you want to save?")
        msg.setStyleSheet(self.var.theme.get("dialog").to_config())
        msg.setStandardButtons(QMessageBox.Yes)        
        msg.addButton(QMessageBox.No)  
        msg.setDefaultButton(QMessageBox.Yes) 
        msg.children()[3].setStyleSheet(self.var.theme.get("dialog_password_buttons").to_config())    
        msg.children()[2].setStyleSheet(self.var.theme.get("dialog_password_message").to_config())    
             
              
        result = msg.exec()
        if result == 0x4000: #Yes
            return True    
        return False

    def close_save_prompt(self): # 1 -> true, 0 -> false, -1 -> Cancel; if already saved -> returns 1
        if self.isSaved: 
            return 1
        self.logger.add("Asking the user to save before closing")
        msg = QMessageBox()
        #msg.setIcon(QMessageBox.Question)        
        msg.setWindowTitle("Save before closing")
        msg.setText("Do you want to save before closing?")
        msg.setStyleSheet(self.var.theme.get("dialog").to_config())
        msg.setStandardButtons(QMessageBox.Cancel)        
        msg.addButton(QMessageBox.Yes)  
        msg.addButton(QMessageBox.No)  
        msg.setDefaultButton(QMessageBox.Yes)  

        msg.children()[3].setStyleSheet(self.var.theme.get("dialog_password_buttons").to_config())    
        msg.children()[2].setStyleSheet(self.var.theme.get("dialog_password_message").to_config())    
        
        result = msg.exec()
        if result == 0x4000: #Yes
            return 1 
        elif result == 0x400000: #Cancel
            return -1
        return 0
    
    def setSaved(self,b: bool):
        self.isSaved = b
        if self.isSaved == False:
            self.var.indicator.set("Not saved","blue")
        else:
            self.var.indicator.set("Saved","green")




            

            
            



