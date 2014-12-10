/*
  3DScan
  This driver controls a easydriver
  H.P.
  Commands are :
  r/R: light right laser
  l/L: light left laser
  t/T: turn
  0: shut off both lasers
  b/B: light both lasers
 */

/* Pinout */
static const int dirPin = 2;
static const int stepPin = 3;
static const int laserLeftPin = 12;
static const int laserRightPin = 13;

/* Delay, in microseconds, to ensure laser state totally changed (on/off time) */
static const int lightDelay = 1;

/* Delay, in microseconds, between each motor half step */
static const int stepDelay = 200;

/* Number of steps for a complete rotation */
static const int totalSteps = 800;

/* Change lasers state */
void laser(bool left, bool right){
  digitalWrite(laserLeftPin, left ? HIGH : LOW);
  digitalWrite(laserRightPin, right ? HIGH : LOW);
  delay(lightDelay);
}

/* Turn platform */
int currentPos = 0;
void turn(int n_steps=1){
  for (; n_steps>0; n_steps--){
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(stepDelay);
    currentPos++;
  }
  currentPos %= totalSteps;
  Serial.print(currentPos);
}

void setup() {
  Serial.begin(9600);
  pinMode(dirPin, OUTPUT);
  digitalWrite(dirPin, HIGH);
  pinMode(stepPin, OUTPUT);
  digitalWrite(stepPin, LOW);
  pinMode(laserLeftPin, OUTPUT);
  pinMode(laserRightPin, OUTPUT);
  laser(false, false);
}

char cmd = 0;
bool ok = true;
void loop() {
  if (Serial.available() > 0){
    ok = true;
    cmd = Serial.read();
    switch (cmd) {
      case '0':
        laser(false, false);
        break;

      case 'b':
      case 'B':
        laser(true, true);
        break;

      case 'l':
      case 'L':
        laser(true, false);
        break;
      case 'r':
      case 'R':
        laser(false, true);
        break;

      case 't':
      case 'T':
        turn();
        break;

      /* Unknow command*/
      default: 
        ok = false;
    }
    /* Echo back if command suceeded */
    if (ok) 
      Serial.println(cmd);
  }      
}
