"""
registro.py

Fluxo de REGISTRO facial (item 1 do documento "Reconhecimento_Facial"):
  - detecta baixa confiança em óculos/máscara/chapéu e instrui o usuário a remover
  - só salva o embedding quando o rosto está sem oclusões e a uma distância adequada

No sistema final este fluxo roda no APP (celular). Aqui está implementado em
Python/webcam apenas para permitir testar e demonstrar a lógica no protótipo
do Raspberry Pi / notebook, já que o app mobile é outra frente do trabalho.
"""

import numpy as np
import cv2

import config
from face_utils import DetectorFacial, avaliar_distancia, avaliar_qualidade, detectar_acessorios
from embedding import ExtratorPlaceholder, ExtratorTFLite, similaridade_cosseno
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

    capturando = False
    embeddings = []
    frames_desde_captura = config.REGISTRO_INTERVALO_FRAMES

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
                distancia = avaliar_distancia(rosto, modo="registro")
                qualidade = avaliar_qualidade(rosto, modo="registro")
                acessorios = detectar_acessorios(rosto.landmarks, rosto.bordas_olhos)

                if distancia == "longe":
                    mensagem = "Aproxime-se um pouco mais."
                elif distancia == "perto_demais":
                    mensagem = "Afaste-se um pouco."
                elif qualidade == "virado":
                    mensagem = "Olhe de frente para a camera (sem virar o rosto)."
                elif qualidade == "inclinado":
                    mensagem = "Mantenha a cabeca reta (nao incline para cima/baixo)."
                elif qualidade == "borrado":
                    mensagem = "Imagem borrada. Fique parado / melhore a iluminacao."
                elif acessorios["oculos_detectado"]:
                    mensagem = "Remova os oculos/oculos escuros."
                elif acessorios["mascara_detectada"]:
                    mensagem = "Remova a mascara."
                else:
                    mensagem = "Rosto OK! Pressione 'c' para cadastrar."
                    pode_cadastrar = True

                x1, y1, x2, y2 = rosto.bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0) if pode_cadastrar else (0, 0, 255), 2)

                # Mostra os valores na tela para ajudar a calibrar o config.py
                debug_txt = (f"Bordas olhos: {rosto.bordas_olhos:.3f} (Limite: {config.BORDAS_MAX_OLHOS}) | "
                             f"Boca: {acessorios['confianca_boca']:.4f}")
                cv2.putText(frame, debug_txt, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                debug2 = (f"Dist.olhos: {rosto.proporcao_olhos:.3f} | yaw: {rosto.yaw:+.2f} | "
                          f"pitch: {rosto.pitch:+.2f} | nitidez: {rosto.nitidez:.0f}")
                cv2.putText(frame, debug2, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            # --- Captura múltipla: só acumula frames que passam em TODOS os critérios ---
            if capturando:
                if pode_cadastrar:
                    frames_desde_captura += 1
                    if frames_desde_captura >= config.REGISTRO_INTERVALO_FRAMES:
                        embeddings.append(extrator.extrair(frame, rosto.bbox, rosto.landmarks))
                        frames_desde_captura = 0
                    mensagem = f"Capturando... {len(embeddings)}/{config.REGISTRO_NUM_CAPTURAS}"
                else:
                    mensagem = f"Captura pausada ({len(embeddings)}/{config.REGISTRO_NUM_CAPTURAS}): {mensagem}"

            cv2.putText(frame, mensagem, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0) if pode_cadastrar else (0, 0, 255), 2)
            cv2.imshow("Registro Facial - Prototipo", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[REGISTRO] Cancelado pelo usuario.")
                break
            elif key == ord("c") and pode_cadastrar and not capturando:
                capturando = True
                embeddings = []
                frames_desde_captura = config.REGISTRO_INTERVALO_FRAMES

            if capturando and len(embeddings) >= config.REGISTRO_NUM_CAPTURAS:
                # Descarta capturas discrepantes (outliers) em relação à média preliminar
                media = np.mean(embeddings, axis=0)
                consistentes = [e for e in embeddings
                                if similaridade_cosseno(e, media) >= config.REGISTRO_SIM_MIN_ENTRE_CAPTURAS]
                if len(consistentes) < 3:
                    print("[REGISTRO] Capturas inconsistentes entre si. Tente novamente com boa iluminacao e rosto parado.")
                    break

                embedding = np.mean(consistentes, axis=0)
                embedding = embedding / np.linalg.norm(embedding)
                print(f"[REGISTRO] {len(consistentes)}/{len(embeddings)} capturas consistentes usadas na media.")

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
