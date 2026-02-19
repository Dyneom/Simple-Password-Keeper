from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QFont



import sys
import spk_manager
import spk_variables

if __name__ == "__main__":

    vars = spk_variables.SpkVariables(current_field_edited=None,current_shown_fields=[])
    vars.loadConfig("spk_settings.json")
    vars.loadTheme("spk.conf")  
    font = QFont(vars.theme.get("font").get("font"))    
    font.setPixelSize(int(vars.theme.get("font").get("size")))
    
    app = QApplication()  
    app.setFont(font)
    spk_app = spk_manager.SimplePasswordKeeper(dir="",var=vars) 
    vars.manager = spk_app
    app.setStyle(QStyleFactory.create(vars.theme.get("global").get("global")))
    spk_app.setStyleSheet(vars.theme.get("background").to_config())     
    
    spk_app.show()
    sys.exit(app.exec())
   






# TODO LIST:  
# - be able to change the master password
# - import passwords
# - export passwords (copy the file :) ) 
# - make it able to run with argparse
# - Sort / Minecraft world sort ?



