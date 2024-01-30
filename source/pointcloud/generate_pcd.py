import os

class PCDGenerator:
    def __init__(self, filename, width):
        self.filename = filename
        self.headerfilename = './__header__.pcd'
        self.datafilename = './__data__.pcd'
        self.version = '.7'
        self.fields = ['x', 'y', 'z', 'rgb']
        self.size = [4, 4, 4, 4]
        self.type = ['F', 'F', 'F', 'F']
        self.count = [1, 1, 1, 1]
        self.width = width
        self.height = 0     # Internal default if no lines are added, change to 1 while writing the file.
        self.viewpoint = [0, 0, 0, 1, 0, 0, 0]
        self.points = self.width * self.height
        self.datatype = "ascii"

        self.pointdata = []
        self.yscale = 5

    def __enter__(self):
        self.data = open(self.datafilename, "w")
        #self.file = open(self.filename, "w")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.data:
            self.data.close()
        #self.file.close()

    def WriteHeader(self):
        with open(self.headerfilename, "w") as headerFile:
            headerFile.write("# .PCD v.7 - Point Cloud Data file format\n")
            headerFile.write("VERSION " + self.version + "\n")
            line = "FIELDS"
            for field in self.fields:
                line += " " + field
            headerFile.write(line + "\n")
            line = "SIZE"
            for size in self.size:
                line += " " + str(size)
            headerFile.write(line + "\n")
            line = "TYPE"
            for type in self.type:
                line += " " + type
            headerFile.write(line + "\n")
            line = "COUNT"
            for count in self.count:
                line += " " + str(count)
            headerFile.write(line + "\n")
            headerFile.write("WIDTH " + str(self.width) + "\n")
            height = 1 if (self.height == 0) else self.height
            print('Writing header height = ' + str(height) + ' because self.height = ' + str(self.height))
            headerFile.write("HEIGHT " + str(height) + "\n")
            line = "VIEWPOINT "
            for view in self.viewpoint:
                line += " " + str(view)
            headerFile.write(line + "\n")
            self.points = self.width * height
            headerFile.write("POINTS " + str(self.points) + "\n")
            headerFile.write("DATA " + self.datatype + "\n")

#    def WritePoints(self):
#        for point in self.pointdata:
#            self.data.write("{:.5f} {:.5f} {:.5f} {:.9e}\n".format(point[0], point[1], point[2], point[3]))

    def WritePCD(self):
        self.WriteHeader()
        #self.WritePoints()
        self.data.close()
        self.data = None
        os.system('rm ' + self.filename)
        os.system('cat ' + self.headerfilename + ' ' + self.datafilename + ' >> ' + self.filename)

    def AddPoint(self, x, y, z, r, g, b, a):
        red = (int)(r)
        if red > 127 or red < 0:
            red = 127
        green = (int)(g)
        if green > 127 or green < 0:
            green = 127
        blue = (int)(b)
        if blue > 127 or blue < 0:
            blue = 127
        alpha = (int)(a) & 0xff
        #print('R={:02x}, G={:02x}, B={:02x}, A={:02x}'.format(red, green, blue, alpha))
        redshift = red << 16
        greenshift = green << 8
        blueshift = blue
        alphashift = alpha
        #print('Shifted R={:08x}, G={:08x}, B={:08x}, A={:08x}'.format(redshift, greenshift, blueshift, alphashift))
        rgba = redshift | greenshift | blueshift
        #print('Shifted R={:08x}, G={:08x}, B={:08x}  Merged={:08x} ({:.9e})'.format(redshift, greenshift, blueshift, rgba, rgba))
        ####self.pointdata.append([x/10, y/10, z/10, rgba])
        self.data.write("{:.5f} {:.5f} {:.5f} {:.9e}\n".format(x, y*self.yscale, z, rgba))

    def AddLine(self, line):
        if self.width == 0:
            self.width = len(line)

        if (self.width != len(line)):
            print('!!Inconsistent line length.  Previous line was ' + str(self.width) + ' points, but new line is ' + str(len(line)))
            return

        self.height += 1
        print('Adding ' + str(len(line)) + ' points in line ' + str(self.height))

        for point in line:
            self.AddPoint(point[0], point[1], point[2], point[3], point[4], point[5], point[6])

def test():
    with PCDGenerator("test.pcd", 3) as pcd:
        pcd.AddPoint(1,2,3, 64,64,120,   0)
        pcd.AddPoint(2,3,1, 127,0,0,     0)
        pcd.AddPoint(3,1,2, 0,1,0,   0)
        pcd.WritePCD()

