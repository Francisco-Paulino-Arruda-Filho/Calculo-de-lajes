import sys
from PySide6.QtWidgets import QApplication
from gui import Janela

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = Janela()
    janela.show()
    sys.exit(app.exec())