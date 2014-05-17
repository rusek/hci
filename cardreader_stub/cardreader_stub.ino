void setup() { 
 // Initialize serial and wait for port to open:
  Serial.begin(9600); 
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  
} 

void loop() { 
  Serial.println("aaa"); 
  delay(1000);
  Serial.println("bbb"); 
  delay(1000);
  Serial.println("ccc"); 
  delay(1000);
}

