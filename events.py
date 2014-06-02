import datetime
import helpers
import userTypes

class Event(object):
    def __init__(self):
        pass

    def _zf(self, arg):
        # zfills string to given argument
        return str(arg).zfill(2)

    # NOW: pass time to event objects
    def _generateTime(self):
        return ':'.join([self._zf(self.date.hour), self._zf(self.date.minute)])

    def _generateJLQBeginning(self):
        # generates beginning of join/leave/quit message
        return "{0} -!- {1} [{2}] has ".format(self._generateTime(),
                                               self.user.nick,
                                               self.user.combinedUserAndHost)

# NOW:
class KickEvent(Event):
    def __init__(self, kickee, kicker, reason, channel):
        pass

# NOW: population check??
class LeaveEvent(Event):
    def __init__(self, user, reason, channel):
        self.user = user
        self.reason = reason
        self.channel = channel
        pass

    def process(self):
        self.channel.setOffline(self.user)
        return "{0}left #{1} [{2}]\n".format(self._generateJLQBeginning(), self.channel.name, self.reason)

# NOW: population check??
class QuitEvent(Event):
    def __init__(self, user, reason, channel):
        self.user = user
        self.reason = reason
        self.channel = channel

    def process(self):
        self.channel.setOffline(self.user)
        return "{0}quit [{1}]\n".format(self._generateJLQBeginning(), self.reason)

# NOW:
class JoinEvent(Event):
    def __init__(self, user, channel):
        self.user = user
        self.channel = channel

    def process(self):
        self.channel.setOnline(user)
        return "{0}joined #{1}\n".format(self._generateJLQBeginning(), self.channel.name)

# NOW:
class MessageEvent(Event):
    def __init__(self, user, message):
        self.user = user
        self.message = message

    def process(self):
        return "{0} < {1}> {2}\n".format(self._generateTime(), self.user.nick)

# NOW:
class UserActionEvent(Event):
    def __init__(self, user, action):
        pass
