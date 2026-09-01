# Contexto do Projeto — Catraca com Reconhecimento Facial

> Este arquivo existe para dar contexto rápido a qualquer agente de IA (ex: os
> agentes do Google Antigravity) que for ajudar a evoluir este código. Leia
> isto antes de sugerir mudanças de arquitetura.

## O que é o projeto

Trabalho da disciplina de **Sistemas Embarcados** (faculdade) — **não é TCC**.
Objetivo: construir um totem/catraca de acesso com reconhecimento facial,
usando Raspberry Pi 5 como sistema central.

## Arquitetura geral (visão de produto)

1. Usuário se cadastra pelo **aplicativo de celular** (fora do escopo deste
   repositório) — lá ele registra o rosto e opcionalmente associa um cartão RFID.
2. O **Raspberry Pi** roda o destravamento: webcam capta o rosto, gera um
   embedding e compara com os cadastrados. Se bater, aciona o servo motor
   que simula a abertura da porta.
3. Se o reconhecimento facial falhar repetidamente, cai para leitura de
   **RFID (RC522)** como fallback.
4. Um **display de LED (via PCF8574T)** mostra mensagens de status ao usuário.

## Restrição arquitetural mais importante

O app (celular) e o Raspberry Pi **precisam gerar embeddings comparáveis**,
ou seja, **o mesmo modelo (arquitetura + pesos)** precisa rodar dos dois
lados, em formato cross-platform (TFLite ou ONNX). Isso está detalhado em
`Stack_Reconhecimento_Facial.md` (documento de decisão, não é código).

Modelos escolhidos para o embedding: **MobileFaceNet (TFLite)** ou
**InsightFace buffalo_s (ONNX)** — qualquer sugestão de trocar o modelo de
embedding só faz sentido se o mesmo modelo puder rodar no app mobile também.

Para detecção de rosto + landmarks + heurísticas (distância, acessórios),
usamos **MediaPipe Face Landmarker**, pois roda nativamente em Android/iOS e
em Python (Pi) sem reconversão.

## Estado atual do código (pasta `reconhecimento_facial/`)

Este é um **protótipo validador de pipeline**, não a entrega final. Arquivos:

| Arquivo | Papel |
|---|---|
| `config.py` | Limiares e caminhos centralizados (a calibrar com hardware real) |
| `face_utils.py` | Wrapper do MediaPipe: rosto mais próximo, heurística de distância e de acessórios (óculos/máscara) |
| `embedding.py` | `ExtratorPlaceholder` (geométrico, só para testar o pipeline) + `ExtratorTFLite` (ponto de integração do modelo real, ainda não plugado) |
| `database.py` | Banco local em JSON com matching por similaridade de cosseno (protótipo — produção usaria backend) |
| `registro.py` | Fluxo de cadastro via webcam (equivalente ao que o app mobile faria) |
| `destravamento.py` | Fluxo da catraca: reconhecimento facial → aciona servo (placeholder) → fallback RFID (placeholder) após falhas repetidas |

**Importante:** `ExtratorPlaceholder` em `embedding.py` é determinístico mas
**não tem poder real de discriminação facial**. Ele existe só para validar
que registro → banco → matching → destravamento funcionam de ponta a ponta.
**Não deve ir para a entrega final do trabalho.**

Interações de hardware (`abrir_catraca`, `ler_rfid` em `destravamento.py`)
são placeholders documentados com comentários indicando exatamente qual
biblioteca real usar (`gpiozero`/`RPi.GPIO` e `mfrc522`), pois o
desenvolvimento foi feito sem Raspberry Pi físico disponível.

## Próximos passos pendentes (nesta ordem de prioridade)

1. Baixar pesos reais do MobileFaceNet (`.tflite`) ou InsightFace buffalo_s
   (`.onnx`) e plugar em `ExtratorTFLite`; usar o mesmo modelo no app mobile.
2. Calibrar `LIMIAR_SIMILARIDADE` e as proporções de distância em `config.py`
   com testes reais na distância de instalação da catraca.
3. Substituir os placeholders de hardware pelas chamadas reais de GPIO
   (servo motor) e leitura do RC522 (RFID).
4. Conectar as mensagens de status ao display de LED via PCF8574T.
5. (Opcional, se sobrar tempo) treinar um classificador leve (MobileNetV2)
   para detecção de acessórios em vez da heurística de variância atual.

## Convenções e decisões já tomadas (não reabrir sem motivo forte)

- Terminologia: sempre "trabalho da disciplina", nunca "TCC".
- Comentários e nomes de variáveis em português, consistente com o resto
  da documentação do projeto (`Fluxo_de_funcionamento`, `Componentes`, etc.).
- Banco de dados do protótipo é JSON local por simplicidade — não sugerir
  migração para um banco relacional a menos que o usuário peça, já que foge
  do escopo de um protótipo de disciplina.
- Câmera é acessada via OpenCV (`cv2.VideoCapture`) diretamente pela webcam
  local durante o desenvolvimento; no Pi final, o mesmo código deve
  funcionar trocando `CAMERA_INDEX` em `config.py`.

## O que evitar

- Não sugerir usar `face_recognition`/`dlib` para o embedding final — o
  encoding de 128d do dlib não é compatível com o que o app mobile vai gerar
  (MobileFaceNet/InsightFace). Isso quebraria a restrição arquitetural central.
- Não remover os comentários que documentam onde entra o hardware real
  (servo, RFID) — eles são parte da documentação do trabalho para a banca.
