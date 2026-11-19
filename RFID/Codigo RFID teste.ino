#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 21
#define RST_PIN 22

#define LED_VERDE 25
#define LED_VERMELHO 26

MFRC522 rfid(SS_PIN, RST_PIN);

byte uidCadastrado[] = {0xB7, 0x9F, 0x14, 0x15};

void setup() {

  Serial.begin(115200);

  SPI.begin(18, 19, 23, 21);
  rfid.PCD_Init();

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);

  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_VERMELHO, LOW);

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

  if (tagCorreta) {

    Serial.println("Abre porta");

    digitalWrite(LED_VERDE, HIGH);
    digitalWrite(LED_VERMELHO, LOW);

  } else {

    Serial.println("Invalido :(");

    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_VERMELHO, HIGH);
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(500);

  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_VERMELHO, LOW);
}