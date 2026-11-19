#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define SS_PIN 21
#define RST_PIN 22

#define SDA_LCD 25
#define SCL_LCD 26

#define ENDERECO 0x27
#define COL 16
#define LIN 2

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(ENDERECO, COL, LIN);

byte uidCadastrado[] = {0xB7, 0x9F, 0x14, 0x15};

const unsigned long TEMPO_EXIBICAO = 3000;

void setup() {

  Serial.begin(115200);

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

  if (!rfid.PICC_IsNewCardPresent()) {
    delay(50);
    return;
  }

  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

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

    lcd.setCursor(0, 0);
    lcd.print("Bem vindo!");

  } else {

    Serial.println("Invalido :(");

    lcd.setCursor(0, 0);
    lcd.print("Invalido");

  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(TEMPO_EXIBICAO);

  mostrarTelaPadrao();
}

void mostrarTelaPadrao() {

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Aproxime o");

  lcd.setCursor(0, 1);
  lcd.print("cartao/rosto");
}