#!/usr/bin/python3
input_tty='/dev/ttyS0'
import serial

port = serial.Serial(input_tty, baudrate=9600)

while True:
  byte=port.read_until(b'\x03',1000)
  byte_checksum1=port.read(1)
  print('Received: ', byte,byte_checksum1)
  port.write(b'\x06')

