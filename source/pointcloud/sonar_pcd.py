import sys
import os
import math
import csv
from generate_pcd import PCDGenerator

class SonarPCD:
    def __init__(self, path, scannumber=0):
        self.path = path
        self.scannumber = scannumber
        self.index = []
        self.currentIndex = 0
        self.firstPing = True
        self.firstHeadPos = 0.0
        self.pcdLine = []
        self.maxperiod = 2
        self.period = self.maxperiod
        self.depthbias = 0.0
        self.depthbiasdelta = 0.1
        self.headpositions = []

    def __enter__(self):
        #self.pcdGenerator = PCDGenerator(os.path.join(self.path, 'sonar881.pcd'), 0)
        if self.scannumber == 0:
            self.pcdGenerator = PCDGenerator(os.path.join(self.path, 'sonar881.pcd'), 0)
        else:
            self.pcdGenerator = PCDGenerator(os.path.join(self.path, f'sonar881_{self.scannumber}.pcd'), 0)

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
        header['stepdirection'] = ' cw' if (pingHeader[6] & 0x40) != 0 else 'ccw'
        header['range'] = pingHeader[7]
        header['profilerange'] = pingHeader[9] << 7 | pingHeader[8] & 0x7f
        header['databytes'] = pingHeader[11] << 7 | pingHeader[10] & 0x7f

        if self.firstPing:
            self.firstHeadPos = header['headposition']
            self.firstPing = False

        return header
    
    def CreatePoint(self, cosine, sine, header, distance, intensity):
        #print('Creating point for angle ' + str(header['headposition']) + ', distance ' + str(distance))
        xPos = distance * cosine
        zPos = distance * sine
        #if intensity > 3:
        #self.pcdLine.append([xPos, self.currentIndex, zPos, (int)(intensity), (int)(intensity + self.depthbias), (int)(intensity + self.depthbias), 0])
        self.pcdLine.append([xPos, self.currentIndex, zPos, (int)(intensity/2), (int)(intensity), (int)(intensity*2), 0])
        #else:
        #    self.pcdLine.append([xPos, self.currentIndex, zPos, 0, 0, 0, 0])

    def ReadPingData(self, dataFile):
        pingHeader = dataFile.read(12)
        if not pingHeader or len(pingHeader) < 12:
            return False
        
        header = self.ParsePingHeader(pingHeader)
        self.headpositions.append(f"{header['headposition']: >5.1f} {header['stepdirection']}")
        radians = header['headposition'] * math.pi / 180.0
        cosine = math.cos(radians)
        sine = math.sin(radians)

        pingData = dataFile.read(header['databytes'] + 1)  # Don't forget the 0xfc terminator.
        for pointIndex in range(len(pingData)-1):
            #self.period -= 1
            #if self.period == 0:
            #    self.period = self.maxperiod
                intensity = pingData[pointIndex] if pointIndex >= 120 else 0
                if header['headposition'] == self.firstHeadPos:
                    intensity = 255
                self.CreatePoint(cosine, sine, header, pointIndex, intensity)

        self.firstPing = False
        return True

    def ReadSonarData(self, dataFileName):
        print('Reading sonar pings in file ' + dataFileName)
        self.headpositions = []
        dataPath = os.path.join(self.path, dataFileName)
        with open(dataPath, 'rb') as dataFile:
            self.firstPing = True
            while self.ReadPingData(dataFile):
                pass

        print(f'{len(self.headpositions)} scans:')
        breakcount = 0
        for headpos in self.headpositions:
            print(headpos, end=' ')
            breakcount += 1
            if breakcount >= 15:
                print()
                breakcount = 0
        print()
        self.pcdGenerator.AddLine(self.pcdLine)
        self.pcdLine = []
        self.depthbias += self.depthbiasdelta

    def MakePCD(self):
        self.ReadIndex()

        for scanOrDownward in self.index:
            self.currentIndex += 1
            if (self.scannumber == 0) or (self.scannumber == self.currentIndex):
                self.ReadSonarData(scanOrDownward[2])

        self.pcdGenerator.WritePCD()

path = "./"
scannumber = 0
if len(sys.argv) > 1:
    path = sys.argv[1]
if len(sys.argv) > 2:
    scannumber = int(sys.argv[2])
with SonarPCD(path, scannumber) as pcd:
    pcd.MakePCD()
