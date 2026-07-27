#this file is to run the project directly with python, to use the command line interface see the main.py folder (default is with verbose)

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QFont

import sys
import spk_manager
import spk_variables



if __name__ == "__main__":
    app = QApplication()  

    vars = spk_variables.SpkVariables(isVerbose=True,current_field_edited=None,current_shown_fields=[],config="spk_settings.json",theme="spk.conf")
    
    font = QFont(vars.theme.get("font").get("font"))    
    font.setPixelSize(int(vars.theme.get("font").get("size")))
    
    
    app.setFont(font)
    spk_app = spk_manager.SimplePasswordKeeper(dir="",var=vars)     
    app.setStyle(QStyleFactory.create(vars.theme.get("global").get("global")))
    spk_app.setStyleSheet(vars.theme.get("background").to_config())     
    
    spk_app.show()
    sys.exit(app.exec())


   
    



# TODO:
#   add a copy-like system (CTRL-C / CTRL-X -> CTRL-V)