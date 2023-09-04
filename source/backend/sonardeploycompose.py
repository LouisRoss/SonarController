import sys
import os
import json
import time
import math
import threading
from sonarcommchannel import SonarCommChannel
from sonardeploy import SonarDeploy

configurationpath = '/sonar/configuration/'
logPathRoot = '/sonar/log/'
logFilePath = logPathRoot + 'default/'
logFile = logFilePath + 'default.log'
debug_mode = True

result = { 'success': False, 'message': 'Unknown error' }

def emit_status(message):
  """ TODO - figure out a way to pass status to the web service,
             probably through an API call.
  """
  global logFile
  global debug_mode

  utcDateTime = time.gmtime()
  timestamp = "{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}".format(year=utcDateTime.tm_year, month=utcDateTime.tm_mon, day=utcDateTime.tm_mday, hour=utcDateTime.tm_hour, minute=utcDateTime.tm_min, second=utcDateTime.tm_sec)

  if debug_mode:
    print(timestamp + ': ' + message)

  with open(logFile, "a") as outfile:
    outfile.write(timestamp + ': ' + message + '\n')



def makeNewLogFolder():
  global logFilePath
  global logFile

  utcDateTime = time.gmtime()
  log_folder = "{year:04d}-{month:02d}-{day:02d}_{hour:02d}:{minute:02d}:{second:02d}".format(year=utcDateTime.tm_year, month=utcDateTime.tm_mon, day=utcDateTime.tm_mday, hour=utcDateTime.tm_hour, minute=utcDateTime.tm_min, second=utcDateTime.tm_sec)
  logFilePath = logPathRoot + log_folder + '/'
  if not os.path.exists(logFilePath):
      os.makedirs(logFilePath)

  logFile = logFilePath + "sonar.log"
  with open(logFile, "w") as outfile:
    outfile.write('Start of log file ' + log_folder + '\n')



class SonarDeployCompose:
  def __init__(self, configurationName, debug=False):
    global debug_mode

    self.configurationName = configurationName
    self.configuration = {}
    
    debug_mode = debug

    makeNewLogFolder()

    fullpathname = configurationpath + configurationName + ".json"
    if not os.path.isfile(fullpathname):
      emit_status('Configuration file ' + fullpathname + ' does not exist')
      exit(503)

    with open(fullpathname, 'r') as configfile:
      self.configuration = json.load(configfile)


  def delay_start(self):
    delay_minutes = float(self.configuration['deployment']['minutes'])
    delay_seconds = int(delay_minutes * 60)

    emit_status('Waiting for ' + str(delay_seconds) + ' seconds')
    for _ in range(delay_seconds):
      time.sleep(1)
    emit_status('Done waiting ' + str(delay_seconds) + ' seconds')

  def downwardStep(self, deployer, period, count):
    if count == 0:
      emit_status('')
      emit_status('Downward(' + self.configurationName + ') being skipped')
      return False

    deployer.makeNewDataFolder()

    for iteration in range(count): 
      emit_status('')
      emit_status('Downward(' + self.configurationName + ') ' + str(iteration + 1) + ' of '  + str(count) + ' for ' + str(period) + ' seconds')
      result = deployer.doSonarStep()
      if result['success']:
        emit_status('Downward(' + self.configurationName + ') ' + str(iteration + 1) + ' of ' + str(count) + ' completed with ' + str(result['response']['count']) + ' steps')
      else:
        emit_status('Error during downward(' + str(self.configurationName) + ': ' + result['message'])

      time.sleep(period)

  def scanStep(self, deployer, period, count):
    if count == 0:
      emit_status('')
      emit_status('Scan(' + self.configurationName + ') being skipped')
      return False

    deployer.makeNewDataFolder()

    for iteration in range(count): 
      emit_status('')
      emit_status('Scan(' + self.configurationName + ') '  + str(iteration + 1) + ' of ' + str(count) + ' for ' + str(period) + ' seconds')
      result = deployer.doSonarScan()
      if result['success']:
        emit_status('Scan(' + self.configurationName + ') ' + str(iteration + 1) + ' of ' + str(count) + ' completed with ' + str(result['response']['count']) + ' steps')
      else:
        emit_status('Error during scan(' + str(self.configurationName) + ': ' + result['message'])

      time.sleep(period)



  def compose_and_deploy(self):
    sonar = SonarCommChannel()
    with sonar:
      deployer = SonarDeploy(sonar, self.configurationName, self.configuration, emit_status)

      # All times in seconds.
      downwardSamplingTime = self.configuration['deployment']['downwardsamplingtime'] * 60
      downwardSamplePeriod = self.configuration['downward']['sampleperiod']
      scanSamplingTime = self.configuration['deployment']['scansamplingtime'] * 60
      scanSamplePeriod = self.configuration['scan']['sampleperiod']

      emit_status('Composing downward sample time ' + str(downwardSamplingTime) + ' period ' + str(downwardSamplePeriod) + ', scan sample time ' + str(scanSamplingTime) + ' period ' + str(scanSamplePeriod))
      downwardCount = 0
      if downwardSamplingTime > 0 and downwardSamplePeriod > 0:
        downwardCount = math.ceil(downwardSamplingTime / downwardSamplePeriod)

      scanCount = 0
      if scanSamplingTime > 0 and scanSamplePeriod > 0:
        scanCount = math.ceil(scanSamplingTime / scanSamplePeriod)

      emit_status('Composing downward count ' + str(downwardCount) + ' sample period ' + str(downwardSamplePeriod) + '  scan count ' + str(scanCount) + ' sample period ' + str(scanSamplePeriod))

      self.delay_start()

      while True:
        self.downwardStep(deployer, downwardSamplePeriod, downwardCount)
        self.scanStep(deployer, scanSamplePeriod, scanCount)


