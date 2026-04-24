import sys
from PyQt6 import QtWidgets, QtGui, QtCore, uic
import requests
import pyqtgraph as pg


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

        # ====== CONFIGURAÇÕES INICIAIS =====
        self.stackedWidget.setCurrentIndex(0)
        self.selected_device_id = None
        self.atualizar_estado_botoes()

        # ===== SCROLL HORIZONTAL (botões) =====
        self.scroll = self.findChild(QtWidgets.QScrollArea, "scrBotoes")
        self.scroll.viewport().installEventFilter(self)

        # ===== BOTÕES → PÁGINAS =====
        self.btnDash.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.btnTemperatura.clicked.connect(lambda: self.trocar_pagina(1))
        self.btnPressao.clicked.connect(lambda: self.trocar_pagina(2))
        self.btnHumidade.clicked.connect(lambda: self.trocar_pagina(3))
        self.btnLuminosidade.clicked.connect(lambda: self.trocar_pagina(4))
        self.btnPM.clicked.connect(lambda: self.trocar_pagina(5))
        self.btnNC.clicked.connect(lambda: self.trocar_pagina(6))
        self.btnDados.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(7))

        # ====== CONECTANDO GRÁFICOS AOS BOTÕES ======
        self.graficoTemperatura = self.findChild(pg.PlotWidget, "graficoTemperatura")
        self.graficoPressao = self.findChild(pg.PlotWidget, "graficoPressao")
        self.graficoHumidade = self.findChild(pg.PlotWidget, "graficoHumidade")
        self.graficoLuminosidade = self.findChild(pg.PlotWidget, "graficoLuminosidade")
        self.graficoPM = self.findChild(pg.PlotWidget, "graficoPM")
        self.graficoNC = self.findChild(pg.PlotWidget, "graficoNC")

        self.btnTemperaturaAtualizar.clicked.connect(
            lambda: self.carregar_grafico("temperature", self.graficoTemperatura)
        )
        self.btnPressaoAtualizar.clicked.connect(
            lambda: self.carregar_grafico("pressure", self.graficoPressao)
        )
        self.btnHumidadeAtualizar.clicked.connect(
            lambda: self.carregar_grafico("humidity", self.graficoHumidade)
        )
        self.btnLuminosidadeAtualizar.clicked.connect(
            lambda: self.carregar_grafico("light", self.graficoLuminosidade)
        )
        self.btnPMAtualizar.clicked.connect(
            lambda: self.carregar_grafico("pm_2_5", self.graficoPM)
        )
        self.btnNCAtualizar.clicked.connect(
            lambda: self.carregar_grafico("nc_1_0", self.graficoNC)
        )

        # ===== LISTA DE DISPOSITIVOS =====
        self.scrollLista = self.findChild(QtWidgets.QScrollArea, "scrollDevices")
        self.inputBusca = self.findChild(QtWidgets.QLineEdit, "inputBusca")

        self.lblTitulo = self.findChild(QtWidgets.QLabel, "lblTitulo")
        self.lblDashEstacao = self.findChild(QtWidgets.QLabel, "lblDashEstacaoNome")

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

        # ===== EXEMPLO GRÁFICO (pyqtgraph) =====
        self.graph = self.findChild(pg.PlotWidget, "graficoTemperatura")

        x = [1, 2, 3, 4]
        y = [10, 20, 15, 30]

        self.graph.plot(x, y, pen='b')

        self.vb = self.graph.getViewBox()
        
    def carregar_grafico(self, parametro, grafico):
        if self.selected_device_id is None:
            print("Selecione um dispositivo primeiro")
            return

        try:
            url = f"http://127.0.0.1:8000/timeseries?device_id={self.selected_device_id}&parameter={parametro}&limit=50"

            response = requests.get(url, timeout=2)
            data = response.json()

            y = data["values"]

            if not y:
                print("Sem dados")
                return

            x = list(range(len(y)))

            grafico.clear()
            grafico.plot(x, y, pen='c', symbol='o')

        except Exception as e:
            print("Erro:", e)

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
        self.device_map = {} 

        for card in self.cards:
            card.deleteLater()

        self.cards.clear()

        for device in devices:
            device_id, name, lat, lon, *_ = device

            # salva relação nome → id
            self.device_map[name.lower()] = device_id

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

    # ===== CLIQUE NO CARD DO DISPOSITIVO =====
    def on_card_clicked(self, name):
        self.selected_device_id = self.device_map.get(name.lower())
        self.lblTitulo.setText(f"Interface de monitoramento - {name.title()}")
        self.lblDashEstacao.setText(f"{name.title()}")

        print(f"Selecionado: {name} | ID: {self.selected_device_id}")
        self.atualizar_estado_botoes()
        self.atualizar_grafico_atual()

    # ===== HABILITA/DESABILITA BOTÕES DE PARÂMETROS =====
    def atualizar_estado_botoes(self):
        sem_modulo = (self.selected_device_id is None)

        self.btnTemperatura.setEnabled(not sem_modulo)
        self.btnPressao.setEnabled(not sem_modulo)
        self.btnHumidade.setEnabled(not sem_modulo)
        self.btnLuminosidade.setEnabled(not sem_modulo)
        self.btnPM.setEnabled(not sem_modulo)
        self.btnNC.setEnabled(not sem_modulo)
        self.btnDados.setEnabled(not sem_modulo)

    # ===== RESETA INTERFACE (SEM DISPOSITIVO SELECIONADO) =====
    def resetar_modulo(self):
        self.selected_device_id = None
        self.lblTitulo.setText("Interface de monitoramento")
        self.atualizar_estado_botoes()

    # self.btnDash.clicked.connect(self.resetar_modulo) #Conectar botão para resetar a seleção

    # ===== ATUALIZA GRÁFICO ATUAL (APÓS SELEÇÃO DE DISPOSITIVO OU TELA) =====
    def atualizar_grafico_atual(self):
        if self.selected_device_id is None:
            return

        index = self.stackedWidget.currentIndex()

        if index == 1:
            self.carregar_grafico("temperature", self.graficoTemperatura)

        elif index == 2:
            self.carregar_grafico("pressure", self.graficoPressao)

        elif index == 3:
            self.carregar_grafico("humidity", self.graficoHumidade)

        elif index == 4:
            self.carregar_grafico("light", self.graficoLuminosidade)

        elif index == 5:
            self.carregar_grafico("pm_2_5", self.graficoPM)

        elif index == 6:
            self.carregar_grafico("nc_1_0", self.graficoNC)
    
    # ===== TROCA DE PÁGINA (ATUALIZA GRÁFICO) =====
    def trocar_pagina(self, index):
        self.stackedWidget.setCurrentIndex(index)
        self.atualizar_grafico_atual()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())