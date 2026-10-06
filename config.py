"""
Configurações centrais do protótipo de reconhecimento facial.
Ajuste os limiares aqui conforme os testes com a câmera/webcam real.
"""

# --- Banco de embeddings (protótipo: JSON local; em produção seria uma tabela no backend) ---
DB_PATH = "usuarios_embeddings.json"

# --- Matching ---
# Similaridade de cosseno mínima para considerar "mesma pessoa".
# Precisa ser calibrado empiricamente com o modelo de embedding escolhido.
LIMIAR_SIMILARIDADE = 0.85

# --- Distância da câmera (heurística por bounding box) ---
# Fração da largura do frame que o rosto deve ocupar para ser considerado "perto o suficiente".
DISTANCIA_MIN_PROPORCAO = 0.15  # rosto muito pequeno -> pessoa longe demais
DISTANCIA_MAX_PROPORCAO = 0.70  # rosto muito grande -> pessoa colada na câmera

# --- Detecção de acessórios (heurística via confiança dos landmarks) ---
CONFIANCA_MIN_OLHOS = 0.0190  # ajustado com base nos testes reais do usuário (com oculos: 0.018, sem: 0.02)
CONFIANCA_MIN_BOCA = 0.0664   # abaixo disso, suspeita de máscara

# --- Câmera ---
# Para mudar a câmera, altere este valor (ex: mude de 0 para 1, 2, etc.)
CAMERA_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- Caminho do modelo MediaPipe Face Landmarker ---
# Baixar de: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
MODELO_FACE_LANDMARKER = "face_landmarker.task"

# --- Arduino (Display LCD) ---
# Altere para a porta correta onde o Arduino está conectado (ex: 'COM3' no Windows, '/dev/ttyACM0' ou '/dev/ttyUSB0' no Linux)
# Para testar sem o display (Arduino), deixe como None
PORTA_ARDUINO = None
BAUDRATE_ARDUINO = 115200
