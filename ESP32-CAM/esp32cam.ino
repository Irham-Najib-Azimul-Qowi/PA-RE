#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <PubSubClient.h>

const char* ssid = "ssid";
const char* password = "password";

const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;
const char* topic_ip = "lintas_alam/ip1";
const char* topic_lampu = "lintas_alam/lampu1";

WiFiClient espClient;
PubSubClient mqttClient(espClient);
WebServer server(80);

#define FLASH_PIN 4
bool flashState = false;

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

WiFiClient streamClient;
bool isStreaming = false;
unsigned long lastFrameTime = 0;
const unsigned long frameInterval = 100;

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (String(topic) == topic_lampu) {
    if (message == "ON") {
      digitalWrite(FLASH_PIN, HIGH);
      flashState = true;
    } else if (message == "OFF") {
      digitalWrite(FLASH_PIN, LOW);
      flashState = false;
    }
  }
}

void reconnect() {
  while (!mqttClient.connected()) {
    String clientId = "ESP32CAM-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      mqttClient.subscribe(topic_lampu);
      String ip = WiFi.localIP().toString();
      mqttClient.publish(topic_ip, ip.c_str());
    } else {
      delay(5000);
    }
  }
}

void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }
  server.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void handleStreamStart() {
  streamClient = server.client();
  isStreaming = true;
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  streamClient.print(response);
}

void sendNextFrame() {
  if (!isStreaming) return;
  if (!streamClient.connected()) {
    isStreaming = false;
    return;
  }

  unsigned long now = millis();
  if (now - lastFrameTime > frameInterval) {
    lastFrameTime = now;
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) return;

    streamClient.print("--frame\r\n");
    streamClient.print("Content-Type: image/jpeg\r\n");
    streamClient.print("Content-Length: " + String(fb->len) + "\r\n\r\n");
    streamClient.write(fb->buf, fb->len);
    streamClient.print("\r\n");

    esp_camera_fb_return(fb);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(FLASH_PIN, OUTPUT);
  digitalWrite(FLASH_PIN, LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_VGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return;
  }
  sensor_t * s = esp_camera_sensor_get();  
  s->set_vflip(s, 1);    // Flip vertical (0 = normal, 1 = terbalik)
  s->set_hmirror(s, 1);  // Mirror horizontal (0 = normal, 1 = cermin)

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);

  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/stream", HTTP_GET, handleStreamStart);
  server.begin();

  Serial.print("Streaming tersedia di: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();
  server.handleClient();
  sendNextFrame();  // Kirim frame hanya kalau isStreaming = true
}