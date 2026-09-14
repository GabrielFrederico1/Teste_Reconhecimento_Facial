# CONTEXTO.md — Catraca/Totem com Reconhecimento Facial

> Arquivo de contexto geral do projeto, para uso por agentes de IA (ex:
> Antigravity) ou por qualquer pessoa que precise entender rapidamente o
> projeto sem reler tudo do zero. Leia antes de sugerir mudanças de
> arquitetura ou decisões já tomadas.

## O que é o projeto

Trabalho da disciplina de **Sistemas Embarcados** (faculdade) — **não é TCC**.
Um totem/catraca de controle de acesso com reconhecimento facial, RFID como
fallback, motor de servo para abertura da porta e display de LED para
mensagens. Sistema central: **Raspberry Pi 5**.

## Fluxo de funcionamento (produto)

1. Usuário faz login no aplicativo de celular.
2. No app, registra o rosto e, opcionalmente, recebe a opção de associar um
   cartão/aproximação RFID.
3. Na catraca (Raspberry Pi), o usuário escolhe entre reconhecimento facial
   ou RFID.
4. Ao ser reconhecido por qualquer um dos dois métodos, o servo motor abre
   a porta (simulação de destravamento).

## Componentes de hardware

- Raspberry Pi 5 — sistema central
- Webcam — reconhecimento facial
- Servo motor — simula abertura da porta
- Display de LED (controlado via **PCF8574T**) — mensagens ao usuário
- Sensor RFID **RC522** — fallback caso a detecção facial falhe
- Iluminação do totem
- Totem impresso em filamento (estrutura física, impressão 3D)

## Reconhecimento facial — dois momentos distintos

1. **Registro** (feito no app mobile): o algoritmo detecta uso de acessórios
   (óculos, máscara, chapéu) e instrui o usuário a removê-los antes de
   prosseguir; só então salva o embedding.
2. **Destravamento da catraca** (feito no Pi via webcam): detecta o rosto
   mais próximo da câmera e destrava se o embedding bater com algum usuário
   cadastrado no sistema.

## Restrição arquitetural mais importante

O registro do usuário acontece no **app** e o desbloqueio no **Raspberry
Pi** — para que os embeddings gerados nos dois lados sejam comparáveis, é
obrigatório usar **exatamente o mesmo modelo (arquitetura + pesos)** nas
duas pontas, em formato cross-platform (TFLite ou ONNX). Essa é a decisão
arquitetural central do projeto e qualquer sugestão que a quebre deve ser
descartada.

## Stack de reconhecimento facial (decidida)

| Função | Ferramenta | App | Pi |
|---|---|---|---|
| Detecção + landmarks + distância + acessórios (heurística) | **MediaPipe Face Landmarker** (Face Mesh) | ✅ Android/iOS via MediaPipe Tasks API | ✅ Python |
| Embedding para matching | **MobileFaceNet (TFLite)** ou **InsightFace buffalo_s (ONNX)** | ✅ | ✅ |
| Matching | Similaridade de cosseno contra banco local em JSON | — | ✅ (protótipo) |

- **MediaPipe Face Landmarker**: mesmo modelo roda nativamente em
  Android/iOS e em Python no Pi, sem reconversão. 478 landmarks + bounding
  box. Distância estimada pela proporção da bounding box (ou distância
  interocular) em relação ao frame. Acessórios detectados via heurística de
  confiança/variância dos landmarks de olhos e boca.
- **MobileFaceNet (TFLite)**: leve (~4MB), boa opção padrão para protótipo.
- **InsightFace buffalo_s (ONNX)**: alternativa mais robusta, se a banca
  exigir métricas de acurácia mais rigorosas.
- **dlib/`face_recognition` foram descartados** — o encoding de 128d do
  dlib não é compatível com o que o app mobile geraria com
  MobileFaceNet/InsightFace, quebrando a restrição de cross-platform.

**Por que gerar o embedding on-device (não enviar a imagem):** privacidade
(só o vetor sai do celular, não a imagem — mais fácil de justificar em
termos de LGPD), economia de banda (vetor de 128–512 floats vs. foto/vídeo)
e escalabilidade do backend (só compara vetores, não roda detecção +
extração a cada requisição). Exemplos de mercado: Face ID da Apple roda
100% on-device.

**Trade-off documentado:** modelos mobile leves (MobileFaceNet) são um
pouco menos precisos que modelos maiores (ResNet-based), mas rodam bem
tanto no celular quanto no Pi 5 — equilíbrio aceitável para protótipo
acadêmico.

