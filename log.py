class Log(object):
    def __init__(self, fileObjectList):
        self.lfs = fileObjectList
        self.totalLines = 0

    def flush(self):
        for lf in self.lfs:
            lf.flush()

    def write(self, line):
        for lf in self.lfs:
            lf.write(line)
        self.totalLines += 1
