class User(object):
    def __init__(self, ID, username, hostmask, nicks, userType, activity, isOnline):
        self.ID = ID
        self.username = username
        self.hostmask = hostmask
        self.nicks = nicks
        self.userType = userType
        self.activity = activity
        self.isOnline = isOnline

        self.nick = nicks[0]
        # TODO: do this:
        self.combinedUserAndHost = '@'.join([username, hostmask])
