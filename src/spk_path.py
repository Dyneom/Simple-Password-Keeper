from PySide6.QtWidgets import QLabel                             


class SpkPath(QLabel):

    def __init__(self,var,text = ""):
        super().__init__(text)
        self.var = var
        self.setStyleSheet(var.theme.get("path").to_config())

    def refresh(self):
        self.setText(self.var.current_node.getPath())
