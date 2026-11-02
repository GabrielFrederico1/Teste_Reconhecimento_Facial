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
| `config.py` | Limiares e caminhos centralizados (já calibrados com a webcam do desenvolvedor; recalibrar no hardware final) |
| `face_utils.py` | Wrapper do MediaPipe: rosto mais próximo, distância (entre olhos), pose (yaw/pitch), nitidez e heurísticas de acessórios (óculos por bordas, máscara por variância de z) |
| `embedding.py` | `ExtratorTFLite` (MobileFaceNet `mobilefacenet.tflite`, **em uso** em registro e destravamento) + `ExtratorPlaceholder` (geométrico, só para testes) |
| `database.py` | Banco local em JSON com matching por similaridade de cosseno (protótipo — produção usaria backend). CLI: `listar`, `remover`, `limpar` |
| `registro.py` | Cadastro via webcam: valida qualidade e salva a **média de 5 capturas** |
| `destravamento.py` | Catraca: valida distância/pose/nitidez → embedding → matching → aciona servo (placeholder) → fallback RFID/Arduino após falhas repetidas |
| `requirements.txt` | Dependências e passo a passo dos comandos de execução (em comentários) |

`ExtratorPlaceholder` não tem poder real de discriminação facial e **não deve ir
para a entrega final**; os fluxos já usam o `ExtratorTFLite`.

## Critérios de qualidade do rosto (consistência do embedding)

Distância, pose e nitidez alteram o embedding, por isso são exigidas **antes** de
gerar/comparar embeddings:

- **Distância**: medida pela distância entre os cantos externos dos olhos
  (landmarks 33 e 263) como fração da largura do frame — mais estável que a
  bounding box. Faixas separadas: `REGISTRO_DIST_OLHOS_*` (estreita) e
  `DESTRAVAMENTO_DIST_OLHOS_*` (um pouco mais folgada). Ambos os fluxos aplicam
  mínimo e máximo.
- **Pose**: `yaw` e `pitch` (0 = frontal), com `PITCH_CENTRO` calibrado;
  limites `*_YAW_MAX` / `*_PITCH_MAX` por fluxo.
- **Nitidez**: variância do Laplaciano do recorte 112x112 (`*_NITIDEZ_MIN`).
- **Registro com múltiplas capturas**: `REGISTRO_NUM_CAPTURAS` frames válidos,
  espaçados por `REGISTRO_INTERVALO_FRAMES`; capturas com similaridade à média
  abaixo de `REGISTRO_SIM_MIN_ENTRE_CAPTURAS` são descartadas (mín. 3 restantes);
  salva-se a média normalizada.
- Fluxo de acessórios é checado **só no registro**.

## Detecção de acessórios (lições aprendidas)

- **Óculos (inclusive de grau)**: intensidade de bordas da armação sob os olhos e
  na ponte do nariz (`bordas_olhos` > `BORDAS_MAX_OLHOS`). Medições do usuário:
  sem óculos ≈ 0.20, com óculos de grau ≈ 0.50 → limiar 0.35.
- A antiga heurística por variância de `z` nos olhos foi **abandonada** para
  óculos: depende de distância/pose e não separava os casos
  (`CONFIANCA_MIN_OLHOS` é legado, só exibido/retornado).
- **Máscara**: ainda usa variância de `z` da boca (`CONFIANCA_MIN_BOCA`).
  Medições: sem máscara (com barba) ≈ 0.045, com máscara ≈ 0.025 → limiar 0.035.
  É frágil; se falhar com distância/pose/barba, trocar por critério de cor/textura
  da região boca/nariz vs. bochechas.
- A tela do registro exibe `Bordas olhos`, `Boca`, `Dist.olhos`, `yaw`, `pitch`
  e `nitidez` para facilitar a calibração.

Interações de hardware (`abrir_catraca`, `ler_rfid` em `destravamento.py`)
são placeholders documentados com comentários indicando exatamente qual
biblioteca real usar (`gpiozero`/`RPi.GPIO` e `mfrc522`), pois o
desenvolvimento foi feito sem Raspberry Pi físico disponível. A comunicação com o
Arduino (display/RFID) é via serial (`PORTA_ARDUINO`, `None` desativa).

## Como executar

Ver `requirements.txt` (comandos de instalação, cadastro, catraca e gestão do banco).
Resumo: `python registro.py "nome"` e `python destravamento.py`.

## Próximos passos pendentes (nesta ordem de prioridade)

1. Validar o embedding do app mobile com o mesmo `mobilefacenet.tflite` usado aqui.
2. Calibrar `LIMIAR_SIMILARIDADE`, faixas de distância, pose, nitidez e limiares de
   acessórios na distância de instalação real da catraca (e com a câmera final).
3. Substituir os placeholders de hardware pelas chamadas reais de GPIO
   (servo motor) e leitura do RC522 (RFID).
4. Conectar as mensagens de status ao display de LED via PCF8574T.
5. (Opcional, se sobrar tempo) treinar um classificador leve (MobileNetV2)
   para detecção de acessórios em vez das heurísticas atuais.

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
