import sys
from PyQt6 import QtWidgets, QtGui, QtCore, uic
import requests


class DeviceCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal()  # sinal customizado

    def __init__(self, name, lat, lon):
        super().__init__()

        self.setObjectName("card")

        self.name = name.lower()

        self.setFixedHeight(80)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(20)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        # imagem
        icon = QtWidgets.QLabel()
        icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pixmap = QtGui.QPixmap("imgs/module2.png")
        icon.setPixmap(pixmap.scaled(40, 40, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(icon)
        icon.setFixedSize(40, 40)

        # textos
        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setSpacing(5)
        text_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.label_name = QtWidgets.QLabel(name)
        self.label_name.setStyleSheet("font-weight: 600; font-size: 14px;")

        self.label_coords = QtWidgets.QLabel(f"Latitude: {lat}, Longitude: {lon}")
        self.label_coords.setStyleSheet("color: rgb(160,160,160); font-size: 11px;")

        text_layout.addWidget(self.label_name)
        text_layout.addWidget(self.label_coords)

        layout.addLayout(text_layout)
        layout.addStretch()

        # estilo moderno
        self.setStyleSheet("""
            #card {
                background-color: rgb(50, 50, 50);
                border: 2px solid rgb(70, 70, 70);
                border-radius: 10px;
            }

            #card:hover {
                border: 2px solid #3daee9;
                background-color: rgb(60, 60, 60);
            }

            #card:pressed {
                background-color: rgb(40, 40, 40);
                border: 2px solid #3daee9;
            }

            QLabel {
                background: transparent;
                color: #ebebeb;
                border: none;
            }
        """)

    # clique do mouse
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/interface.ui", self)

        # ===== SCROLL HORIZONTAL (botões) =====
        self.scroll = self.findChild(QtWidgets.QScrollArea, "scrBotoes")
        self.scroll.viewport().installEventFilter(self)

        # ===== BOTÕES → PÁGINAS =====
        self.btnDash.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.btnTemperatura.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.btnPressao.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.btnHumidade.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.btnLuminosidade.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        self.btnPM.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(5))
        self.btnNC.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(6))
        self.btnDados.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(7))

        # ===== LISTA DE DISPOSITIVOS =====
        self.scrollLista = self.findChild(QtWidgets.QScrollArea, "scrollDevices")
        self.inputBusca = self.findChild(QtWidgets.QLineEdit, "inputBusca")

        self.container = QtWidgets.QWidget()
        self.layoutLista = QtWidgets.QVBoxLayout(self.container)
        self.layoutLista.setSpacing(8)
        self.layoutLista.setContentsMargins(0, 0, 0, 0)

        self.scrollLista.setWidget(self.container)
        self.scrollLista.setWidgetResizable(True)

        self.cards = []

        # exemplo inicial (depois vem do backend)
        self.carregar_devices()

        # empurra tudo pra cima
        self.layoutLista.addStretch()

        # ===== BUSCA EM TEMPO REAL =====
        self.inputBusca.textChanged.connect(self.filtrar_lista)
        
        #self.timer = QtCore.QTimer()
        #self.timer.timeout.connect(self.carregar_devices)
        #self.timer.start(5000)  # atualiza a cada 5s
        

    # ===== SCROLL HORIZONTAL BOTÕES GRÁFICOS =====
    def eventFilter(self, source, event):
        if event.type() == event.Type.Wheel and source is self.scroll.viewport():
            delta = event.angleDelta().y()
            self.scroll.horizontalScrollBar().setValue(
                self.scroll.horizontalScrollBar().value() - delta
            )
            return True
        return super().eventFilter(source, event)
    
    # ======= BUSCA DE MODULOS NO SERVIDOR ===========
    def carregar_devices(self):
        try:
            response = requests.get("http://127.0.0.1:8000/devices", timeout=2)
            devices = response.json()

            self.atualizar_lista(devices)

        except Exception as e:
            print("Erro ao conectar com servidor:", e)

    # ======= ATUALIZA A LISTA DE MODULOS ===========
    def atualizar_lista(self, devices):
        # limpa lista atual
        for card in self.cards:
            card.deleteLater()

        self.cards.clear()

        # adiciona novos
        for device in devices:
            device_id, name, lat, lon, *_ = device
            self.add_device(name, lat, lon)

    # ===== ADICIONAR DISPOSITIVO LISTA MODULOS =====
    def add_device(self, name, lat, lon):
        card = DeviceCard(name.title(), lat, lon)

        # conecta o clique
        card.clicked.connect(lambda n=name: self.on_card_clicked(n))

        self.layoutLista.insertWidget(self.layoutLista.count() - 1, card)
        self.cards.append(card)

    # ===== FILTRO MODULOS PESQUISA =====
    def filtrar_lista(self, texto):
        texto = texto.lower()

        for card in self.cards:
            if texto in card.name:
                card.show()
            else:
                card.hide()

    def on_card_clicked(self, name):
        print(f"Clicou no dispositivo: {name}")


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())