from random import choice, randint, random, uniform
import os

import helpers
from user import User
import userTypes

nicksPerUser = 3
minNickLenght = 6
lowercaseNickProbability = 0.5

# user/host source files:
userfileName = os.path.join(os.path.dirname(__file__), 'users.txt')
prefixfileName = os.path.join(os.path.dirname(__file__), 'adjectives.txt')
nounfileName = os.path.join(os.path.dirname(__file__), 'nouns.txt')
placesfileName = os.path.join(os.path.dirname(__file__), 'places.txt')

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

    def _chooseNick(self, generator, startListLen):
        # returns nick from list of possible starting words removes punctuation from nick
        return generator.messageStartList[randint(0, startListLen - 1)][0].translate(helpers.removePunctuationMap)

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
        startListLen = len(generator.messageStartList)

        self.users = []
        nicks = []

        # generate list of possible nicks
        for i in range(0, self.userCount * nicksPerUser):
            # choose nick from list of possible starting words, remove punctuation from nick
            nick = self._chooseNick(generator, startListLen)
            # make sure nick isn't in nicks and of some lenght
            while (nick.lower() in [nick.lower() for nick in nicks]) or (len(nick) < minNickLenght):
                nick = self._chooseNick(generator, startListLen)

            # make some of them lowercase
            if random() < lowercaseNickProbability:
                nick = nick.lower()
            else:
                pass
            nicks.append(nick)

        # load lists for username and hostmask generation
        userList = helpers.splitFileToList(userfileName)
        prefixList = helpers.splitFileToList(prefixfileName)
        nounList = helpers.splitFileToList(nounfileName)
        placesList = helpers.splitFileToList(placesfileName)

        # lists used to prevent the same username/hostmask appearing twice
        userNames = []
        hostmasks = []

        self.offline = []
        self.online = []

        inverseTotal = sum(1 / n for n in range(1, self.userCount + 1))

        # choose values for each user, create user and append to users
        for i in range(0, self.userCount):
            # choose username
            userName = choice(userList)
            while userName in userNames:
                userName = choice(userList)
            userNames.append(userName)

            # choose hostmask
            hostmask = self._joinHostmask(choice(prefixList), choice(nounList), choice(placesList))
            while hostmask in hostmasks:
                hostmask = self._joinHostmask(choice(prefixList), choice(nounList), choice(placesList))
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