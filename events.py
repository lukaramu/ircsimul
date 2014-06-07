import datetime
import sys
from random import random

import helpers
import userTypes
from channel import nicksPerUser

rejoinProbability = 0.7
multipleMessagesProbability = 0.03

# cumulative
userActionProbability = 0.01
kickProbability = 0.002 + userActionProbability
nickChangeProbability = 0.0005 + kickProbability

class Event(object):
    def __init__(self):
        pass

    def __lt__(self, other):
        if self.date < other.date:
            return True

    def _zf(self, arg):
        # zfills string to given argument
        return str(arg).zfill(2)

    def _generateTime(self):
        return ':'.join([self._zf(self.date.hour), self._zf(self.date.minute)])

class JLQEvent(Event):
    def __init__(self):
        pass

    def _generateJLQBeginning(self):
        # generates beginning of join/leave/quit message
        return "{0} -!- {1} [{2}] has ".format(self._generateTime(),
                                               self.user.nick,
                                               self.user.combinedUserAndHost)

class KickEvent(Event):
    def __init__(self, date, kickee, kicker, reason, channel):
        self.date = date
        self.kickee = kickee
        self.kicker = kicker
        self.reason = reason
        self.channel = channel

    def process(self, queue):
        if self.kickee.isOnline and self.kicker.isOnline:
            self.channel.setOffline(self.kickee)
            if random() < rejoinProbability:
                # set nextJoin in User
                rejoinTime = self.date + datetime.timedelta(seconds = 5 + 2 * random())
                self.kickee.nextJoin = rejoinTime
                event = JoinEvent(rejoinTime, self.kickee, self.channel)
            else:
                event = JoinEvent(self.kickee.getJoinDate(self.date), self.kickee, self.channel)
            queue.put(event)
            return "{0} -!- {1} was kicked from #{2} by {3} [{4}]\n".format(self._generateTime(), 
                                                                            self.kickee.nick, 
                                                                            self.channel.name, 
                                                                            self.kicker.nick, 
                                                                            self.reason)

class LeaveEvent(JLQEvent):
    def __init__(self, date, user, reason, channel):
        self.date = date
        self.user = user
        self.reason = reason
        self.channel = channel

    # NOW:
    def process(self, queue):
        if self.user.isOnline:
            self.channel.setOffline(self.user)
            queue.put(JoinEvent(self.user.getJoinDate(self.date), self.user, self.channel))
            return "{0}left #{1} [{2}]\n".format(self._generateJLQBeginning(), self.channel.name, self.reason)

class QuitEvent(JLQEvent):
    def __init__(self, date, user, reason, channel):
        self.date = date
        self.user = user
        self.reason = reason
        self.channel = channel

    def process(self, queue):
        if self.user.isOnline:
            self.channel.setOffline(self.user)
            queue.put(JoinEvent(self.user.getJoinDate(self.date), self.user, self.channel))
            return "{0}quit [{1}]\n".format(self._generateJLQBeginning(), self.reason)

class JoinEvent(JLQEvent):
    def __init__(self, date, user, channel):
        self.date = date
        self.user = user
        self.channel = channel

    def process(self, queue):
        if not self.user.isOnline:
            self.channel.setOnline(self.user)
            if self.user.isQuitter:
                event = QuitEvent(self.user.getQuitDate(self.date), self.user, self.user.markovGenerator.generateReason(), self.channel)
            else:
                event = LeaveEvent(self.user.getQuitDate(self.date), self.user, self.user.markovGenerator.generateReason(), self.channel)
            queue.put(event)
            return "{0}joined #{1}\n".format(self._generateJLQBeginning(), self.channel.name)

class MessageEvent(Event):
    def __init__(self, date, user, message, channel, generateNewMessage):
        self.date = date
        self.user = user
        self.message = message
        self.channel = channel
        self.generateNewMessage = generateNewMessage

    def process(self, queue):
        messageDate = self.user.getMessageDate(self.date)
        line = None
        if self.user.isOnline:
            # create line
            line = "{0} < {1}> {2}\n".format(self._generateTime(), self.user.nick, self.message)

            # create special events
            determineSpecialEvent = random()
            if determineSpecialEvent < nickChangeProbability:
                if determineSpecialEvent < kickProbability:
                    if determineSpecialEvent < userActionProbability:
                        # TODO: variable action text
                        # user action event
                        queue.put(UserActionEvent(self.date + datetime.timedelta(seconds = 5 + 2 * random()), self.user, "does action"))
                    else:
                        # kick event
                        queue.put(KickEvent(self.date + datetime.timedelta(seconds = 5 + 2 * random()),
                                            self.channel.selectOnlineUser(),
                                            self.user,
                                            self.user.markovGenerator.generateReason(),
                                            self.channel))
                else:
                    # nick change event
                    queue.put(NickChangeEvent(self.date + datetime.timedelta(seconds = 5 + 2 * random()), self.user))
        else:
            # put date of next message after next join
            if messageDate < self.user.nextJoin:
                intervalNumber = int((self.user.nextJoin - messageDate).total_seconds() / self.user.messageInterval)+1
                messageDate += datetime.timedelta(seconds = intervalNumber * self.user.messageInterval)
        if self.generateNewMessage:
            if random() > multipleMessagesProbability:
                queue.put(MessageEvent(messageDate,
                                       self.user,
                                       helpers.flavourText(self.user.markovGenerator.generateMessage(), self.user),
                                       self.channel,
                                       True))
            else:
                messages = self.user.markovGenerator.generateMessages()
                lenght = len(messages) - 1
                helpers.debugPrint("Generating {0} messages at once\n".format(str(lenght + 1)))
                for i, message in enumerate(messages):
                    if i == lenght:
                        generateMore = True
                    else:
                        generateMore = False
                    queue.put(MessageEvent(messageDate + datetime.timedelta(seconds=i * 2 + 0.5 * random()),
                                           self.user,
                                           helpers.flavourText(message, self.user),
                                           self.channel,
                                           generateMore))
        return line

class UserActionEvent(Event):
    def __init__(self, date, user, action):
        self.date = date
        self.user = user
        self.action = action

    def process(self, queue):
        if self.user.isOnline:
            return "{0}  * {1} {2}\n".format(self._generateTime(), self.user.nick, self.action)

class NickChangeEvent(Event):
    def __init__(self, date, user):
        self.date = date
        self.user = user

    def process(self, queue):
        # TODO: imposters?
        helpers.debugPrint("Nick Change\n")
        if self.user.isOnline:
            oldNick = self.user.nick
            for i, nick in enumerate(self.user.nicks):
                if self.user.nick == nick:
                    self.user.nick = self.user.nicks[(i+1) % nicksPerUser]
                    return "{0} -!- {1} is now known as {2}\n".format(self._generateTime(), oldNick, self.user.nick)
            else:
                helpers.debugPrint("Didn't find nick in user.nicks\n")
