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
    def __init__(self, landmarks, bbox, proporcao_frame):
        self.landmarks = landmarks              # lista de landmarks (x, y, z) normalizados
        self.bbox = bbox                         # (x_min, y_min, x_max, y_max) em pixels
        self.proporcao_frame = proporcao_frame   # largura do rosto / largura do frame


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
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
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
                melhor_rosto = ResultadoRosto(
                    landmarks=landmarks,
                    bbox=(int(x_min), int(y_min), int(x_max), int(y_max)),
                    proporcao_frame=proporcao,
                )
        return melhor_rosto

    def fechar(self):
        self.detector.close()


def avaliar_distancia(rosto: ResultadoRosto) -> str:
    """Retorna 'longe', 'perto_demais' ou 'ok' com base na heurística de proporção."""
    if rosto.proporcao_frame < config.DISTANCIA_MIN_PROPORCAO:
        return "longe"
    if rosto.proporcao_frame > config.DISTANCIA_MAX_PROPORCAO:
        return "perto_demais"
    return "ok"


# Índices de landmarks do MediaPipe Face Mesh (478 pontos) usados na heurística.
# Referência: mapa oficial "Face Mesh Landmark Map" do MediaPipe.
_IDX_OLHO_ESQUERDO = [33, 133, 160, 159, 158, 157, 173]
_IDX_OLHO_DIREITO = [362, 263, 387, 386, 385, 384, 398]
_IDX_BOCA = [13, 14, 61, 291, 78, 308]


def detectar_acessorios(landmarks) -> dict:
    """
    Heurística simples: usa a variação de posição (z) e presença consistente
    dos pontos-chave de olhos e boca como indício de oclusão.

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

    usa_oculos = confianca_olhos < config.CONFIANCA_MIN_OLHOS
    usa_mascara = confianca_boca < config.CONFIANCA_MIN_BOCA

    return {
        "oculos_detectado": usa_oculos,
        "mascara_detectada": usa_mascara,
        "confianca_olhos": confianca_olhos,
        "confianca_boca": confianca_boca,
    }
