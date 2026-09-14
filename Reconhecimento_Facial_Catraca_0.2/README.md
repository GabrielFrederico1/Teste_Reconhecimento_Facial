# Protótipo — Módulo de Reconhecimento Facial

Protótipo do trabalho da disciplina de Sistemas Embarcados (catraca/totem com
Raspberry Pi). Este módulo cobre a parte de **reconhecimento facial** descrita
nos documentos do projeto: registro (com checagem de acessórios) e
destravamento da catraca (com fallback para RFID).

## Estrutura

- `config.py` — limiares e caminhos (calibrar depois de testar com a câmera real)
- `face_utils.py` — detecção do rosto, distância e heurística de acessórios (MediaPipe Face Landmarker)
- `embedding.py` — geração do vetor facial (embedding). Tem duas implementações:
  - `ExtratorPlaceholder`: geométrico, só para validar o pipeline, **não é o modelo final**
  - `ExtratorTFLite`: **modelo real já integrado** (MobileFaceNet, `mobilefacenet.tflite` incluso na pasta). `registro.py` e `destravamento.py` usam automaticamente o modelo real se o arquivo `.tflite` estiver presente; caso contrário caem no placeholder e avisam no console.
- `database.py` — banco local em JSON com embeddings cadastrados + matching por similaridade de cosseno
- `registro.py` — fluxo de cadastro facial (roda a webcam e guia o usuário)
- `destravamento.py` — fluxo da catraca: reconhece o rosto, aciona o servo motor (placeholder) e cai para RFID (placeholder) se falhar muitas vezes seguidas

## Como rodar (com webcam local, para testar o pipeline)

```bash
pip install -r requirements.txt
```

Baixe o modelo do MediaPipe Face Landmarker (link está comentado em `config.py`)
e coloque o arquivo `face_landmarker.task` na raiz do projeto.

Cadastrar um usuário:
```bash
python registro.py "joao"
```

Rodar a catraca:
```bash
python destravamento.py
```

## O que falta para a versão "de verdade" (próximos passos do trabalho)

1. ~~Trocar o `ExtratorPlaceholder` pelo `ExtratorTFLite`~~ — **feito**. O
   modelo `mobilefacenet.tflite` (convertido a partir do InsightFace, fonte:
   github.com/MCarlomagno/FaceRecognitionAuth) já está integrado e validado
   (entrada 112x112x3, saída 192-d normalizada). Falta apenas usar o **mesmo**
   modelo no app mobile, conforme decidido no `Stack_Reconhecimento_Facial.md`,
   e documentar a fonte do modelo no relatório do trabalho.
2. **Calibrar `LIMIAR_SIMILARIDADE`** (ponto de partida: 0.6, com o modelo
   real) e as proporções de distância em `config.py`
   com testes reais na distância em que a catraca vai ficar instalada.
3. **Trocar os placeholders de hardware** (`abrir_catraca`, `ler_rfid`) pelas
   bibliotecas reais do Pi (`gpiozero`/`RPi.GPIO` para o servo, `mfrc522` para o RC522).
4. **Ligar o display de LED** (via PCF8574T) às mensagens que hoje aparecem só no `cv2.imshow`.
5. Opcional, se sobrar tempo: treinar um classificador leve (MobileNetV2) para
   detecção de óculos/máscara em vez da heurística atual, como já é discutido
   no `Stack_Reconhecimento_Facial.md`.

Este protótipo já valida o **fluxo completo de software**: registro → checagem
de acessórios/distância → salvamento do embedding → matching → sinal de
abertura da catraca — faltando só plugar o modelo de embedding definitivo e o
hardware real do Pi.
