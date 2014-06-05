import datetime
import helpers
import userTypes

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

    def process(self):
        if self.kickee.isOnline and self.kicker.isOnline:
            self.channel.setOffline(self.kickee)
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

    def process(self):
        if self.user.isOnline:
            self.channel.setOffline(self.user)
            return "{0}left #{1} [{2}]\n".format(self._generateJLQBeginning(), self.channel.name, self.reason)

class QuitEvent(JLQEvent):
    def __init__(self, date, user, reason, channel):
        self.date = date
        self.user = user
        self.reason = reason
        self.channel = channel

    def process(self):
        if self.user.isOnline:
            self.channel.setOffline(self.user)
            return "{0}quit [{1}]\n".format(self._generateJLQBeginning(), self.reason)

class JoinEvent(JLQEvent):
    def __init__(self, date, user, channel):
        self.date = date
        self.user = user
        self.channel = channel

    def process(self):
        if not self.user.isOnline:
            self.channel.setOnline(self.user)
            return "{0}joined #{1}\n".format(self._generateJLQBeginning(), self.channel.name)

class MessageEvent(Event):
    def __init__(self, date, user, message):
        self.date = date
        self.user = user
        self.message = message

    def process(self):
        if self.user.isOnline:
            return "{0} < {1}> {2}\n".format(self._generateTime(), self.user.nick, self.message)

class UserActionEvent(Event):
    def __init__(self, date, user, action):
        self.date = date
        self.user = user
        self.action = action

    def process(self):
        if self.user.isOnline:
            return "{0}  * {1} {2}\n".format(self._generateTime(), self.user.nick, self.action)
