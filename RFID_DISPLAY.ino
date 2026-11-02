#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define SS_PIN 21
#define RST_PIN 22

#define SDA_LCD 25
#define SCL_LCD 26

#define LED_VERDE 27
#define LED_VERMELHO 32

#define ENDERECO 0x27
#define COL 16
#define LIN 2

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(ENDERECO, COL, LIN);

byte uidCadastrado[] = {0xB7, 0x9F, 0x14, 0x15};

const unsigned long TEMPO_EXIBICAO = 3000;

void setup() {

  Serial.begin(115200);

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);

  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_VERMELHO, LOW);

  SPI.begin(18, 19, 23, 21);
  rfid.PCD_Init();

  Wire.begin(SDA_LCD, SCL_LCD);

  lcd.init();
  lcd.backlight();

  mostrarTelaPadrao();

  delay(100);

  Serial.println("Aproxime a tag...");
}

void loop() {
  // 1. Verifica se tem nova tag RFID
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    bool tagCorreta = true;

    if (rfid.uid.size != 4) {
      tagCorreta = false;
    } else {
      for (byte i = 0; i < 4; i++) {
        if (rfid.uid.uidByte[i] != uidCadastrado[i]) {
          tagCorreta = false;
          break;
        }
      }
    }

    lcd.clear();

    if (tagCorreta) {
      Serial.println("Abre porta");

      digitalWrite(LED_VERDE, HIGH);
      digitalWrite(LED_VERMELHO, LOW);

      lcd.setCursor(0, 0);
      lcd.print("Bem vindo!");

    } else {
      Serial.println("Invalido :(");

      digitalWrite(LED_VERDE, LOW);
      digitalWrite(LED_VERMELHO, HIGH);

      lcd.setCursor(0, 0);
      lcd.print("Invalido");
    }

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();

    delay(TEMPO_EXIBICAO);

    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_VERMELHO, LOW);

    mostrarTelaPadrao();
  }

  // 2. Verifica se o Python mandou o nome de alguem reconhecido pelo rosto
  if (Serial.available() > 0) {
    String nome = Serial.readStringUntil('\n');
    nome.trim();

    // ECO DE DEBUG PARA O PYTHON LER
    Serial.println("Recebido pelo Arduino: " + nome);

    if (nome.length() > 0) {
      lcd.clear();

      digitalWrite(LED_VERDE, HIGH);
      digitalWrite(LED_VERMELHO, LOW);

      lcd.setCursor(0, 0);
      lcd.print("Bem vindo!");

      lcd.setCursor(0, 1);
      if (nome.length() <= COL) {
        lcd.print(nome);
      } else {
        lcd.print(nome.substring(0, COL));
      }

      delay(TEMPO_EXIBICAO);

      digitalWrite(LED_VERDE, LOW);
      digitalWrite(LED_VERMELHO, LOW);

      mostrarTelaPadrao();
    }
  }

  delay(50);
}

void mostrarTelaPadrao() {

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Aproxime o");

  lcd.setCursor(0, 1);
  lcd.print("cartao/rosto");
}