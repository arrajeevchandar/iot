#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ctime>
#include "cloud_manager.h"
#include "config.h"
#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "secrets.example.h"
#endif
struct Message { char data[2048]; };
static QueueHandle_t outgoing, incoming;
static void cloudTask(void*) {
  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  configTime(0,0,"pool.ntp.org","time.google.com");
  uint32_t retry=millis();
  for(;;) {
    Message msg{};
    if(WiFi.status()!=WL_CONNECTED && millis()-retry>=config::WIFI_RETRY_MS) { WiFi.reconnect(); retry=millis(); }
    if(xQueueReceive(outgoing,&msg,pdMS_TO_TICKS(200))!=pdTRUE) continue;
    if(WiFi.status()!=WL_CONNECTED || strlen(CLOUD_URL)==0) continue;
    String url=String(CLOUD_URL)+"/api/devices/"+DEVICE_ID+"/telemetry";
    HTTPClient http; WiFiClient plain; WiFiClientSecure tls;
    bool begun=false;
    if(url.startsWith("https://") && strlen(CLOUD_ROOT_CA)>0 && time(nullptr)>1700000000) {
      tls.setCACert(CLOUD_ROOT_CA); begun=http.begin(tls,url);
    } else if(url.startsWith("http://") && ALLOW_INSECURE_HTTP) begun=http.begin(plain,url);
    if(!begun) { Serial.println("CLOUD: configure HTTPS root CA and wait for NTP, or explicit lab HTTP"); continue; }
    http.setConnectTimeout(2000); http.setTimeout(2000);
    http.addHeader("Content-Type","application/json"); http.addHeader("Authorization",String("Bearer ")+DEVICE_TOKEN);
    const int code=http.POST(reinterpret_cast<uint8_t*>(msg.data),strlen(msg.data));
    if(code==200) { String response=http.getString(); if(response.length()<sizeof(msg.data)) { response.toCharArray(msg.data,sizeof(msg.data)); xQueueOverwrite(incoming,&msg); } }
    else Serial.printf("CLOUD: HTTP %d; local automation remains active\n",code);
    http.end();
  }
}
void initializeCloud() {
  outgoing=xQueueCreate(1,sizeof(Message)); incoming=xQueueCreate(1,sizeof(Message));
  xTaskCreatePinnedToCore(cloudTask,"cloud",12288,nullptr,1,nullptr,0);
}
void sendTelemetry(const State& s) {
  JsonDocument d; d["source"]="esp32"; d["temperature"]=s.sensors.temperature; d["humidity"]=s.sensors.humidity;
  d["light"]=s.sensors.light; d["air_quality"]=s.sensors.air; d["occupancy"]=s.sensors.occupancy; d["sensor_valid"]=s.sensors.valid;
  d["mode"]=s.mode==Mode::AUTO?"AUTO":"MANUAL"; d["light1"]=s.outputs.light1; d["light2"]=s.outputs.light2; d["fan"]=s.outputs.fan;
  d["servo"]=s.outputs.servo; d["alarm"]=s.outputs.alarm; d["power_w"]=s.power; d["energy_wh"]=s.energyWh;
  d["auto_wh"]=s.autoWh; d["baseline_wh"]=s.baselineWh; d["ml_class"]=className(s.mlClass); d["confidence"]=s.confidence;
  d["alert"]=s.alert==2?"CRITICAL":s.alert==1?"WARNING":"INFO"; d["applied_version"]=s.commandVersion;
  Message msg{}; serializeJson(d,msg.data,sizeof(msg.data)); xQueueOverwrite(outgoing,&msg);
}
void receiveCommands(State& s) {
  Message msg{}; if(xQueueReceive(incoming,&msg,0)!=pdTRUE) return;
  JsonDocument d; if(deserializeJson(d,msg.data)) return;
  auto c=d["command"];
  if(!c.is<JsonObject>() || !c["version"].is<uint64_t>()) return;
  uint64_t version=c["version"]; if(version<=s.commandVersion) return;
  const String mode=c["mode"] | "";
  if(mode!="AUTO" && mode!="MANUAL") return;
  if(!c["light1"].is<bool>() || !c["light2"].is<bool>() || !c["fan"].is<bool>() || !c["servo"].is<int>()) return;
  int angle=c["servo"]; if(angle<0 || angle>180) return;
  s.mode=mode=="AUTO"?Mode::AUTO:Mode::MANUAL;
  s.manual.light1=c["light1"]; s.manual.light2=c["light2"]; s.manual.fan=c["fan"]; s.manual.servo=angle; s.manual.alarm=false;
  s.commandVersion=version;
}
