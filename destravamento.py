"""
destravamento.py

Fluxo de DESTRAVAMENTO DA CATRACA (item 2 do documento "Reconhecimento_Facial"):
  - detecta o rosto mais proximo da camera
  - gera o embedding e compara com os usuarios cadastrados
  - se bater com algum usuario (acima do limiar), aciona o servo motor
  - se a deteccao facial falhar continuamente, cai para o fallback RFID (RC522)

O acionamento real do servo motor e a leitura do RC522 estao isolados em
funcoes separadas (`abrir_catraca` / `ler_rfid`) para serem trocadas pela
implementacao real de GPIO quando o codigo for rodar no Raspberry Pi.
"""

import time
import cv2

import config
from face_utils import DetectorFacial, avaliar_distancia
from embedding import ExtratorPlaceholder
from database import BancoUsuarios

# Numero de frames seguidos sem rosto valido antes de oferecer o fallback RFID
FRAMES_FALHA_ANTES_DO_RFID = 60  # ~ alguns segundos, depende do FPS da webcam


def abrir_catraca(usuario: str = None, via: str = "facial"):
    """
    Placeholder para o acionamento do servo motor.
    No Raspberry Pi real, aqui entraria algo como:

        from gpiozero import Servo
        servo = Servo(17)
        servo.max()
        time.sleep(2)
        servo.min()
    """
    quem = usuario or "usuario RFID"
    print(f"[CATRACA] Acesso liberado para '{quem}' via {via}. Acionando servo motor...")


def ler_rfid():
    """
    Placeholder para a leitura do modulo RC522.
    No Raspberry Pi real, aqui entraria a biblioteca mfrc522, ex:

        from mfrc522 import SimpleMFRC522
        leitor = SimpleMFRC522()
        id_tag, texto = leitor.read()
        return id_tag
    """
    print("[RFID] Aguardando aproximacao do cartao/celular (simulado)...")
    return None  # substituir pela leitura real


def rodar_catraca():
    detector = DetectorFacial()
    extrator = ExtratorPlaceholder()  # trocar por ExtratorTFLite quando o modelo estiver pronto
    banco = BancoUsuarios()

    if not banco.usuarios_cadastrados():
        print("[AVISO] Nenhum usuario cadastrado ainda. Rode registro.py primeiro.")

    import os
    if os.name == 'nt':
        cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduz o lag (evita acumular frames antigos na fila)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    print("[CATRACA] Sistema ativo. Pressione 'q' para encerrar.")
    frames_sem_rosto_valido = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Falha ao ler a camera.")
                break

            rosto = detector.detectar_rosto_mais_proximo(frame)
            mensagem = ""

            if rosto is None:
                frames_sem_rosto_valido += 1
                mensagem = "Aproxime o rosto da catraca."
            else:
                distancia = avaliar_distancia(rosto)
                if distancia != "ok":
                    frames_sem_rosto_valido += 1
                    mensagem = "Ajuste a distancia do rosto."
                else:
                    embedding = extrator.extrair(frame, rosto.bbox, rosto.landmarks)
                    nome, similaridade = banco.buscar_mais_proximo(embedding)

                    if nome is not None and similaridade >= config.LIMIAR_SIMILARIDADE:
                        abrir_catraca(usuario=nome, via="facial")
                        frames_sem_rosto_valido = 0
                        
                        # Em vez de pausar o vídeo por 1.5s (o que causa o congelamento),
                        # mostramos a mensagem na tela por 45 frames (aprox 1.5s) sem travar a câmera
                        for _ in range(45):
                            ok, f = cap.read()
                            if not ok: break
                            cv2.putText(f, f"Bem-vindo, {nome}!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            cv2.imshow("Catraca - Prototipo", f)
                            cv2.waitKey(1)
                            
                        # Limpa o buffer acumulado para a câmera voltar ao tempo real
                        for _ in range(5): cap.read()
                        continue
                    else:
                        frames_sem_rosto_valido += 1
                        mensagem = f"Rosto nao reconhecido (similaridade {similaridade:.2f})."

            # fallback para RFID apos varias falhas seguidas de reconhecimento facial
            if frames_sem_rosto_valido >= FRAMES_FALHA_ANTES_DO_RFID:
                mensagem = "Reconhecimento facial falhou. Aproxime o RFID/celular."
                
                if rosto is not None:
                    x1, y1, x2, y2 = rosto.bbox
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, mensagem, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 0, 255), 2)
                cv2.imshow("Catraca - Prototipo", frame)
                cv2.waitKey(1)
                
                tag = ler_rfid()
                if tag is not None:
                    abrir_catraca(via="rfid")
                frames_sem_rosto_valido = 0

            if rosto is not None:
                x1, y1, x2, y2 = rosto.bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, mensagem, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
            cv2.imshow("Catraca - Prototipo", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.fechar()


if __name__ == "__main__":
    rodar_catraca()
