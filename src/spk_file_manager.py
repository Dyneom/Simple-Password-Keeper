import os
import logs
import datetime
from cryptography.fernet import Fernet
import cryptography
import binascii




class FileManager():
    
    def __init__(self,key,settings,file_dir,content="",encrypted_content=bytes()):
        super().__init__()        
        self.file_logger = logs.Logger(display=settings.to_settings("logs"),write_in_file=False,name="file_manager")
        self.file_dir=file_dir
        self.content = content
        self.settings = settings
        
        #self.fernet=Fernet(key) 
        
        #init 
        if not os.path.exists(file_dir):
            with open(file_dir,"w") as f:
                self.encrypted_content = bytes()
                self.salt = os.urandom(256)
                self.hash = None
        else:
            with open(file_dir,"rb") as f2:
                tmp_e_c = f2.read()                                   
                hash_len_bytes = tmp_e_c[:4]
                hash_len = int.from_bytes(hash_len_bytes)
                if len(tmp_e_c) > 256 + hash_len + 4 : # 256  -> urandom                       
                    self.hash = tmp_e_c[4 : hash_len + 4]                        
                    self.salt = tmp_e_c[hash_len + 4 : 256 + hash_len  + 4] 
                    self.encrypted_content = tmp_e_c[256 + hash_len + 4:] 

                                   
                                               
                else: 
                    self.file_logger.add("The saved file has not the right syntax, couldnt parse the content",self.file_logger.error)
                    self.hash = None
                    self.salt = os.urandom(256)
                    self.encrypted_content = bytes()
                    
                
                    
                    
                

        self.file_logger.add("File class created",self.file_logger.success)

    #content managing
    def set_content(self,content,bypass_empty_restriction = False) -> None :
        if content != "" or bypass_empty_restriction:
            self.content = content        
            self.file_logger.add("Contents changed",self.file_logger.information)
            return
        self.file_logger.add("To delete the file content, please use the delete_content function instead (or the bypass_empty_restriction arg, not recommanded)| nothing was changed",self.file_logger.error)

    def delete_content(self) -> None:
        self.content = ""
        self.file_logger.add("File content deleted",self.file_logger.success)
    
    def get_content(self) -> str:
        return self.content
    
    #file directory manager
    def set_file_dir(self,file_dir, update_content = True):
        self.file_dir = file_dir
        if update_content : 
            if not os.path.exists(file_dir):
                with open(file_dir,"w") as f:
                    pass 
            else:
                with open(file_dir,"rb") as f2:
                    self.encrypted_content = f2.read()
        
    def get_file_dir(self) -> str:
        return self.file_dir 

    #encrypted content managing
    def set_encrypted_content(self,encrypted_content, bypass_empty_restriction= False) -> None:
        if encrypted_content != "" or bypass_empty_restriction:
            self.encrypted_content = encrypted_content        
            self.file_logger.add("Encrypted content changed",self.file_logger.information)
            return
        self.file_logger.add("To delete the file (encrypted) content, please use the delete_encrypted_content function instead (or the bypass_empty_restriction arg, not recommanded)| You may want to delete all the passwords deleting the file will be easier :)| nothing was changed",self.file_logger.error)

    def delete_encrypted_content(self) -> None:
        self.encrypted_content = ""
        self.file_logger.add("File encrypted content deleted",self.file_logger.success)
    
    #managing the whole file    
    def load_encrypted_content(self) -> None:
        with open(self.file_dir,"rb") as f:
            tmp_e_c = f.read()                                   
            hash_len_bytes = tmp_e_c[:4]
            hash_len = int.from_bytes(hash_len_bytes)            
            
            if len(tmp_e_c) > 256 + hash_len + 4 : # 256  -> urandom                       
                self.hash = tmp_e_c[4 : hash_len + 4]                        
                self.salt = tmp_e_c[hash_len + 4 : 256 + hash_len  + 4] 
                self.encrypted_content = tmp_e_c[256 + hash_len + 4:] 
                #print("encr :",self.encrypted_content)   
                #print(f"hash is {self.hash} | salt is {self.salt}") 
                self.file_logger.add("Encrypted content loaded",self.file_logger.success)
                return
        if tmp_e_c != b'' : self.file_logger.add("Encrypted content failed to load",self.file_logger.error)

        

    def decrypt_content(self) -> bool: 
        """Decrypt content in the encrypted content variable and puts it in the content variable
        Input:
            - key : the password decryption key
        Output:
            - True if the decryption worked
            - False if it didn't
        """
        try:
            if self.encrypted_content != bytes():     
                #print("encr :",self.encrypted_content)                    
                self.content = str(self.fernet.decrypt(self.encrypted_content),encoding="utf8")
            else:
                self.content = ""
            return True
        except binascii.Error or cryptography.fernet.InvalidToken as e:
            self.file_logger.add(f"Couldn't decrypt the content ({e})",logs.Logger.critical_error)
            return False
        
    def encrypt_content(self, is_backup = False) -> bool: 
        """Encrypt content in the content variable & puts it in the encrypted content variable
        Input:
            - key : the password encryption key
            - is_backup : puts it the backup variable instead of the encrypted content variable
        Output:
            - True if the encryption worked
            - False if it didn't
        """
        try:
            if not is_backup:                        
                self.encrypted_content = self.fernet.encrypt(bytes(self.content,encoding="utf8")) 
            else : 
                self.backup_encrypted_content = self.fernet.encrypt(bytes(self.content,encoding="utf8"))
                return
            return True
        except binascii.Error:
            self.file_logger.add("Couldn't encrypt the content",logs.Logger.critical_error)
            return False

    def save(self,is_backup = False,silent = False) -> None:  
        dir = self.file_dir if not is_backup else self.settings.to_settings("backup_file")
        what_is_done = ("saving", "save") if not is_backup else ("backing up", "backup")  
        try : os.mkdir(".spkbackups") 
        except FileExistsError : pass
        try : os.mkdir(self.settings.to_settings("dump_directory"))
        except FileExistsError : pass

        try :
            content_to_save = self.encrypted_content if not is_backup else self.backup_encrypted_content
            if isinstance(self.hash,bytes) : 
                header  = self.hash + self.salt            
            elif isinstance(self.hash,str): 
                header  = bytes(self.hash,encoding="utf8") + self.salt          
            elif self.hash == None:                 
                raise ValueError("Hash is shouldnt be None at this point")  
            else: 
                raise ValueError(f"Incorrect type for hash : {type(self.hash)}")  
            
            with open(dir,"wb") as f:
                f.write(len(self.hash).to_bytes(length=4)+header+content_to_save)
            if not silent : self.file_logger.add(f"A {what_is_done[1]} has been made (file: {dir})")

        except Exception as e : 
            self.file_logger.add(f"Problems when {what_is_done[0]} : {e}",self.file_logger.critical_error)
            with open(f"{self.settings.to_settings("dump_directory")}/spk_dump_{datetime.datetime.now().strftime("%d_%m_%Y_%H:%M:%S:%f")[:-3]}.spk","wb") as f2:
                f2.write(content_to_save)
        
    def make_backup(self) -> None:
        self.encrypt_content(is_backup=True)
        self.save(is_backup = True, silent = self.settings.to_settings("backups_silent"))

    def get_salt(self):
        return self.salt

    def get_hash(self):
        return self.hash

    def set_hash(self,hash):
        self.hash = hash
if __name__ == '__main__' : 
    pass


