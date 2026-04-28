help_string = """This file is made to run the Simple Password Keeper project through the terminal.
It allows multiple things:
-c, --config: path to the config  
-h, --help: display this help
-p, --passwords: path to the password file -- doesn't work for now
-t, --theme: path to the theme file
 """

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QFont

import sys
import os
import spk_manager

import spk_variables






args = sys.argv
config = "spk_settings.json"
theme = "spk.conf"
password_path = "d"

for i in range(1,len(args)):
    if args[i] == "-h" or args[i] == "--help":
        print(help_string)
        exit(0)
    elif i==len(args)-1:
        break
    elif args[i] == "-c" or args[i] == "--config":        
        if os.path.exists(args[i+1]):
            config = args[i+1]
    elif args[i] == "-t" or args[i] == "--theme":
        if os.path.exists(args[i+1]):
            theme = args[i+1]     
    elif args[i] == "-p" or args[i] == "--passwords":
        if os.path.exists(args[i+1]):
            password_path = args[i+1]




 
app = QApplication()  

vars = spk_variables.SpkVariables(current_field_edited=None,current_shown_fields=[],config=config,theme=theme)
    
font = QFont(vars.theme.get("font").get("font"))    
font.setPixelSize(int(vars.theme.get("font").get("size")))
    
    
app.setFont(font)
spk_app = spk_manager.SimplePasswordKeeper(dir="",var=vars) 
vars.manager = spk_app
app.setStyle(QStyleFactory.create(vars.theme.get("global").get("global")))
spk_app.setStyleSheet(vars.theme.get("background").to_config())     

spk_app.show()
sys.exit(app.exec())
font = QFont(vars.theme.get("font").get("font"))    
font.setPixelSize(int(vars.theme.get("font").get("size")))
    
    
app.setFont(font)
spk_app = spk_manager.SimplePasswordKeeper(dir="",var=vars) 
vars.manager = spk_app
app.setStyle(QStyleFactory.create(vars.theme.get("global").get("global")))
spk_app.setStyleSheet(vars.theme.get("background").to_config())     

spk_app.show()
sys.exit(app.exec())