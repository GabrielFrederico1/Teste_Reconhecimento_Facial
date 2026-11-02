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

# --- Distância da câmera (heurística pela distância entre os olhos) ---
# A distância entre os cantos externos dos olhos (landmarks 33 e 263) é mais estável
# que a bounding box, pois varia pouco com a pose. Valor = fração da largura do frame.
# (referência: antiga faixa de bbox 0.15~0.70 equivalia a ~0.06~0.28 em distância entre olhos)
# REGISTRO: faixa estreita, pois define o embedding de referência.
REGISTRO_DIST_OLHOS_MIN = 0.10  # abaixo -> longe demais
REGISTRO_DIST_OLHOS_MAX = 0.20  # acima  -> perto demais
# DESTRAVAMENTO: faixa mais tolerante.
DESTRAVAMENTO_DIST_OLHOS_MIN = 0.09
DESTRAVAMENTO_DIST_OLHOS_MAX = 0.22

# --- Pose do rosto (desvio tolerado em relação ao rosto frontal) ---
# yaw: desvio da ponta do nariz em relação ao centro entre as bochechas (0 = frontal)
# pitch: desvio da posição vertical do nariz entre testa e queixo (0 = frontal)
PITCH_CENTRO = 0.54  # calibrado: rosto frontal media pitch ~-0.06/-0.03 com centro 0.58
REGISTRO_YAW_MAX = 0.08
REGISTRO_PITCH_MAX = 0.12
DESTRAVAMENTO_YAW_MAX = 0.14
DESTRAVAMENTO_PITCH_MAX = 0.20

# --- Nitidez (variância do Laplaciano no recorte do rosto, em 112x112) ---
# Calibrar olhando o valor exibido na tela do registro.
REGISTRO_NITIDEZ_MIN = 60.0
DESTRAVAMENTO_NITIDEZ_MIN = 30.0

# --- Registro com múltiplas capturas ---
REGISTRO_NUM_CAPTURAS = 5          # frames válidos usados para a média do embedding
REGISTRO_INTERVALO_FRAMES = 8      # frames entre capturas (gera variação natural de pose)
REGISTRO_SIM_MIN_ENTRE_CAPTURAS = 0.75  # capturas muito diferentes entre si são descartadas

# --- Detecção de acessórios (heurística via confiança dos landmarks) ---
# Óculos (inclusive de grau): intensidade de bordas (armação) sob os olhos/ponte do nariz.
# Acima disso -> óculos. Valor inicial ESTIMADO: calibrar com o "Bordas olhos" exibido no registro.
BORDAS_MAX_OLHOS = 0.35  # calibrado: sem óculos ~0.20, com óculos de grau ~0.50
# (CONFIANCA_MIN_OLHOS não é mais usado na decisão; a variância de z varia com distância/pose)
CONFIANCA_MIN_OLHOS = 0.0190  # ajustado com base nos testes reais do usuário (com oculos: 0.018, sem: 0.02)
CONFIANCA_MIN_BOCA = 0.035   # calibrado: sem máscara (com barba) ~0.045, com máscara ~0.025

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
