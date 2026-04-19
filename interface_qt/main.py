import sys
from PyQt6 import QtWidgets, uic

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/interface.ui", self)

        # encontra o scroll area pelo nome do Designer
        self.scroll = self.findChild(QtWidgets.QScrollArea, "scrBotoes")

        # instala filtro de evento
        self.scroll.viewport().installEventFilter(self)

        # conecta botões às páginas
        self.btnDash.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.btnTemperatura.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.btnPressao.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.btnHumidade.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.btnLuminosidade.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        self.btnPM.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(5))
        self.btnNC.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(6))
        self.btnDados.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(7))

    def eventFilter(self, source, event):
        if event.type() == event.Type.Wheel and source is self.scroll.viewport():
            # move horizontal ao invés de vertical
            delta = event.angleDelta().y()
            self.scroll.horizontalScrollBar().setValue(
                self.scroll.horizontalScrollBar().value() - delta
            )
            return True
        return super().eventFilter(source, event)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())