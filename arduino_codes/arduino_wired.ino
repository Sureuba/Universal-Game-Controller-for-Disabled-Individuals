#define SENSOR_PIN A0

int muscleSignal;


void setup() {

  Serial.begin(9600); //Start serial communication at 9600 baud rate 

}


void loop() {

  //Repeatedly run this code to read the sensor

  muscleSignal = analogRead(SENSOR_PIN);  // Read the processed muscle signal from A0

  

  Serial.print(500); // To freeze the lower limit

  Serial.print(" ");

  Serial.print(650); // To freeze the upper limit

  Serial.print(" ");


  Serial.println(muscleSignal);       // Output the value to the serial port

}