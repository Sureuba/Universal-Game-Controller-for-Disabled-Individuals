#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <BLEClient.h>

static BLEUUID SERVICE_UUID("ec3af789-2154-49f4-a9fc-bc6c88e9e930");
static BLEUUID CHAR_UUID   ("f3a56edf-8f1e-4533-93bf-5601b2e91308");

static BLEClient* pClient = nullptr;
static BLERemoteCharacteristic* pRemoteChar = nullptr;

volatile float latestValue = -1.0f;   // -1 means "no data yet"
volatile bool haveNotify = false;

static bool found = false;
static BLEAddress foundAddr("");

static float parseAsciiFloat(const uint8_t* data, size_t len) {
  char buf[32];
  size_t n = (len < sizeof(buf) - 1) ? len : (sizeof(buf) - 1);
  memcpy(buf, data, n);
  buf[n] = '\0';
  return atof(buf);
}

static void notifyCB(BLERemoteCharacteristic*, uint8_t* data, size_t len, bool) {
  latestValue = parseAsciiFloat(data, len);
  haveNotify = true;
}

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice dev) override {
    if (dev.haveServiceUUID() && dev.isAdvertisingService(SERVICE_UUID)) {
      foundAddr = dev.getAddress();
      found = true;
      BLEDevice::getScan()->stop();
    }
  }
};

void startScan() {
  BLEScan* scan = BLEDevice::getScan();
  scan->clearResults();
  scan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks(), true);
  scan->setActiveScan(true);
  scan->start(3, false);
}

bool connectAndSubscribe() {
  if (!pClient) pClient = BLEDevice::createClient();
  if (!pClient->connect(foundAddr)) return false;

  BLERemoteService* svc = pClient->getService(SERVICE_UUID);
  if (!svc) { pClient->disconnect(); return false; }

  pRemoteChar = svc->getCharacteristic(CHAR_UUID);
  if (!pRemoteChar) { pClient->disconnect(); return false; }

  if (!pRemoteChar->canNotify()) { pClient->disconnect(); return false; }

  pRemoteChar->registerForNotify(notifyCB);
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(300); // give serial time to come up

  BLEDevice::init("");
  startScan();
}

void loop() {
  // ALWAYS print a number so Serial Plotter shows something
  // If not connected yet, you’ll see -1.000 (flat line) instead of nothing.
  Serial.println(latestValue, 3);

  // If we found device but aren't connected, connect/sub
  if (found && (!pClient || !pClient->isConnected())) {
    haveNotify = false;
    latestValue = -1.0f;
    connectAndSubscribe();
  }

  // If we haven't found it yet, keep scanning occasionally
  static uint32_t lastScanMs = 0;
  if (!found && (millis() - lastScanMs > 3000)) {
    lastScanMs = millis();
    startScan();
  }

  // If we got disconnected, allow re-scan
  if (pClient && !pClient->isConnected()) {
    found = false;
    pRemoteChar = nullptr;
    haveNotify = false;
    latestValue = -1.0f;
  }

  delay(10);
}