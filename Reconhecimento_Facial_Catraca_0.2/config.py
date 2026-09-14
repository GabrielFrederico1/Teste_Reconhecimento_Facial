"""
Configurações centrais do protótipo de reconhecimento facial.
Ajuste os limiares aqui conforme os testes com a câmera/webcam real.
"""

# --- Banco de embeddings (protótipo: JSON local; em produção seria uma tabela no backend) ---
DB_PATH = "usuarios_embeddings.json"

# --- Matching ---
# Similaridade de cosseno mínima para considerar "mesma pessoa".
# Precisa ser calibrado empiricamente com o modelo de embedding escolhido.
# Com o MobileFaceNet real, valores tipicos de referencia ficam entre 0.5 e 0.65
# (varia por modelo/conversao) — 0.75 era calibrado para o placeholder geometrico
# e tende a ficar rigoroso demais agora; teste e ajuste com seus proprios dados.
LIMIAR_SIMILARIDADE = 0.6

# --- Distância da câmera (heurística por bounding box) ---
# Fração da largura do frame que o rosto deve ocupar para ser considerado "perto o suficiente".
DISTANCIA_MIN_PROPORCAO = 0.15  # rosto muito pequeno -> pessoa longe demais
DISTANCIA_MAX_PROPORCAO = 0.70  # rosto muito grande -> pessoa colada na câmera

# --- Detecção de acessórios (heurística via confiança dos landmarks) ---
CONFIANCA_MIN_OLHOS = 0.5   # abaixo disso, suspeita de óculos escuros/oclusão
CONFIANCA_MIN_BOCA = 0.5    # abaixo disso, suspeita de máscara

# --- Câmera ---
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- Caminho do modelo MediaPipe Face Landmarker ---
# Baixar de: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
MODELO_FACE_LANDMARKER = "face_landmarker.task"

# --- Caminho do modelo de embedding facial (MobileFaceNet TFLite) ---
# Testado e validado: entrada 112x112x3 float32, saida 192-d ja normalizada.
# Fonte: https://github.com/MCarlomagno/FaceRecognitionAuth (modelo convertido
# a partir dos pesos do InsightFace/MobileFaceNet, uso comunitario amplamente
# replicado). Documentar essa fonte no relatorio do trabalho.
MODELO_EMBEDDING = "mobilefacenet.tflite"
