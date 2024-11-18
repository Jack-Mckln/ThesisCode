#include <avr/sleep.h>
#include <avr/power.h>

const int arrLength  = 18;
int n = 0;

// Signal will switch between different horizontal and then vertical halves, spending twice as long on the vertical split

static byte multiplexTop[arrLength] = { 0b00111111, 0b00111111, 0b00111000,
                                        0b00111111, 0b00111111, 0b00110001,
                                        0b00111111, 0b00111111, 0b00100011,
                                        0b00111111, 0b00111111, 0b00000111,
                                        0b00111111, 0b00111111, 0b00001110,
                                        0b00111111, 0b00111111, 0b00011100
                                        };  
static byte multiplexBot[arrLength] = { 0b00000000, 0b00000000, 0b00111000,
                                        0b00000000, 0b00000000, 0b00110001,
                                        0b00000000, 0b00000000, 0b00100011,
                                        0b00000000, 0b00000000, 0b00000111,
                                        0b00000000, 0b00000000, 0b00001110,
                                        0b00000000, 0b00000000, 0b00011100
                                        };


void setup() {
  DDRC  = 0b00111111;   //set pins A0 to A5 as outputs
  PORTC = multiplexTop[0];  //output the TOP[0] signal in all of them

  DDRB  = 0b00111111;  //set pins D8-13 as outputs
  PORTB = multiplexBot[0];  //output the BOT[0] singal (intialise)

  // initialize timer1
  cli();  // disable all interrupts

//set timer0 interrupt at 80kHz
  TCCR0A = 0;// set entire TCCR2A register to 0
  TCCR0B = 0;// same for TCCR2B
  TCNT0  = 0;//initialize counter value to 0
  // set compare match register for 80khz increments
  OCR0A = 199;// 80kHz
  // turn on CTC mode
  TCCR0A |= (1 << WGM01);
  // Set  CS00 bits for 1 prescaler
  TCCR0B |= (1 << CS00);   
  // enable timer compare interrupt
   TIMSK0 |= (1 << OCIE0A);

//set timer1 interrupt at phase change frequency
  TCCR1A = 0;// set entire TCCR1A register to 0
  TCCR1B = 0;// same for TCCR1B
  TCNT1  = 0;//initialize counter value to 0
  // set compare match register for 1hz increments
  OCR1A =  15624;// 1Hz
  // turn on CTC mode
  TCCR1B |= (1 << WGM12);
  // Set CS10,12 bits for 1024 prescaler
  TCCR1B |= (1 << CS10) | (1 << CS12);  
  // enable timer compare interrupt
  TIMSK1 |= (1 << OCIE1A);

sei();//allow interrupts

}//end setup

ISR(TIMER0_COMPA_vect){///toggle timer which switches pins high and low
  PORTC ^= 0b00111111; //invert all the active pins at timer0 frequency
  PORTB ^= 0b00111111;
  
}

ISR(TIMER1_COMPA_vect){//mutiplexing signal: change what pins are being affected in syncn
  PORTC = multiplexTop[n]; //sets the relation between the various pins
  PORTB = multiplexBot[n];
  n++; //Steps through to the next position in the array for the next loop to set the pins as according to the multiplexing
  if (n >= arrLength){
    n=0;
  }
  
}
  



void loop() {
}


