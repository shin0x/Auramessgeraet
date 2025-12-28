#include <random>

const int HUMIDITY_SENSOR_PIN = 15;
const int LED_PINS[] = {13,12,14,27,26,25,33,32};//,16,17};
const int LED_AMOUNT = sizeof(LED_PINS) / sizeof(LED_PINS[0]);
const int MOTOR_PIN = 2;
const int SPEAKER_PIN = 1;
const int DEFAULT_DELAY = 400;

int current_led_pin_ctr = 0;
int current_motor_speed = 0;

void clear_next_led(){
  if(current_led_pin_ctr < 0)
    return;

  Serial.println(current_led_pin_ctr);
  digitalWrite(LED_PINS[current_led_pin_ctr], LOW);

  current_led_pin_ctr --;
}

void power_next_led(){
  // go one led forward
  if (current_led_pin_ctr >= LED_AMOUNT)
    return;
  digitalWrite(LED_PINS[current_led_pin_ctr], HIGH);
  current_led_pin_ctr ++;
}

void init_leds(){
  // turn all leds on
  for(int i=0; i<LED_AMOUNT; i++){
    digitalWrite(LED_PINS[i], 1);
  }
  delay(1000);
  // turn all off after some delay for start-up visual
  for(int i=LED_AMOUNT - 1; i>=0; i--){
    digitalWrite(LED_PINS[i], 0);
    delay(DEFAULT_DELAY);
  }
  current_led_pin_ctr = 0;
}

void control_motor(bool status, int& power){
  // turn off motor
  if(!status){
    digitalWrite(MOTOR_PIN, 0);
    return;
  }
  analogWrite(MOTOR_PIN, power);
}

void create_sound(int max_pwm=1000){
  int cur_pwm = (int)random(max_pwm);
  analogWrite(SPEAKER_PIN, cur_pwm);
}

void setup() {
  Serial.begin(115200);
  // init pins
  pinMode(HUMIDITY_SENSOR_PIN, INPUT);
  // iterate through LEDs
  for (int i=0; i<LED_AMOUNT; i++){
    pinMode(LED_PINS[i], OUTPUT);
  }

  pinMode(MOTOR_PIN, OUTPUT);

  // short sound at startup
  pinMode(SPEAKER_PIN, OUTPUT);
  digitalWrite(SPEAKER_PIN, HIGH);
  delay(DEFAULT_DELAY);
  digitalWrite(SPEAKER_PIN, LOW);


  init_leds();
}

void loop() {
  // check for finger on sensor
  //Serial.println(analogRead(HUMIDITY_SENSOR_PIN));
  if(analogRead(HUMIDITY_SENSOR_PIN) > 3000){
    // finger is on sensor
    power_next_led();
    current_motor_speed += 300;
    if (current_motor_speed > 3800)
      current_motor_speed = 500;
    control_motor(true, current_motor_speed);
    Serial.print("Running motor with speed: ");
    Serial.println(current_motor_speed);


    // testsound - mag sehr aetzend klingen, gerne aendern
    if(!digitalRead(SPEAKER_PIN))
      analogWrite(SPEAKER_PIN, (int)random(50, 4000));
    else
      digitalWrite(SPEAKER_PIN, 0);
    delay(DEFAULT_DELAY);
  }
  // if finger is no longer on sensor, turn leds off
  else{
    clear_next_led();
    current_motor_speed = 0;
    control_motor(false, current_motor_speed);
    digitalWrite(SPEAKER_PIN, 0);
    delay(DEFAULT_DELAY);
  }
}
