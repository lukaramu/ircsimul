from random import choice, randint, random, uniform
import sys

import helpers
from user import User
import userTypes

nicksPerUser = 3
minNickLenght = 6
lowercaseNickProbability = 0.5

# probabilities for various user types
lowercaseNoPunctuationUserProbability = 0.4                                 # type 0
standardUserProbability = 0.22 + lowercaseNoPunctuationUserProbability      # type 1
lowercaseUserProbability = 0.15 + standardUserProbability                   # type 2
uppercaseUserProbability = 0.1 + lowercaseUserProbability                   # type 3
noPunctuationUserProbability = 0.05 + uppercaseUserProbability              # type 4
txtSpeechUserProbability = 0.08 + noPunctuationUserProbability              # type 5

class Channel(object):
    def __init__(self, name, generator, userCount):
        self.name = name
        self.userCount = userCount
        self.loadUsers(generator)
        self.day = 0

    def _joinHostmask(self, prefix, noun, place):
        # returns combined hostmask
        strList = []
        strList.append(prefix)
        strList.append(noun)
        strList.append("from")
        strList.append(place)
        return '.'.join(strList)

    # TODO: make it possible to create additional users later?
    # TODO: move some of the property generation to User object initialization
    def loadUsers(self, generator):
        # load nicks from startList items, as they all have a uppercase starting letter
        # depends on startList already being generated
        nicks = []
        lowerList = []
        for start in generator.messageStartList:
            if start[0].lower() not in lowerList and len(start[0]) >= minNickLenght:
                lowerList.append(start[0].lower())
                if random() < lowercaseNickProbability:
                    nicks.append(start[0].lower())
                else:
                    nicks.append(start[0])

        maxUsers = int(len(nicks) / nicksPerUser)

        if self.userCount > maxUsers:
            sys.stderr.write("WARNING: Number of users too big for number of possible nicknames.\n")
            sys.stderr.write("         Generating {0} users instead\n".format(str(maxUsers)))
            self.userCount = maxUsers

        self.users = []

        # lists used to prevent the same hostmask appearing twice
        hostmasks = []

        self.offline = []
        self.online = []

        inverseTotal = sum(1 / n for n in range(1, self.userCount + 1))

        # choose values for each user, create user and append to users
        for i in range(0, self.userCount):
            # choose username
            userName = choice(helpers.userList)

            # choose hostmask
            hostmask = self._joinHostmask(choice(helpers.prefixList), choice(helpers.nounList), choice(helpers.placesList))
            while hostmask in hostmasks:
                hostmask = self._joinHostmask(choice(helpers.prefixList), choice(helpers.nounList), choice(helpers.placesList))
            hostmasks.append(hostmask)

            # create list of possible nicks for user from list of overall possible nicks
            userNicks = []
            for j in range(0, nicksPerUser):
                userNicks.append(nicks.pop())

            # choose user type
            determineType = random()
            if determineType < lowercaseNoPunctuationUserProbability:
                userType = userTypes.lowercaseNoPunctuation
            elif determineType < standardUserProbability:
                userType = userTypes.standard
            elif determineType < lowercaseUserProbability:
                userType = userTypes.lowercase
            elif determineType < uppercaseUserProbability:
                userType = userTypes.uppercase
            elif determineType < noPunctuationUserProbability:
                userType = userTypes.noPunctuation
            elif determineType < txtSpeechUserProbability:
                userType = userTypes.txtSpeech

            # choose activity level
            activity = 1 / (i + 1) / inverseTotal * 2

            # create User object, append to global user list
            # user is initially offline
            user = User(i, userName, hostmask, userNicks, userType, activity, False, generator)
            self.users.append(user)
            self.offline.append(user)

        self.onlineUsers = 0

        # sums of activity numbers for weighted choice
        self.activityTotal = sum(user.activity for user in self.users)
        self.offlineActivityTotal = self.activityTotal
        self.onlineActivityTotal = 0

    def setOnline(self, user):
        if user in self.offline:
            self.online.append(user)
            self.offline.remove(user)
            user.isOnline = True

            self.onlineActivityTotal += user.activity
            self.offlineActivityTotal -= user.activity
            self.onlineUsers += 1

    def setOffline(self, user):
        if user in self.online:
            self.online.remove(user)
            self.offline.append(user)
            user.isOnline = False

            self.onlineActivityTotal -= user.activity
            self.offlineActivityTotal += user.activity
            self.onlineUsers -= 1

    # TODO: remove when obsolete (after events are implemented)
    def _selectUserByActivity(self, userList, total):
        r = uniform(0, total)
        upto = 0
        for user in userList:
            upto += user.activity
            if r <= upto:
                return user

    # TODO: check if still necessary with new event system
    def selectUser(self):
        return self._selectUserByActivity(self.users, self.activityTotal)

    def selectOnlineUser(self):
        return self._selectUserByActivity(self.online, self.onlineActivityTotal)

    def selectOfflineUser(self):
        return self._selectUserByActivity(self.offline, self.offlineActivityTotal)