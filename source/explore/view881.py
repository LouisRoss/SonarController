import sys
import os
import math
import csv

class SonarViewer:
    def __init__(self, path, sampleStart, sampleCount, depth=0):
        self.sampleStart = sampleStart
        self.sampleCount = sampleCount
        self.depth = depth
        self.path = path
        self.index = []
        self.currentIndex = 0
        self.scans = []
        self.maxperiod = 2
        self.period = self.maxperiod
        self.depthbias = 0.0
        self.depthbiasdelta = 0.1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

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
    
    def ReadScanData(self, dataFileName):
        pingpoints = []
        dataPath = os.path.join(self.path, dataFileName)
        with open(dataPath, 'rb') as dataFile:
            done = False
            pingIndex = 0
            while not done:
                pingHeader = dataFile.read(12)
                if not pingHeader or len(pingHeader) < 12:
                    done = True
                else:                
                    header = self.ParsePingHeader(pingHeader)
                    headpos = header['headposition']

                    pingData = dataFile.read(header['databytes'] + 1)  # Don't forget the 0xfc terminator.
                    if pingIndex >= self.sampleStart and pingIndex <= self.sampleStart + self.sampleCount:
                        '''intensitySum = 0
                        for pointIndex in range(len(pingData)-1):
                            intensitySum += pingData[pointIndex]
                        intensityAvg = intensitySum / (len(pingData) - 1)'''
                        intensityAvg = pingData[self.depth]
                        pingpoints.append({"headpos": headpos, "intensity": intensityAvg})
                pingIndex += 1

        return pingpoints

    def DisplayScans(self):
        print(f'{self.sampleStart:7d}', end=' ')
        for i in range(self.sampleCount - 2):
            print("       ", end=' ')
        print(f'{self.sampleStart + self.sampleCount - 1:15d}')

        for scan in self.scans:
            for ping in scan:
                print(f"{ping['headpos']:7.1f}", end=' ')
            print()
            for ping in scan:
                print(f"{ping['intensity']:7.3f}", end=' ')
            print()
            print()

    def CompressScanSubset(self):
        self.ReadIndex()

        for scanOrDownward in self.index:
            if scanOrDownward[1] != 'scan':
                print(f'Skipping file {scanOrDownward[2]}, not scan')
            else:
                self.currentIndex += 1
                self.scans.append(self.ReadScanData(scanOrDownward[2]))

        self.DisplayScans()

path = "./"
startIndex = 0
count = 100
depth = 0
if len(sys.argv) > 1:
    path = sys.argv[1]
if len(sys.argv) > 2:
    startIndex = int(sys.argv[2])
if len(sys.argv) > 3:
    count = int(sys.argv[3])
if len(sys.argv) > 4:
    depth = int(sys.argv[4])
with SonarViewer(path, startIndex, count, depth) as view:
    view.CompressScanSubset()
