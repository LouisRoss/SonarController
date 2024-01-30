import os
import math
import csv
from generate_pcd import PCDGenerator

class SonarPCD:
    def __init__(self, path):
        self.path = path
        self.index = []
        self.currentIndex = 0
        self.pcdLine = []
        self.maxperiod = 2
        self.period = self.maxperiod
        self.depthbias = 0.0
        self.depthbiasdelta = 0.1

    def __enter__(self):
        #self.pcdGenerator = PCDGenerator(os.path.join(self.path, 'sonar881.pcd'), 0)
        self.pcdGenerator = PCDGenerator(os.path.join('.', 'sonar881.pcd'), 0)
        self.pcdGenerator.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.pcdGenerator.close()

    def ReadIndex(self):
        indexPath = os.path.join(self.path, 'RunIndex.csv')
        with open(indexPath, newline='') as csvfile:
            indexreader = csv.DictReader(csvfile)
            for row in indexreader:
                self.index.append([row['Time Stamp'], row['Type'], row['File']])
        self.currentIndex = 0

    def ParsePingHeader(self, pingHeader):
        header = {}
        command = pingHeader[:3].decode('utf-8')

        if (command != 'IMX') and (command != 'IGX') and (command != 'IPX'):
            print('Unrecognized command')
            return header

        header['command'] = command
        header['headid'] = pingHeader[3]
        header['firmware'] = 'V5' if (pingHeader[4] & 0x01) != 0 else 'V4'
        header['switches_accepted'] = True if (pingHeader[4] & 0x40) != 0 else False
        header['overrun'] = True if (pingHeader[4] & 0x80) != 0 else False
        header['headposition'] = (((pingHeader[6] & 0x3f) << 7 | (pingHeader[5] & 0x7f)) - 600) * 0.3
        header['stepdirection'] = 'cw' if (pingHeader[6] & 0x40) != 0 else 'ccw'
        header['range'] = pingHeader[7]
        header['profilerange'] = pingHeader[9] << 7 | pingHeader[8] & 0x7f
        header['databytes'] = pingHeader[11] << 7 | pingHeader[10] & 0x7f

        return header
    
    def CreatePoint(self, cosine, sine, header, distance, intensity):
        #print('Creating point for angle ' + str(header['headposition']) + ', distance ' + str(distance))
        xPos = distance * cosine
        zPos = distance * sine
        if intensity > 3:
            self.pcdLine.append([xPos, self.currentIndex, zPos, (int)(intensity), (int)(intensity + self.depthbias), (int)(intensity + self.depthbias), 0])
        else:
            self.pcdLine.append([xPos, self.currentIndex, zPos, 0, 0, 0, 0])

    def ReadPingData(self, dataFile):
        pingHeader = dataFile.read(12)
        if not pingHeader or len(pingHeader) < 12:
            return False
        
        header = self.ParsePingHeader(pingHeader)
        radians = header['headposition'] * math.pi / 180.0
        cosine = math.cos(radians)
        sine = math.sin(radians)

        pingData = dataFile.read(header['databytes'] + 1)  # Don't forget the 0xfc terminator.
        for pointIndex in range(len(pingData)-1):
            self.period -= 1
            if self.period == 0:
                self.period = self.maxperiod
                intensity = pingData[pointIndex] if pointIndex >= 120 else 0
                self.CreatePoint(cosine, sine, header, pointIndex, intensity)

        return True

    def ReadSonarData(self, dataFileName):
        print('Reading sonar pings in file ' + dataFileName)
        dataPath = os.path.join(self.path, dataFileName)
        with open(dataPath, 'rb') as dataFile:
            while self.ReadPingData(dataFile):
                pass

        self.pcdGenerator.AddLine(self.pcdLine)
        self.pcdLine = []
        self.depthbias += self.depthbiasdelta

    def MakePCD(self):
        self.ReadIndex()

        for scanOrDownward in self.index:
            self.currentIndex += 1
            self.ReadSonarData(scanOrDownward[2])

        self.pcdGenerator.WritePCD()

