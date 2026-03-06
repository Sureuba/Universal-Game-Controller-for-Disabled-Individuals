// MyoWare 2.0 Wireless Shield (ESP32-WROOM) RAW logging over USB
// A3 = ENV, A4 = RAW, A5 = REF  (per MyoWare library/examples) :contentReference[oaicite:3]{index=3}

const int ENV_PIN = A3;
const int RAW_PIN = A4;
const int REF_PIN = A5;

const int FS = 1000;                         // 1000 Hz
const uint32_t SAMPLE_US = 1000000UL / FS;
uint32_t nextSample = 0;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);                  // 0–4095
  nextSample = micros();
  Serial.println("t_us,env,raw,ref,raw_centered");
}

void loop() {
  uint32_t now = micros();
  if ((int32_t)(now - nextSample) >= 0) {
    nextSample += SAMPLE_US;

    int env = analogRead(ENV_PIN);
    int raw = analogRead(RAW_PIN);
    int ref = analogRead(REF_PIN);
    int raw_centered = raw - ref;

    Serial.print(now); Serial.print(",");
    Serial.print(env); Serial.print(",");
    Serial.print(raw); Serial.print(",");
    Serial.print(ref); Serial.print(",");
    Serial.println(raw_centered);
  }
}