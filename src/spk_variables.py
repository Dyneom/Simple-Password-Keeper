#This is a class to sync the variables between the classes. Surely there is a better way to do this but I chose to do this that way
from PySide6.QtGui import QCursor

import spk_password
from logs import Logger
import spk_theme
import json

class SpkVariables():
    def __init__(self,indicator = None,settings = None,theme = None,last_mouse_pos : tuple= None,current_field_edited : spk_password.Password = None,current_shown_fields : list[spk_password.Password] = None,editing :bool = None):
        self.indicator = indicator
        self.settings = settings
        self.theme = theme
        self.global_logs = Logger(display=True,write_in_file=False,name = "global")
        self.last_mouse_pos = last_mouse_pos
        self.current_field_edited = current_field_edited
        self.current_shown_fields = current_shown_fields
        self.editing = editing
        self.manager = None
        self.minimum_password_field_height = 30
        self.password_list = []

    def loadConfig(self,path: str):     

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
    
        with open(path) as json_settings_file:        
            tmp_settings=json.load(json_settings_file)
            
        
        for u_ in default_settings.keys():
            if not u_ in tmp_settings:
                self.global_logs.add(f"Missing argument in config, the valid args are {default_settings.keys()}",self.global_logs.warning)
        self.settings = spk_theme.ConfigDicts(tmp_settings,default=default_settings)
      


    def loadTheme(self,path):
        self.theme = spk_theme.SpkTheme(path,settings=self.settings) 


    def resetMousePos(self):
        self.last_mouse_pos = (QCursor.pos() ,1)
