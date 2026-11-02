"""
face_utils.py

Encapsula o MediaPipe Face Landmarker:
  - detecção do rosto mais próximo da câmera
  - estimativa de distância (heurística por bounding box)
  - heurística de acessórios (óculos / máscara) por confiança dos landmarks

Esse módulo é o mesmo em espírito ao que rodaria no app (via MediaPipe Tasks),
mas aqui implementado em Python para rodar no Raspberry Pi.
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

import config


class ResultadoRosto:
    def __init__(self, landmarks, bbox, proporcao_frame, proporcao_olhos=0.0,
                 yaw=0.0, pitch=0.0, nitidez=0.0, bordas_olhos=0.0):
        self.landmarks = landmarks              # lista de landmarks (x, y, z) normalizados
        self.bbox = bbox                         # (x_min, y_min, x_max, y_max) em pixels
        self.proporcao_frame = proporcao_frame   # largura do rosto / largura do frame
        self.proporcao_olhos = proporcao_olhos   # distância entre olhos / largura do frame
        self.yaw = yaw                           # desvio horizontal do nariz (0 = frontal)
        self.pitch = pitch                       # desvio vertical do nariz (0 = frontal)
        self.nitidez = nitidez                   # variância do Laplaciano do recorte
        self.bordas_olhos = bordas_olhos         # intensidade de bordas sob os olhos/ponte do nariz (armação)


def _calcular_pose(landmarks):
    """Estima desvios de yaw/pitch (0 = frontal) a partir de landmarks do FaceMesh."""
    nariz, esq, dir_ = landmarks[1], landmarks[234], landmarks[454]
    testa, queixo = landmarks[10], landmarks[152]
    larg = (dir_.x - esq.x) or 1e-6
    alt = (queixo.y - testa.y) or 1e-6
    yaw = (nariz.x - esq.x) / larg - 0.5
    pitch = (nariz.y - testa.y) / alt - config.PITCH_CENTRO
    return yaw, pitch


def _calcular_nitidez(frame_bgr, bbox) -> float:
    x1, y1, x2, y2 = bbox
    recorte = frame_bgr[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
    if recorte.size == 0:
        return 0.0
    cinza = cv2.cvtColor(cv2.resize(recorte, (112, 112)), cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(cinza, cv2.CV_64F).var())


def _intensidade_bordas(cinza, x1, y1, x2, y2) -> float:
    """
    Intensidade média de gradiente de uma região, normalizada pelo brilho médio.
    A região é redimensionada para tamanho fixo, tornando a métrica independente da distância.
    """
    h, w = cinza.shape
    x1, x2 = max(0, int(x1)), min(w, int(x2))
    y1, y2 = max(0, int(y1)), min(h, int(y2))
    if x2 - x1 < 4 or y2 - y1 < 2:
        return 0.0
    roi = cv2.resize(cinza[y1:y2, x1:x2], (48, 24)).astype(np.float32)
    roi = cv2.GaussianBlur(roi, (3, 3), 0)
    gx = cv2.Sobel(roi, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(roi, cv2.CV_32F, 0, 1, ksize=3)
    return float(np.mean(np.hypot(gx, gy)) / (roi.mean() + 1.0))


def _calcular_bordas_olhos(frame_bgr, landmarks) -> float:
    """
    Detecta armação de óculos (inclusive de grau, com lentes transparentes): a armação
    cria bordas fortes logo abaixo dos olhos e na ponte do nariz, regiões que em pele
    lisa têm poucas bordas. Retorna o maior valor entre as três regiões.
    """
    h, w, _ = frame_bgr.shape
    cinza = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    def px(i):
        return landmarks[i].x * w, landmarks[i].y * h

    olho_e, olho_d = px(33), px(263)
    d = np.hypot(olho_e[0] - olho_d[0], olho_e[1] - olho_d[1]) or 1.0

    # Faixa logo abaixo de cada olho (onde passa a borda inferior da armação)
    regioes = []
    for externo, interno, inferiores in ((33, 133, (145, 144, 153)), (263, 362, (374, 380, 373))):
        xe, xi = px(externo)[0], px(interno)[0]
        y_base = max(px(i)[1] for i in inferiores) + 0.04 * d
        regioes.append((min(xe, xi), y_base, max(xe, xi), y_base + 0.30 * d))

    # Ponte do nariz, entre os cantos internos dos olhos (onde fica a ponte da armação)
    xi_e, yi_e = px(133)
    xi_d, yi_d = px(362)
    y_ref = (yi_e + yi_d) / 2
    regioes.append((min(xi_e, xi_d), y_ref - 0.10 * d, max(xi_e, xi_d), y_ref + 0.20 * d))

    return max(_intensidade_bordas(cinza, *r) for r in regioes)


class DetectorFacial:
    def __init__(self, modelo_path: str = config.MODELO_FACE_LANDMARKER):
        if not os.path.exists(modelo_path):
            raise FileNotFoundError(
                f"Modelo '{modelo_path}' não encontrado. Baixe o face_landmarker.task "
                "do MediaPipe (link no config.py) e coloque no diretório do projeto."
            )
        base_options = mp_python.BaseOptions(model_asset_path=modelo_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=5,  # detecta vários rostos para escolher o mais próximo
            min_face_detection_confidence=0.8, # Aumentado de 0.5 para 0.8 para exigir rosto mais visível
            min_face_presence_confidence=0.8,
            min_tracking_confidence=0.5,
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detectar_rosto_mais_proximo(self, frame_bgr: np.ndarray) -> ResultadoRosto | None:
        """
        Roda a detecção no frame e retorna o rosto com maior bounding box
        (ou seja, o mais próximo da câmera). Retorna None se nenhum rosto for achado.
        """
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        resultado = self.detector.detect(mp_image)
        if not resultado.face_landmarks:
            return None

        melhor_rosto = None
        melhor_area = -1
        for landmarks in resultado.face_landmarks:
            xs = [lm.x for lm in landmarks]
            ys = [lm.y for lm in landmarks]
            x_min, x_max = min(xs) * w, max(xs) * w
            y_min, y_max = min(ys) * h, max(ys) * h
            area = (x_max - x_min) * (y_max - y_min)
            if area > melhor_area:
                melhor_area = area
                proporcao = (x_max - x_min) / w
                olho_e, olho_d = landmarks[33], landmarks[263]
                dist_olhos = np.hypot((olho_e.x - olho_d.x) * w, (olho_e.y - olho_d.y) * h) / w
                yaw, pitch = _calcular_pose(landmarks)
                melhor_rosto = ResultadoRosto(
                    landmarks=landmarks,
                    bbox=(int(x_min), int(y_min), int(x_max), int(y_max)),
                    proporcao_frame=proporcao,
                    proporcao_olhos=float(dist_olhos),
                    yaw=float(yaw),
                    pitch=float(pitch),
                )
        if melhor_rosto is not None:
            melhor_rosto.nitidez = _calcular_nitidez(frame_bgr, melhor_rosto.bbox)
            melhor_rosto.bordas_olhos = _calcular_bordas_olhos(frame_bgr, melhor_rosto.landmarks)
        return melhor_rosto

    def fechar(self):
        self.detector.close()


def avaliar_distancia(rosto: ResultadoRosto, modo: str = "destravamento") -> str:
    """
    Retorna 'longe', 'perto_demais' ou 'ok' com base na distância entre os olhos.
    modo: 'registro' (faixa estreita) ou 'destravamento' (faixa tolerante).
    """
    if modo == "registro":
        d_min, d_max = config.REGISTRO_DIST_OLHOS_MIN, config.REGISTRO_DIST_OLHOS_MAX
    else:
        d_min, d_max = config.DESTRAVAMENTO_DIST_OLHOS_MIN, config.DESTRAVAMENTO_DIST_OLHOS_MAX
    if rosto.proporcao_olhos < d_min:
        return "longe"
    if rosto.proporcao_olhos > d_max:
        return "perto_demais"
    return "ok"


def avaliar_qualidade(rosto: ResultadoRosto, modo: str = "destravamento") -> str:
    """
    Retorna 'ok' ou o motivo da rejeição: 'virado', 'inclinado' ou 'borrado'.
    Pose e nitidez impactam a consistência do embedding mais que a distância.
    """
    if modo == "registro":
        yaw_max, pitch_max, nit_min = (config.REGISTRO_YAW_MAX, config.REGISTRO_PITCH_MAX,
                                       config.REGISTRO_NITIDEZ_MIN)
    else:
        yaw_max, pitch_max, nit_min = (config.DESTRAVAMENTO_YAW_MAX, config.DESTRAVAMENTO_PITCH_MAX,
                                       config.DESTRAVAMENTO_NITIDEZ_MIN)
    if abs(rosto.yaw) > yaw_max:
        return "virado"
    if abs(rosto.pitch) > pitch_max:
        return "inclinado"
    if rosto.nitidez < nit_min:
        return "borrado"
    return "ok"


# Índices de landmarks do MediaPipe Face Mesh (478 pontos) usados na heurística.
# Referência: mapa oficial "Face Mesh Landmark Map" do MediaPipe.
_IDX_OLHO_ESQUERDO = [33, 133, 160, 159, 158, 157, 173]
_IDX_OLHO_DIREITO = [362, 263, 387, 386, 385, 384, 398]
_IDX_BOCA = [13, 14, 61, 291, 78, 308]


def detectar_acessorios(landmarks, bordas_olhos: float = 0.0) -> dict:
    """
    Heurística simples: usa a variação de posição (z) e presença consistente
    dos pontos-chave de olhos e boca como indício de oclusão.
    Óculos (inclusive de grau) são detectados pelas bordas da armação ao redor dos olhos.

    Isso é uma primeira aproximação (conforme documentado no Stack_Reconhecimento_Facial.md);
    para a versão final, considerar treinar um classificador leve caso sobre tempo.
    """
    def presenca_media(indices):
        # Quando há oclusão (óculos escuros, máscara), o MediaPipe ainda entrega uma
        # posição interpolada, mas a variância de profundidade (z) tende a cair
        # porque o modelo perde referência de textura real. Usamos isso como proxy.
        zs = [landmarks[i].z for i in indices]
        variancia = float(np.var(zs))
        # normalizando para uma pseudo-confiança entre 0 e 1 (calibrar empiricamente)
        confianca = min(1.0, variancia * 500)
        return confianca

    confianca_olhos = min(
        presenca_media(_IDX_OLHO_ESQUERDO), presenca_media(_IDX_OLHO_DIREITO)
    )
    confianca_boca = presenca_media(_IDX_BOCA)

    usa_oculos = bordas_olhos > config.BORDAS_MAX_OLHOS
    usa_mascara = confianca_boca < config.CONFIANCA_MIN_BOCA

    return {
        "oculos_detectado": usa_oculos,
        "mascara_detectada": usa_mascara,
        "confianca_olhos": confianca_olhos,
        "confianca_boca": confianca_boca,
        "bordas_olhos": bordas_olhos,
    }
