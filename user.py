from random import random, uniform, choice
import sys
import datetime

probabilities = [1.5 - abs(12-x) / 12 / 288 for x in range(0, 24)]
probabilitySum = sum(probabilities)

messagesPerDay = 10000

# probability a user quits instead of leaving
quitProbability = 0.75

class User(object):
    def __init__(self, ID, username, hostmask, nicks, userType, activity, isOnline, markovGenerator):
        self.ID = ID
        self.username = username
        self.hostmask = hostmask
        self.nicks = nicks
        self.userType = userType
        self.activity = activity
        self.isOnline = isOnline
        self.markovGenerator = markovGenerator
        if random() < quitProbability:
            self.isQuitter = True
        else:
            self.isQuitter = False

        self.nick = nicks[0]
        self.combinedUserAndHost = '@'.join([username, hostmask])
        self.messageInterval = 86400 / self.activity / messagesPerDay

        rand = uniform(0, probabilitySum)
        upto = 0
        for i in range(len(probabilities)):
            upto += probabilities[i]
            if rand < upto:
                self.meanHour = i
                self.joiningHour = (i - 6) % 24
                self.quittingHour = (i + 6) % 24
                break
        else:
            self.meanHour = 12
            self.joiningHour = 6
            self.quittingHour = 18
            sys.stderr.write("Fell through when generating join/quit hours! (This shouldn't happen)\n")

    def getJoinDate(self, date):
        joinTime = datetime.time(choice([(self.joiningHour - 1) % 24, self.joiningHour]), 
                                 choice(list(range(60))),
                                 choice(list(range(60))))
        self.nextJoin = datetime.datetime.combine(date.date(), joinTime)
        if self.nextJoin < date:
            self.nextJoin += datetime.timedelta(days=1)
            return self.nextJoin
        else:
            return self.nextJoin

    def getQuitDate(self, date):
        joinTime = datetime.time(choice([(self.quittingHour - 1) % 24, self.quittingHour]), 
                                 choice(list(range(60))),
                                 choice(list(range(60))))
        self.nextQuit = datetime.datetime.combine(date.date(), joinTime)
        if self.nextQuit < date:
            self.nextQuit += datetime.timedelta(days=1)
            return self.nextQuit
        else:
            return self.nextQuit

    def getMessageDate(self, date):
        delta = datetime.timedelta(seconds = self.messageInterval + uniform(-self.messageInterval/2, 
                                                                             self.messageInterval/2))
        return date + delta