## Ambiente de desenvolvimento

**Google Antigravity** — IDE agêntica baseada em VS Code, roda com Gemini
3 Pro, lançada em preview gratuito em novembro de 2025. Login com conta
Google pessoal (Workspace ainda não suportado no preview).

## Estado atual do código (pasta `reconhecimento_facial/`)

Protótipo **funcional de validação de pipeline**, ainda não a entrega
final. Módulos:

| Arquivo | Papel |
|---|---|
| `config.py` | Limiares e caminhos centralizados (a calibrar com hardware real) |
| `face_utils.py` | Wrapper do MediaPipe: rosto mais próximo, heurística de distância e de acessórios (óculos/máscara) |
| `embedding.py` | `ExtratorPlaceholder` (geométrico, só para testar o pipeline) + `ExtratorTFLite` (ponto de integração do modelo real, ainda não plugado) |
| `database.py` | Banco local em JSON com matching por similaridade de cosseno (protótipo — produção usaria backend) |
| `registro.py` | Fluxo de cadastro via webcam (simula o que o app mobile faria) |
| `destravamento.py` | Fluxo da catraca: reconhecimento facial → aciona servo (placeholder) → fallback RFID (placeholder) após falhas repetidas |

**Atualização:** o modelo real (`ExtratorTFLite` + `mobilefacenet.tflite`)
**já está integrado e validado** — entrada 112x112x3 float32, saída 192-d
já normalizada, forward pass testado com sucesso. Fonte do arquivo:
github.com/MCarlomagno/FaceRecognitionAuth (conversão comunitária a partir
dos pesos do InsightFace/MobileFaceNet — citar essa fonte no relatório).
`registro.py`/`destravamento.py` usam esse modelo automaticamente quando o
arquivo `.tflite` está presente na pasta.

`ExtratorPlaceholder` em `embedding.py` continua existindo só como fallback
de teste (caso o `.tflite` não esteja disponível) — é determinístico
(geométrico, a partir dos landmarks) mas **não tem poder real de
discriminação facial** e **não deve ir para a entrega final do trabalho**.

Interações de hardware (`abrir_catraca`, `ler_rfid` em `destravamento.py`)
são placeholders documentados com comentários indicando exatamente qual
biblioteca real usar (`gpiozero`/`RPi.GPIO` e `mfrc522`), já que o
desenvolvimento foi feito sem Raspberry Pi físico disponível no momento.

## Próximos passos pendentes (ordem de prioridade)

1. ~~Baixar pesos reais do MobileFaceNet e plugar em `ExtratorTFLite`~~ —
   **feito**. Falta usar o mesmo modelo no app mobile e citar a fonte do
   `.tflite` no relatório do trabalho.
2. Calibrar `LIMIAR_SIMILARIDADE` (ponto de partida: 0.6) e as proporções
   de distância em `config.py` com testes reais na distância de instalação
   da catraca.
3. Substituir os placeholders de hardware pelas chamadas reais de GPIO
   (servo motor) e leitura do RC522 (RFID).
4. Conectar as mensagens de status ao display de LED via PCF8574T.
5. (Opcional, se sobrar tempo) treinar um classificador leve (MobileNetV2)
   para detecção de acessórios em vez da heurística de variância atual.

## Convenções e decisões já tomadas (não reabrir sem motivo forte)

- Terminologia: sempre "trabalho da disciplina", nunca "TCC".
- Comentários e nomes de variáveis em **português**, consistente em todo o
  projeto.
- Banco de dados do protótipo é **JSON local** por simplicidade — não
  sugerir migração para banco relacional a menos que pedido explicitamente.
- Documentação estruturada em Markdown é gerada junto com o código para
  registrar decisões e trade-offs à medida que o projeto evolui.
- Código modular e com placeholders bem documentados, separando lógica de
  protótipo da integração de hardware real.
- Câmera é acessada via OpenCV (`cv2.VideoCapture`) diretamente pela webcam
  local durante o desenvolvimento; no Pi final, o mesmo código deve
  funcionar trocando `CAMERA_INDEX` em `config.py`.

## O que evitar

- Não sugerir `face_recognition`/`dlib` para o embedding final (quebra a
  compatibilidade cross-platform com o app mobile).
- Não remover os comentários que documentam onde entra o hardware real
  (servo, RFID) — fazem parte da documentação do trabalho para a banca.
- Não reabrir a decisão de usar MediaPipe Face Landmarker + MobileFaceNet/
  InsightFace sem uma razão técnica concreta, já que essa decisão está
  documentada e justificada.
