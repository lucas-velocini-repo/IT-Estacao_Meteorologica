# IT-Estacao_Meteorologica

Projeto para monitoramento de dados ambientais com backend em Python (FastAPI) e interface gráfica em Qt.

---

## Clonando o repositório

1. Abra o **Git Bash** na pasta onde deseja clonar o projeto.

2. Execute:

```bash
git clone <URL_DO_REPOSITORIO>
```

3. Entre na pasta do projeto:

```bash
cd IT-Estacao_Meteorologica
```

---

## Configuração do ambiente

### Configurar o servidor

1. Entre na pasta do servidor:

```bash
cd server
```

2. Crie o ambiente virtual:

```bash
python -m venv .env
```

3. Ative o ambiente:

```bash
source .env/Scripts/activate
```

4. Instale as dependências:

```bash
pip install -r requerements.txt
```

5. Desative o ambiente:

```bash
deactivate
```

---

### Configurar a interface (Qt)

1. Volte para a raiz do projeto:

```bash
cd ..
```

2. Entre na pasta da interface:

```bash
cd interface_qt
```

3. Crie o ambiente virtual:

```bash
python -m venv .env
```

4. Ative o ambiente:

```bash
source .env/Scripts/activate
```

5. Instale as dependências:

```bash
pip install -r requerements.txt
```

---

## Executando o projeto

### Rodar o servidor

1. Volte para a raiz:

```bash
cd ..
```

2. Certifique-se de que o ambiente está desativado:

```bash
deactivate
```

3. Entre na pasta do servidor:

```bash
cd server
```

4. Ative o ambiente:

```bash
source .env/Scripts/activate
```

5. Execute o servidor:

```bash
uvicorn servidor:app --reload
```

---

## Testando a API

1. Acesse no navegador:

```
http://127.0.0.1:8000/docs#
```

2. Vá até a rota **POST /dados**

3. Envie um JSON no seguinte formato:

```json
{
  "device_id": 1,
  "device_name": "estacao piloto",
  "timestamp": 123456789,
  "location": {
    "lat": -23.5,
    "lon": -47.2
  },
  "pm": {
    "1.0": 12.34,
    "2.5": 23.45,
    "4.0": 34.56,
    "10.0": 45.67
  },
  "nc": {
    "0.5": 100.12,
    "1.0": 90.34,
    "2.5": 80.56,
    "4.0": 70.78,
    "10.0": 60.90
  },
  "typical_size": 1.23,
  "light": 456.78,
  "temperature": 25.67,
  "humidity": 60.12,
  "pressure": 1013.25
}
```

---

## Rodando a interface gráfica

1. Abra **outro terminal Git Bash** na raiz do projeto.

2. Entre na pasta da interface:

```bash
cd interface_qt
```

3. Certifique-se de que o ambiente está desativado:

```bash
deactivate
```

4. Ative o ambiente:

```bash
source .env/Scripts/activate
```

5. Execute a aplicação:

```bash
python main.py
```

---

## Observações

* Certifique-se de que o servidor está rodando antes de iniciar a interface.
* Caso haja erro de dependências, verifique o arquivo `requerements.txt`.
* Sempre ative o ambiente virtual antes de rodar qualquer parte do projeto.

---

