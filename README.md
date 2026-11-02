# Protótipo — Módulo de Reconhecimento Facial

Protótipo do trabalho da disciplina de Sistemas Embarcados (catraca/totem com
Raspberry Pi). Este módulo cobre a parte de **reconhecimento facial** descrita
nos documentos do projeto: registro (com checagem de qualidade e acessórios) e
destravamento da catraca (com fallback para RFID).

## Estrutura

- `config.py` — limiares e caminhos (já calibrados com a webcam do desenvolvedor; recalibrar no hardware final)
- `face_utils.py` — detecção do rosto, distância (entre olhos), pose, nitidez e heurísticas de acessórios (MediaPipe Face Landmarker)
- `embedding.py` — geração do vetor facial (embedding):
  - `ExtratorTFLite`: MobileFaceNet (`mobilefacenet.tflite`), **usado nos fluxos de registro e destravamento**
  - `ExtratorPlaceholder`: geométrico, só para testes de pipeline, **não é o modelo final**
- `database.py` — banco local em JSON com embeddings cadastrados + matching por similaridade de cosseno
- `registro.py` — cadastro facial (webcam guia o usuário e salva a média de várias capturas)
- `destravamento.py` — catraca: reconhece o rosto, aciona o servo motor (placeholder) e cai para RFID/Arduino se falhar muitas vezes seguidas
- `requirements.txt` — dependências e passo a passo dos comandos de execução

## Como rodar (com webcam local)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

O `ExtratorTFLite` precisa de `tflite-runtime` (Raspberry Pi/Linux) **ou** `tensorflow` (PC);
instale um dos dois (ver `requirements.txt`).

Arquivos exigidos na raiz do projeto:
- `face_landmarker.task` (MediaPipe; link em `config.py`)
- `mobilefacenet.tflite` (modelo de embedding)

Antes de rodar, ajuste em `config.py`: `CAMERA_INDEX` (índice da webcam) e
`PORTA_ARDUINO` (ex: `/dev/ttyACM0`, `COM3`; `None` = sem display/RFID).

Cadastrar um usuário:
```bash
python registro.py "joao"
```
Fique de frente, dentro da faixa de distância, sem óculos/máscara, e pressione
`c`. São capturados 5 frames válidos e salva-se a **média** dos embeddings.
Pressione `q` para cancelar.

Rodar a catraca:
```bash
python destravamento.py
```
Pressione `q` para encerrar.

### Gerenciando os cadastros locais

Você pode visualizar e apagar os rostos cadastrados no banco de dados local (`usuarios_embeddings.json`) usando o arquivo `database.py`:

```bash
# Ver quem está cadastrado
python database.py listar

# Apagar um usuário específico
python database.py remover "joao"

# Apagar todos os usuários cadastrados
python database.py limpar
```

Ao mudar critérios de qualidade/distância, refaça os cadastros
(`python database.py limpar` e depois `python registro.py "nome"`).

## Consistência do embedding (critérios de qualidade)

Distância, pose e nitidez alteram o embedding, então são exigidas antes de gerar
ou comparar embeddings:

| Critério | Como é medido | Registro | Destravamento |
|---|---|---|---|
| Distância | distância entre os olhos / largura do frame | 0.10 – 0.20 | 0.09 – 0.22 |
| Pose | yaw e pitch (0 = frontal) | yaw 0.08 / pitch 0.12 | yaw 0.14 / pitch 0.20 |
| Nitidez | variância do Laplaciano (recorte 112x112) | ≥ 60 | ≥ 30 |
| Acessórios | óculos e máscara | checado | não checado |

Os valores ficam em `config.py` (`REGISTRO_*` e `DESTRAVAMENTO_*`).

### Acessórios

- **Óculos (inclusive de grau):** bordas da armação sob os olhos e na ponte do
  nariz (`BORDAS_MAX_OLHOS`, calibrado: sem óculos ≈ 0.20, com óculos ≈ 0.50).
- **Máscara:** variância de `z` dos landmarks da boca (`CONFIANCA_MIN_BOCA`,
  calibrado: sem máscara ≈ 0.045, com máscara ≈ 0.025). Heurística frágil; pode
  variar com distância, pose e barba.

### Calibração

A tela do registro mostra `Bordas olhos`, `Boca`, `Dist.olhos`, `yaw`, `pitch` e
`nitidez` em tempo real. Meça com e sem o acessório, na posição correta, e
ajuste os limiares em `config.py`.

## O que falta para a versão "de verdade" (próximos passos do trabalho)

1. **Validar o embedding do app mobile** com o mesmo `mobilefacenet.tflite`, conforme
   decidido no `Stack_Reconhecimento_Facial.md`.
2. **Calibrar `LIMIAR_SIMILARIDADE`**, as faixas de distância, pose, nitidez e os
   limiares de acessórios em `config.py` com testes reais na distância em que a
   catraca vai ficar instalada.
3. **Trocar os placeholders de hardware** (`abrir_catraca`, `ler_rfid`) pelas
   bibliotecas reais do Pi (`gpiozero`/`RPi.GPIO` para o servo, `mfrc522` para o RC522).
4. **Ligar o display de LED** (via PCF8574T) às mensagens que hoje aparecem só no `cv2.imshow`.
5. Opcional, se sobrar tempo: treinar um classificador leve (MobileNetV2) para
   detecção de óculos/máscara em vez das heurísticas atuais, como já é discutido
   no `Stack_Reconhecimento_Facial.md`.

Este protótipo já valida o **fluxo completo de software**: registro → checagem
de qualidade/acessórios → salvamento do embedding (média de capturas) → matching
→ sinal de abertura da catraca — faltando só o hardware real do Pi e a
integração com o app.
