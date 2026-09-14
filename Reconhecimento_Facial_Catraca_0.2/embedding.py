"""
embedding.py

Responsável por gerar o vetor (embedding) que representa o rosto, usado no matching.

IMPORTANTE (ver Stack_Reconhecimento_Facial.md):
O app (celular) e o Raspberry Pi PRECISAM usar exatamente o mesmo modelo/pesos
para que os embeddings sejam comparáveis. A stack recomendada é:
  - MobileFaceNet (TFLite), ou
  - InsightFace buffalo_s (ONNX)

Este arquivo já está estruturado para plugar o modelo real via `ExtratorTFLite`.
Enquanto o .tflite/.onnx do modelo final não é integrado, existe um
`ExtratorPlaceholder` que gera um vetor determinístico a partir dos landmarks,
só para permitir testar TODO o fluxo (registro -> banco -> matching -> destravar)
de ponta a ponta antes de acoplar o modelo definitivo.

!!! NÃO usar o placeholder para a entrega final do trabalho — ele não tem
poder de discriminação facial real, serve só para validar o pipeline. !!!
"""

from abc import ABC, abstractmethod
import numpy as np


class ExtratorEmbedding(ABC):
    @abstractmethod
    def extrair(self, frame_bgr: np.ndarray, bbox: tuple, landmarks) -> np.ndarray:
        """Recebe o frame, a bbox do rosto e os landmarks; retorna um vetor 1D normalizado."""
        raise NotImplementedError


class ExtratorPlaceholder(ExtratorEmbedding):
    """
    Gera um embedding a partir da geometria relativa dos landmarks (distâncias
    normalizadas entre pontos-chave). Não é robusto a variações reais de
    iluminação/pose, mas é 100% determinístico e serve para testar o pipeline
    sem depender de um arquivo de modelo externo.
    """

    def extrair(self, frame_bgr, bbox, landmarks) -> np.ndarray:
        pontos = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
        centro = pontos.mean(axis=0)
        vetor = (pontos - centro).flatten()
        # reduz para um vetor de tamanho fixo (128) via amostragem, só para o placeholder
        passo = max(1, len(vetor) // 128)
        vetor = vetor[::passo][:128]
        if len(vetor) < 128:
            vetor = np.pad(vetor, (0, 128 - len(vetor)))
        norma = np.linalg.norm(vetor)
        return vetor / norma if norma > 0 else vetor


class ExtratorTFLite(ExtratorEmbedding):
    """
    Ponto de integração do modelo real (MobileFaceNet .tflite).

    Uso após baixar o modelo (ex: mobilefacenet.tflite) e colocar no projeto:
        extrator = ExtratorTFLite("mobilefacenet.tflite")

    Requer: pip install tflite-runtime  (ou tensorflow, no Pi geralmente tflite-runtime)
    """

    def __init__(self, modelo_path: str, tamanho_entrada: int = 112):
        Interpreter = self._importar_interpreter()
        self.tamanho_entrada = tamanho_entrada
        self.interpreter = Interpreter(model_path=modelo_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    @staticmethod
    def _importar_interpreter():
        """
        Tenta, nesta ordem: tflite_runtime (comum no Raspberry Pi),
        ai_edge_litert (pacote atual do Google, usado nos testes de
        desenvolvimento) e por fim tensorflow.lite (fallback pesado).
        """
        try:
            from tflite_runtime.interpreter import Interpreter
            return Interpreter
        except ImportError:
            pass
        try:
            from ai_edge_litert.interpreter import Interpreter
            return Interpreter
        except ImportError:
            pass
        from tensorflow.lite import Interpreter
        return Interpreter

    def extrair(self, frame_bgr, bbox, landmarks) -> np.ndarray:
        import cv2

        x_min, y_min, x_max, y_max = bbox
        rosto = frame_bgr[max(0, y_min):y_max, max(0, x_min):x_max]
        rosto = cv2.resize(rosto, (self.tamanho_entrada, self.tamanho_entrada))
        rosto = cv2.cvtColor(rosto, cv2.COLOR_BGR2RGB).astype(np.float32)
        rosto = (rosto - 127.5) / 128.0  # normalização padrão do MobileFaceNet
        entrada = np.expand_dims(rosto, axis=0)

        self.interpreter.set_tensor(self.input_details[0]["index"], entrada)
        self.interpreter.invoke()
        saida = self.interpreter.get_tensor(self.output_details[0]["index"])[0]

        norma = np.linalg.norm(saida)
        return saida / norma if norma > 0 else saida


def similaridade_cosseno(v1: np.ndarray, v2: np.ndarray) -> float:
    v1, v2 = np.asarray(v1), np.asarray(v2)
    denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)
