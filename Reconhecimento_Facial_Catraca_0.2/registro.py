"""
registro.py

Fluxo de REGISTRO facial (item 1 do documento "Reconhecimento_Facial"):
  - detecta baixa confiança em óculos/máscara/chapéu e instrui o usuário a remover
  - só salva o embedding quando o rosto está sem oclusões e a uma distância adequada

No sistema final este fluxo roda no APP (celular). Aqui está implementado em
Python/webcam apenas para permitir testar e demonstrar a lógica no protótipo
do Raspberry Pi / notebook, já que o app mobile é outra frente do trabalho.
"""

import cv2

import os

import config
from face_utils import DetectorFacial, avaliar_distancia, detectar_acessorios
from embedding import ExtratorPlaceholder, ExtratorTFLite
from database import BancoUsuarios


def _criar_extrator():
    """Usa o modelo real (MobileFaceNet) se o arquivo existir; senao cai no placeholder."""
    if os.path.exists(config.MODELO_EMBEDDING):
        print(f"[INFO] Usando modelo de embedding real: {config.MODELO_EMBEDDING}")
        return ExtratorTFLite(config.MODELO_EMBEDDING)
    print(
        f"[AVISO] Modelo '{config.MODELO_EMBEDDING}' nao encontrado. "
        "Usando ExtratorPlaceholder (NAO usar para a entrega final)."
    )
    return ExtratorPlaceholder()


def registrar_usuario(nome_usuario: str):
    detector = DetectorFacial()
    extrator = _criar_extrator()
    banco = BancoUsuarios()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    print(f"[REGISTRO] Iniciando cadastro de '{nome_usuario}'. Pressione 'q' para cancelar.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Falha ao ler a câmera.")
                break

            rosto = detector.detectar_rosto_mais_proximo(frame)
            mensagem = ""

            if rosto is None:
                mensagem = "Nenhum rosto detectado. Aproxime-se da câmera."
            else:
                distancia = avaliar_distancia(rosto)
                acessorios = detectar_acessorios(rosto.landmarks)

                if distancia == "longe":
                    mensagem = "Aproxime-se um pouco mais."
                elif distancia == "perto_demais":
                    mensagem = "Afaste-se um pouco."
                elif acessorios["oculos_detectado"]:
                    mensagem = "Remova os oculos/oculos escuros para continuar."
                elif acessorios["mascara_detectada"]:
                    mensagem = "Remova a mascara para continuar."
                else:
                    mensagem = "OK! Capturando embedding..."
                    embedding = extrator.extrair(frame, rosto.bbox, rosto.landmarks)
                    banco.cadastrar(nome_usuario, embedding)
                    print(f"[REGISTRO] Usuario '{nome_usuario}' cadastrado com sucesso.")
                    break

            # feedback visual (equivalente ao display de LED no totem real)
            if rosto is not None:
                x1, y1, x2, y2 = rosto.bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, mensagem, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2)
            cv2.imshow("Registro Facial - Prototipo", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[REGISTRO] Cancelado pelo usuario.")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.fechar()


if __name__ == "__main__":
    import sys
    nome = sys.argv[1] if len(sys.argv) > 1 else input("Nome do usuario a cadastrar: ")
    registrar_usuario(nome)
