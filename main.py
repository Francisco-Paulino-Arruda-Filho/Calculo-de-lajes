import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from gui import Janela, caminho_recurso

if __name__ == "__main__":
    app = QApplication(sys.argv)
    icone = caminho_recurso("ico.ico")
    if icone:
        app.setWindowIcon(QIcon(icone))
    janela = Janela()
    janela.show()
    sys.exit(app.exec())