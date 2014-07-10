/**************************************************************************/
/*! 
    @file     iso14443a_uid.pde
    @author   Adafruit Industries
    @license  BSD (see license.txt)

    This example will attempt to connect to an ISO14443A
    card or tag and retrieve some basic information about it
    that can be used to determine what type of card it is.   
   
    Note that you need the baud rate to be 115200 because we need to print
    out the data and read from the card at the same time!

    This is an example sketch for the Adafruit PN532 NFC/RFID breakout boards
    This library works with the Adafruit NFC breakout 
    ----> https://www.adafruit.com/products/364
 
    Check out the links above for our tutorials and wiring diagrams 
    These chips use I2C to communicate, 4 pins required to interface:
    SDA (I2C Data) and SCL (I2C Clock), IRQ and RESET (any digital line)

    Adafruit invests time and resources providing this open source code, 
    please support Adafruit and open-source hardware by purchasing 
    products from Adafruit!
*/
/**************************************************************************/
#include <Wire.h>
#include <Adafruit_NFCShield_I2C.h>


#define IRQ   (2)
#define RESET (3)  // Not connected by default on the NFC Shield

Adafruit_NFCShield_I2C nfc(IRQ, RESET);

int pushButton[3] = {8, 9, 10};
int pushState[3] = {1, 1, 1};
char *file_name = "/home/root/hci/data.log";
FILE *dataFile;

void setup(void) {
  Serial.begin(115200);
  Serial.println("begin");
  
  dataFile = fopen(file_name, "w");

  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (! versiondata) {
    Serial.print("Didn't find PN53x board");
    while (1); // halt
  }
 
  
  nfc.setPassiveActivationRetries(1);
  
  nfc.SAMConfig();
  
  Serial.println("pin");
  
  pinMode(pushButton[0], INPUT);
  pinMode(pushButton[1], INPUT);
  pinMode(pushButton[2], INPUT);
  Serial.println("ok");
}

void check_button(int i){
  int buttonState = digitalRead(pushButton[i]);
  //Serial.println(buttonState);
  if(buttonState == 0 && pushState[i] == 1){
    fprintf(dataFile, "button%d\r\n", i);
    fflush(dataFile);
    Serial.println(i);
  }
  pushState[i] = buttonState;
}

void loop(void) {
  boolean success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };  // Buffer to store the returned UID
  uint8_t uidLength;                        // Length of the UID (4 or 7 bytes depending on ISO14443A card type)
  
  check_button(0);
  check_button(1);
  check_button(2);
  
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, &uid[0], &uidLength);
  
  //frpintf(dataFile, "greeting");
  if (success) {
    for (uint8_t i=0; i < uidLength; i++) 
    {
      fprintf(dataFile, "%02x", uid[i] & 0xff); 
    }
    fprintf(dataFile, "\r\n");
    fflush(dataFile);
    Serial.println("card");
    delay(1000);
  }
  else
  {
    // PN532 probably timed out waiting for a card
    //Serial.println("Timed out waiting for a card");
  }
}
