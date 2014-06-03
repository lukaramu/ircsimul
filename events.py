import datetime
import helpers
import userTypes

# NOW: make events check if users are even online/(or, if join, offline)

# NOW: check if pop checks could be made obsolete by having the next join/parts already cached
class Event(object):
    def __init__(self):
        pass

    def _zf(self, arg):
        # zfills string to given argument
        return str(arg).zfill(2)

    # NOW: pass time to event objects
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

# NOW: population check??
class KickEvent(Event):
    def __init__(self, kickee, kicker, reason, channel):
        self.kickee = kickee
        self.kicker = kicker
        self.reason = reason
        self.channel = channel

    def process(self):
        self.channel.setOffline(kickee)
        return "{0} -!- {1} was kicked from #{2} by {3} [{4}]\n".format(self._generateTime(), 
                                                                        self.kickee.nick, 
                                                                        self.channel.name, 
                                                                        self.kicker.nick, 
                                                                        self.reason)

# NOW: population check??
class LeaveEvent(JLQEvent):
    def __init__(self, user, reason, channel):
        self.user = user
        self.reason = reason
        self.channel = channel

    def process(self):
        self.channel.setOffline(self.user)
        return "{0}left #{1} [{2}]\n".format(self._generateJLQBeginning(), self.channel.name, self.reason)

# NOW: population check??
class QuitEvent(JLQEvent):
    def __init__(self, user, reason, channel):
        self.user = user
        self.reason = reason
        self.channel = channel

    def process(self):
        self.channel.setOffline(self.user)
        return "{0}quit [{1}]\n".format(self._generateJLQBeginning(), self.reason)

# NOW: population check??
class JoinEvent(JLQEvent):
    def __init__(self, user, channel):
        self.user = user
        self.channel = channel

    def process(self):
        self.channel.setOnline(user)
        return "{0}joined #{1}\n".format(self._generateJLQBeginning(), self.channel.name)

class MessageEvent(Event):
    def __init__(self, user, message):
        self.user = user
        self.message = message

    def process(self):
        return "{0} < {1}> {2}\n".format(self._generateTime(), self.user.nick, self.message)

class UserActionEvent(Event):
    def __init__(self, user, action):
        self.user = user
        self.action = action

    def process(self):
        self.write("{0}  * {1} {2}\n".format(self._generateTime(),
                                             self.user.nick,
                                             self.action))
