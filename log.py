import datetime
import helpers
import userTypes
from random import choice
from math import sin, pi

# abbreviations of weekdays and months
days = ['Mon', 'Tue', 'Wed', 'Thu','Fri', 'Sat', 'Sun']
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# TODO: create a function that simulates this behavior with fluid numbers after being given a general activity.
# TODO: tweak activity: currently 1,000,000 lines go from May 29 2014 to Apr 05 2023
# possible timedeltas after messages
timeSpan = [5, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 10, 10, 10, 10, 12, 15, 20, 30, 30, 30, 20, 60, 120, 300, 600, 1200, 2400]

class Log(object):
    def __init__(self, fileObjectList):
        self.lfs = fileObjectList
        self.totalLines = 0

        # TODO: move to channel later??
        # get current date
        self.date = datetime.datetime.now()

    def _write(self, line):
        for lf in self.lfs:
            lf.write(line)

    def _incrementLine(self):
        self.totalLines += 1

        # TODO: move to main() as local when events are implemented?
        # TODO: += ???
        self.date = self.date + datetime.timedelta(seconds = choice(timeSpan) * (sin((self.date.hour + 12) * pi / 24) + 1.5))

    def _flavourText(self, text, flavourType):
        # returns text with 'flavour'
        if flavourType == userTypes.lowercaseNoPunctuation:
            return text.translate(helpers.removePunctuationAndUpperCaseMap)
        elif flavourType == userTypes.standard:
            return text
        elif flavourType == userTypes.lowercase:
            return text.lower()
        elif flavourType == userTypes.uppercase:
            return text.upper()
        elif flavourType == userTypes.noPunctuation:
            return text.translate(helpers.removePunctuationMap)
        elif flavourType == userTypes.txtSpeech:
            return text.translate(helpers.noVocalMap)
        else:
            return "ERROR: false flavourType assigned"

    def _zf(self, arg):
        # zfills string to given argument
        return str(arg).zfill(2)

    def _generateTime(self):
        return ':'.join([self._zf(self.date.hour), self._zf(self.date.minute)])

    def _generateJLQBeginning(self, user):
        # generates beginning of join/leave/quit message
        return "{0} -!- {1} [{2}] has ".format(self._generateTime(),
                                               user.nick,
                                               user.combinedUserAndHost)

    def writeQuit(self, user, reason):
        self._write("{0}quit [{1}]\n".format(self._generateJLQBeginning(user), reason))
        self._incrementLine()

    def writeLeave(self, user, channelName, reason):
        self._write("{0}left #{1} [{2}]\n".format(self._generateJLQBeginning(user), 
                                                  channelName, 
                                                  reason))
        self._incrementLine()

    def writeJoin(self, user, channelName):
        # writes join message to log
        self._write("{0}joined #{1}\n".format(self._generateJLQBeginning(user),
                                              channelName))
        self._incrementLine()

    def writeKick(self, kickee, kicker, channelName, reason):
        self._write("{0} -!- {1} was kicked from #{2} by {3} [{4}]\n".format(self._generateTime(), 
                                                                             kickee.nick, 
                                                                             channelName, 
                                                                             kicker.nick, 
                                                                             reason))
        self._incrementLine()

    def writeMessage(self, user, message):
        # TODO: OP/Half-OP/Voice symbols
        self._write("{0} < {1}> {2}\n".format(self._generateTime(),
                                              user.nick,
                                              self._flavourText(message, user.userType)))
        self._incrementLine()

    def writeAction(self, user, action):
        self._write("{0}  * {1} {2}\n".format(self._generateTime(),
                                              user.nick, action))
        self._incrementLine()

    def _generateFullTimeStamp(self):
        return "{0} {1} {2} {3}:{4}:{5} {6}".format(days[self.date.weekday()],
                                                    months[self.date.month - 1],
                                                    self._zf(self.date.day),
                                                    self._zf(self.date.hour),
                                                    self._zf(self.date.minute),
                                                    self._zf(self.date.second),
                                                    str(self.date.year))

    def writeLogOpening(self):
        self._write("--- Log opened {0}\n".format(self._generateFullTimeStamp()))
        self._incrementLine()

    def writeLogClosing(self):
        self._write("--- Log closed {0}\n".format(self._generateFullTimeStamp()))
        self._incrementLine()

    def writeDayChange(self):
        self._write("--- Day changed {0} {1} {2} {3}\n".format(days[self.date.weekday()],
                                                               months[self.date.month - 1],
                                                               self._zf(self.date.day),
                                                               str(self.date.year)))
        self._incrementLine()
