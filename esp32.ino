// WARNING use Arduino ESP32 library version 1.0.4, newer is unstable
#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <Timestamps.h>
#include <Battery18650Stats.h>

// Scale Mac Address, please use lowercase letters
#define scale_mac_addr "00:00:00:00:00:00"

// Network details
const char* ssid = "ssid_name";
const char* password = "password";

// Synchronization status LED, for LOLIN32 D32 PRO is pin 5
const int led_pin = 5;

// Instantiating object of class Timestamp (time offset is possible in import_data.sh file)
Timestamps ts(0);

// Battery voltage measurement, for LOLIN32 D32 PRO is pin 35
Battery18650Stats battery(35);

// MQTT details
const char* mqtt_server = "ip_address";
const int mqtt_port = 1883;
const char* mqtt_userName = "admin";
const char* mqtt_userPass = "user_password";
const char* clientId = "esp32_scale";
const char* mqtt_attributes = "data"; 

String mqtt_clientId = String(clientId);
String mqtt_topic_attributes = String(mqtt_attributes);
String publish_data;

WiFiClient espClient;
PubSubClient mqtt_client(espClient);

int16_t stoi(String input, uint16_t index1) {
    return (int16_t)(strtol(input.substring(index1, index1+2).c_str(), NULL, 16));
}
int16_t stoi2(String input, uint16_t index1) {
    return (int16_t)(strtol((input.substring(index1+2, index1+4) + input.substring(index1, index1+2)).c_str(), NULL, 16));
}

void goToDeepSleep() {
  // Deep sleep for 7 minutes
  Serial.println("* Waiting for next scan, going to sleep");
  esp_sleep_enable_timer_wakeup(7 * 60 * 1000000);
  esp_deep_sleep_start();
}

void StartESP32() {
  // LED indicate start ESP32, is on for 0.25 second
  pinMode(led_pin, OUTPUT); 
  digitalWrite(led_pin, LOW);
  delay(250);
  digitalWrite(led_pin, HIGH);

  // Initializing serial port for debugging purposes, version info
  Serial.begin(115200);
  Serial.println("");
  Serial.println("Mi Body Composition Scale 2 Garmin Connect v4.4 (esp32.ino)");
  Serial.println("");
}

void errorLED_connect() {
  pinMode(led_pin, OUTPUT); 
  digitalWrite(led_pin, LOW);
  delay(5000);
  Serial.println("failed");
  goToDeepSleep();
}

void connectWiFi() {
   int nFailCount = 0;
   Serial.print("* Connecting to WiFi: ");
     while (WiFi.status() != WL_CONNECTED) {
       WiFi.mode(WIFI_STA);
       WiFi.begin(ssid, password);
       WiFi.waitForConnectResult();
     if (WiFi.status() == WL_CONNECTED) {
        Serial.println("connected");
        Serial.print("  IP address: ");
        Serial.println(WiFi.localIP());
     }
     else {
       Serial.print(".");
       delay(200);
       nFailCount++;
       if (nFailCount > 75)
          errorLED_connect();
    }
  }
}

void connectMQTT() {
   int nFailCount = 0;
   connectWiFi();
   Serial.print("* Connecting to MQTT: ");
     while (!mqtt_client.connected()) {
       mqtt_client.setServer(mqtt_server, mqtt_port);
     if (mqtt_client.connect(mqtt_clientId.c_str(),mqtt_userName,mqtt_userPass)) {
       Serial.println("connected");
     }
     else {
       Serial.print(".");
       delay(200);
       nFailCount++;
       if (nFailCount > 75)
          errorLED_connect();
    }  
  }
}

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      Serial.print("  BLE device found with address: ");
      Serial.print(advertisedDevice.getAddress().toString().c_str());
      if (advertisedDevice.getAddress().toString() == scale_mac_addr) {
        Serial.println(" <= target device");
        BLEScan *pBLEScan = BLEDevice::getScan(); // found what we want, stop now
        pBLEScan->stop();
      }
      else {
        Serial.println(", non-target device");
      }      
   }
};

void errorLED_scan() {
  pinMode(led_pin, OUTPUT); 
  digitalWrite(led_pin, LOW);
  delay(5000);
  Serial.println("* Reading BLE data incomplete, finished BLE scan");
  goToDeepSleep();
}

void ScanBLE() {
  Serial.println("* Starting BLE scan:");
  BLEDevice::init("");
  BLEScan *pBLEScan = BLEDevice::getScan(); //Create new scan.
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(false); //Active scan uses more power.
  pBLEScan->setInterval(0x50);
  pBLEScan->setWindow(0x30);
  
  // Scan for 10 seconds
  BLEScanResults foundDevices = pBLEScan->start(10);
  int count = foundDevices.getCount();
  for (int i = 0; i < count; i++) {
    BLEAdvertisedDevice d = foundDevices.getDevice(i);
    if (d.getAddress().toString() != scale_mac_addr)
      continue;
    String hex;
    if (d.haveServiceData()) {
      std::string md = d.getServiceData();
      uint8_t* mdp = (uint8_t*)d.getServiceData().data();
      char *pHex = BLEUtils::buildHexData(nullptr, mdp, md.length());
      hex = pHex;
      free(pHex);
    }
    float Weight = stoi2(hex, 22) * 0.005;
    float Impedance = stoi2(hex, 18);
    if (Impedance > 0) {
      int Unix_time = ts.getTimestampUNIX(stoi2(hex, 4), stoi(hex, 8), stoi(hex, 10), stoi(hex, 12), stoi(hex, 14), stoi(hex, 16));  
      
      // LED blinking for 0.75 second, indicate finish reading BLE data
      Serial.println("* Reading BLE data complete, finished BLE scan");
      digitalWrite(led_pin, LOW);
      delay(250);
      digitalWrite(led_pin, HIGH);
      delay(250);
      digitalWrite(led_pin, LOW);
      delay(250);
      digitalWrite(led_pin, HIGH);

      // Prepare to send raw values
      publish_data += String(Weight);
      publish_data += String(";");
      publish_data += String(Impedance, 0);
      publish_data += String(";");
      publish_data += String(Unix_time);
      publish_data += String(";");
      publish_data += String(battery.getBatteryVolts());
      publish_data += String(";");
      publish_data += String(battery.getBatteryChargeLevel());

      // Send data to MQTT broker and let app figure out the rest
      connectMQTT();
      mqtt_client.publish(mqtt_topic_attributes.c_str(), publish_data.c_str(), true);
      Serial.print("* Publishing MQTT data: ");
      Serial.println(publish_data.c_str());
    }
    else {
      errorLED_scan();
    }
  }
}

void setup() {
  StartESP32();
  ScanBLE();
  goToDeepSleep();
}

void loop() {
}