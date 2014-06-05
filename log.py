import datetime
import helpers
import userTypes
from random import choice
from math import sin, pi

# abbreviations of weekdays and months
days = ['Mon', 'Tue', 'Wed', 'Thu','Fri', 'Sat', 'Sun']
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

class Log(object):
    def __init__(self, fileObjectList):
        self.lfs = fileObjectList
        self.totalLines = 0

    def write(self, line):
        for lf in self.lfs:
            lf.write(line)
        self.totalLines += 1

    def _zf(self, arg):
        # zfills string to given argument
        return str(arg).zfill(2)

    def _generateFullTimeStamp(self, date):
        return "{0} {1} {2} {3}:{4}:{5} {6}".format(days[date.weekday()],
                                                    months[date.month - 1],
                                                    self._zf(date.day),
                                                    self._zf(date.hour),
                                                    self._zf(date.minute),
                                                    self._zf(date.second),
                                                    str(date.year))

    # TODO: make events as well?
    def writeLogOpening(self, date):
        self.write("--- Log opened {0}\n".format(self._generateFullTimeStamp(date)))

    def writeLogClosing(self, date):
        self.write("--- Log closed {0}\n".format(self._generateFullTimeStamp(date)))

    def writeDayChange(self, date):
        self.write("--- Day changed {0} {1} {2} {3}\n".format(days[date.weekday()],
                                                               months[date.month - 1],
                                                               self._zf(date.day),
                                                               str(date.year)))
