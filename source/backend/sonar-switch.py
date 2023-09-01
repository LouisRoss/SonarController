import sys
import os
import json
import serial

configurationpath = '/sonar/configuration/'


class SonarCommChannel:
  """ First, define a class to encapsulate the serial port transaction
      plus formatting the command from parameters.
  """
  def __init__(self):
    pass

  def __enter__(self):
    self.ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, bytesize=8, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
    self.ser.timeout = 2


  def __exit__(self, *args):
    self.ser.close()


  def send_switch(self, command):
    sent_count = self.ser.write(command)
    self.ser.flush()
    if sent_count != len(command):
      print('Sent ' + str(sent_count) + ' bytes, but should have sent ' + len(command))

    read_data = self.ser.read_until(b'\xfc')
    #print('Read ' + str(read_data) + ' from sonar')

    return read_data


  def create_switch_command(self, sonar_range, gain, logf, absorption, sector_width, train_angle, step_size, pulse_length, data_points, profile, calibrate, frequency):
    command=bytearray(27)

    # Switch data header
    command[0] = bytearray.fromhex('fe')[0]
    command[1] = bytearray.fromhex('44')[0]

    command[2] = 16                          # Head ID
    command[3] = sonar_range                 # Range
    command[4] = 0                           # Reserved, must be 0
    command[5] = 0                           # Rev / hold
    command[6] = bytearray.fromhex('43')[0]  # Master / Slave (always slave)
    command[7] = 0                           # Reserved, must be 0

    command[8] = gain                        # Start Gain
    command[9] = logf                        # Logf (0=10dB 1=20dB 2=30dB 3=40dB)
    command[10] = absorption                 # Absorption dB per m * 100 - Do not use a value of 253 (\xfd)
    command[11] = train_angle                # (Train angle in degrees + 180) / 3 - 60 is 0 degrees
    command[12] = sector_width               # Sector width in 3-degree steps - 60 is 180 degrees
    command[13] = step_size                  # Step size (0 to 8 in 0.3-degree steps) - 4 is 1.2 degrees/step
    command[14] = pulse_length               # Pulse length 1-100 -> 10 to 1000 usec in 10-usec increments - usec / 10
    command[15] = 0                          # Profile Minimum Range: 0-250 -> 0 to 25 meters in 0.1-meter increments

    command[16] = 0                          # Reserved, must be 0
    command[17] = 0                          # Reserved, must be 0
    command[18] = 0                          # Reserved, must be 0
    command[19] = data_points                # 25 - 250 data points returned, header 'IMX'   50 - 500 data points returned, header 'IGX'
    command[20] = 8                          # 4, 8, 16: resolution.  8 is 8-bit data, one sample per byte.
    command[21] = bytearray.fromhex('06')[0] # up baud: \x0b 9600, \x03 14400, \x0c 19200, \x04 28800, \x02 38400, \x05 57600, \x06 115200
    command[22] = profile                    # 0 - off, 1 = on
    command[23] = calibrate                  # calibrate, 0 = off, 1 = on

    command[24] = 1                          # Switch delay 0-255 in 2-msec increments - Do not use value of 253 (\fd)
    command[25] = frequency                  # 0-200 in (kHz - 675)/5 + 100 - 175kHz-1175kHz in 5kHz increments

    # Termination byte
    command[26] = bytearray.fromhex('fd')[0]

    return command


# Actual script entry point.  Parse arguments, create an instance of the SonarCommChannel class,
# do the transaction.
# 1. If a file name is suplied, append the raw response to the file.
# 2. Parse the response into a json object and return it on stdout.
#
if len(sys.argv) < 2:
  print('Usage: ' + sys.argv[0] +  ' <sonar parameter object> <optional capture file name> <optional loop count>')
  exit(1)

parameters_cmd = sys.argv[1]
parameters = json.loads(parameters_cmd)

filepath = ''
if len(sys.argv) > 2:
  filepath = sys.argv[2]

loop_count = 1 
if len(sys.argv) > 3:
  loop_count = int(sys.argv[3])

sonar_range = parameters['range']
gain = parameters['gain']
logf = int(parameters['logf']/10) - 1
absorption = int(parameters['absorption'] * 100)
sector_width = int(parameters['sector_width'] / 3)
train_angle = int((parameters['train_angle'] + 180) / 3)
step_size = int(parameters['step_size'] * 10 / 3)
pulse_length = int(parameters['pulse_length'] / 10)
data_points = int(parameters['data_points'] / 10)
profile = parameters['profile']
calibrate = parameters['calibrate']
frequency = int((parameters['frequency'] - 675) / 5) + 100
#print('range: ' + str(sonar_range) + ' gain: ' + str(gain) + ' logf: ' + str(logf) + ' absorption: ' + str(absorption) + ' pulse_length: ' + str(pulse_length) + ' data_points: ' + str(data_points) + ' profile: ' + str(profile) + ' frequncy: ' + str(frequency))

sonar = SonarCommChannel()
command = sonar.create_switch_command(sonar_range=sonar_range, 
                                      gain=gain, 
                                      logf=logf, 
                                      absorption=absorption, 
                                      sector_width = sector_width,
                                      train_angle = train_angle,
                                      step_size = step_size,
                                      pulse_length=pulse_length, 
                                      data_points=data_points, 
                                      profile=profile, 
                                      calibrate=calibrate,
                                      frequency=frequency)

with sonar:
  for _ in range(loop_count):
    sonar_data = sonar.send_switch(command)
    # print(sonar_data)
    response = {}
    if sonar_data:
      # If we got data and a file path was specified, write the raw binary data.
      if filepath:
        if os.path.exists(filepath):
          append_write = 'a'
        else:
          append_write = 'w'
        with open(filepath, append_write + 'b') as file:
          file.write(sonar_data)

      # Convert raw binary response to engineering units, pack in response object.
      response["header"] = sonar_data[0:3].decode('utf-8')
      response["headid"] = sonar_data[3]
      response["serialstatus"] = sonar_data[4]
      response["stepdirection"] = 1 if sonar_data[6] & 64 else 0
      response["headpos"] = (((sonar_data[6] & 63) << 7 | (sonar_data[5] & 127)) - 600) * 0.3
      response["comment"] = "Computing head position " + str(response["headpos"]) + " from byte 5=" + str(sonar_data[5]) + " and 6=" + str(sonar_data[6])
      response["range"] = sonar_data[7]
      response["profilerange"] = sonar_data[9] << 7 | sonar_data[8] & 127
      response["databytes"] = sonar_data[11] << 7 | sonar_data[10] & 127
      data = ""
      for val in sonar_data[12:-1]:
        data += "{0:02x}".format(val)
      response["data"] = data
    else:
      # No response, don't write to file, pack dummy data in response object.
      response["header"] = "DUM"
      response["headid"] = 16
      response["serialstatus"] = 65
      response["stepdirection"] = 1
      response["headpos"] = 4.3
      response["range"] = 42
      response["profilerange"] = 192
      response["databytes"] = 500
      response["comment"]="No response from sonar"
      data = ""
      for i in range(250):
        data += "{0:02x}".format(i)
      for i in range(250):
        data += "{0:02x}".format(250 - i)
      response["data"] = data

  # Single-step requests want the response back on stdout
  if loop_count == 1:
    print(json.dumps(response))

