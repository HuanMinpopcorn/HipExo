const int analogPin = A0;  // Pin connected to amplifier output
int sensorValue = 0;       // Raw sensor value
float filteredValue = 0.0; // Smoothed value

float alpha = 0.01;        // Low-pass filter smoothing factor

void setup() {
  Serial.begin(9600);      // Start serial communication
}

void loop() {
  sensorValue = analogRead(analogPin);  // Read the analog input

  // Apply low-pass filter
  // filteredValue = alpha * sensorValue + (1 - alpha) * filteredValue;

  // Convert filtered value to weight
  float gain = -0.201452087;        // Calibration gain
  float offset = 84.57830584;
    


  float weight = sensorValue * gain + offset;

  // Print result
  Serial.print("Weight(N): ");
  Serial.println(weight);

  delay(10);               // Small delay between readings
}