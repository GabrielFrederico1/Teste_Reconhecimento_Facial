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

import config
from face_utils import DetectorFacial, avaliar_distancia, detectar_acessorios
from embedding import ExtratorPlaceholder, ExtratorTFLite
from database import BancoUsuarios


def registrar_usuario(nome_usuario: str):
    detector = DetectorFacial()
    extrator = ExtratorTFLite("mobilefacenet.tflite")
    banco = BancoUsuarios()

    import os
    if os.name == 'nt':
        cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduz o lag (evita acumular frames antigos na fila)
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
            pode_cadastrar = False

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
                    mensagem = "Remova os oculos/oculos escuros."
                elif acessorios["mascara_detectada"]:
                    mensagem = "Remova a mascara."
                else:
                    mensagem = "Rosto OK! Pressione 'c' para cadastrar."
                    pode_cadastrar = True

                x1, y1, x2, y2 = rosto.bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0) if pode_cadastrar else (0, 0, 255), 2)
                
                # Mostra o valor na tela para ajudar a calibrar o config.py
                debug_txt = f"Confianca Olhos: {acessorios['confianca_olhos']:.4f} (Limiar: {config.CONFIANCA_MIN_OLHOS})"
                cv2.putText(frame, debug_txt, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            cv2.putText(frame, mensagem, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0) if pode_cadastrar else (0, 0, 255), 2)
            cv2.imshow("Registro Facial - Prototipo", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[REGISTRO] Cancelado pelo usuario.")
                break
            elif key == ord("c") and pode_cadastrar:
                embedding = extrator.extrair(frame, rosto.bbox, rosto.landmarks)
                nome_existente, similaridade = banco.buscar_mais_proximo(embedding)
                
                if nome_existente is not None and similaridade >= config.LIMIAR_SIMILARIDADE:
                    print(f"[REGISTRO] Erro: Esse rosto já pertence ao usuário '{nome_existente}'.")
                    break
                
                banco.cadastrar(nome_usuario, embedding)
                print(f"[REGISTRO] Usuario '{nome_usuario}' cadastrado com sucesso.")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.fechar()


if __name__ == "__main__":
    import sys
    nome = sys.argv[1] if len(sys.argv) > 1 else input("Nome do usuario a cadastrar: ")
    registrar_usuario(nome)
