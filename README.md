# Controle de Acesso RFID com ESP32

Projeto de controle de acesso utilizando um ESP32, um leitor RFID-RC522 e, em uma das versões, um display LCD 16x2 com comunicação I2C.

O projeto lê o identificador (UID) de uma tag RFID e compara com um UID previamente cadastrado no código. Quando a tag corresponde ao cadastro, o acesso é autorizado. Caso contrário, a leitura é considerada inválida.

## Versões disponíveis

O projeto possui dois sketches Arduino (`.ino`):

### 1. `Codigo RFID teste.ino`

Versão de teste com sinalização por LEDs.

- Lê o UID da tag usando o módulo RC522.
- Compara o UID lido com o UID cadastrado.
- Acende o LED verde quando a tag é válida.
- Acende o LED vermelho quando a tag é inválida.
- Envia o resultado da validação pela Serial.

### 2. `RFID_DISPLAY.ino`

Versão com retorno visual em um display LCD 16x2.

- Lê e valida o UID da tag RFID.
- Exibe **"Bem vindo!"** quando a tag é válida.
- Exibe **"Invalido"** quando a tag não corresponde ao cadastro.
- Após três segundos, retorna à tela inicial: **"Aproxime o cartao/rosto"**.
- Envia o resultado da validação pela Serial.

> Observação: apesar da mensagem da tela inicial mencionar "rosto", os códigos deste repositório implementam somente a leitura e validação RFID. Não há implementação de reconhecimento facial nestes sketches.

## Componentes

- ESP32
- Módulo leitor RFID RC522
- Tag ou cartão RFID compatível
- LEDs verde e vermelho (para a versão de teste)
- Display LCD 16x2 com módulo I2C (para a versão com display)
- Jumpers e protoboard, conforme a montagem

## Pinagem

### RC522 conectado ao ESP32

A configuração SPI utilizada no código é:

| Sinal do RC522 | GPIO do ESP32 |
|---|---:|
| SDA / SS | 21 |
| SCK | 18 |
| MISO | 19 |
| MOSI | 23 |
| RST | 22 |

### LEDs — `Codigo RFID teste.ino`

| Componente | GPIO do ESP32 |
|---|---:|
| LED verde | 25 |
| LED vermelho | 26 |

### LCD I2C — `RFID_DISPLAY.ino`

| Sinal do LCD | GPIO do ESP32 |
|---|---:|
| SDA | 25 |
| SCL | 26 |

Configurações do display:

- Endereço I2C: `0x27`
- Dimensões: 16 colunas × 2 linhas

**Atenção:** os GPIOs 25 e 26 são usados pelos LEDs na primeira versão e pelo barramento I2C do LCD na segunda. São montagens alternativas; não conecte os dois circuitos simultaneamente seguindo essas duas configurações.

## Bibliotecas

Instale as seguintes bibliotecas pela Arduino IDE:

- `MFRC522`
- `LiquidCrystal_I2C` — necessária somente para `RFID_DISPLAY.ino`

As bibliotecas `SPI` e `Wire` são utilizadas para comunicação com os periféricos e normalmente já acompanham o ambiente do ESP32.

## Configuração do cartão autorizado

Nos dois sketches, o UID autorizado está definido nesta linha:

```cpp
byte uidCadastrado[] = {0xB7, 0x9F, 0x14, 0x15};
```

Para autorizar outro cartão, substitua os valores pelos bytes do UID da sua tag. O código atual espera um UID de quatro bytes; cartões com outro tamanho são rejeitados.

## Como executar

1. Abra a Arduino IDE e configure o suporte à placa ESP32.
2. Conecte os componentes conforme a pinagem da versão escolhida.
3. Instale as bibliotecas necessárias.
4. Abra um dos arquivos `.ino`.
5. Selecione a placa ESP32 e a porta serial correspondente.
6. Compile e envie o programa para a placa.
7. Abra o Monitor Serial em `115200 baud`.
8. Aproxime uma tag RFID do leitor RC522 e observe o resultado no LED ou no LCD, conforme a versão.

## Funcionamento

O programa verifica continuamente se há uma nova tag próxima ao leitor. Quando uma tag é detectada, tenta obter seu UID e compara seu tamanho e cada um de seus bytes com o UID cadastrado.

- **UID correspondente:** acesso autorizado.
- **UID diferente ou tamanho diferente:** acesso negado.

Após a leitura, o programa encerra a comunicação com a tag e aguarda antes de aceitar uma nova leitura.

## Limitações atuais

- O UID autorizado está definido diretamente no código.
- O projeto utiliza uma única tag cadastrada.
- Não há cadastro ou remoção dinâmica de cartões.
- Não há integração com banco de dados ou servidor nos sketches disponibilizados.
- A saída "Abre porta" é apenas uma mensagem na Serial; não há acionamento de fechadura ou mecanismo físico de abertura implementado nesses arquivos.
- A validação por UID é uma demonstração básica de controle de acesso e não deve ser considerada, isoladamente, um mecanismo de autenticação de alta segurança.

## Estrutura

```text
RFID/
├── Codigo RFID teste.ino
├── RFID_DISPLAY.ino
└── README.md
```
