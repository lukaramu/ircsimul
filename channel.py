from math import sin, pi
from random import choice, randint, random

import helpers
from user import User
import userTypes

nicksPerUser = 3
minNickLenght = 6
lowercaseNickProbability = 0.5

# user/host source files:
userfileName = 'users.txt'
prefixfileName = 'adjectives.txt'
nounfileName = 'nouns.txt'
placesfileName = 'places.txt'

# probabilities for various user types
lowercaseNoPunctuationUserProbability = 0.4                                 # type 0
standardUserProbability = 0.22 + lowercaseNoPunctuationUserProbability      # type 1
lowercaseUserProbability = 0.15 + standardUserProbability                   # type 2
uppercaseUserProbability = 0.1 + lowercaseUserProbability                   # type 3
noPunctuationUserProbability = 0.05 + uppercaseUserProbability              # type 4
txtSpeechUserProbability = 0.08 + noPunctuationUserProbability              # type 5

class Channel(object):
    def _chooseNick(self, generator, startListLen):
        # returns nick from list of possible starting words removes punctuation from nick
        return generator.startList[randint(0, startListLen - 1)][0].translate(helpers.removePunctuationMap)

    def _joinHostmask(self, prefix, noun, place):
        # returns combined hostmask
        strList = []
        strList.append(prefix)
        strList.append(noun)
        strList.append("from")
        strList.append(place)
        return '.'.join(strList)

    # TODO: make it possible to create additional users later?
    def loadUsers(self, generator):
        # load nicks from startList items, as they all have a uppercase starting letter
        # depends on startList already being generated
        startListLen = len(generator.startList)

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
            # TODO: beautify (i.e. create a function for this type of selection? only if faster)
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
            # TODO: find better activity distribution
            activity = (sin(random() * pi) + 1) / 2

            # create User object, append to global user list
            # user is initially offline
            user = User(i, userName, hostmask, userNicks, userType, activity, False)
            self.users.append(user)
            self.offline.append(user)

        # TODO: move to channel class later
        self.onlineUsers = 0

        # sums of activity numbers for weighted choice
        # TODO: move to channel class later (might not be necessary b/c of rework w/ events and such)
        self.activityTotal = sum(user.activity for user in self.users)
        self.offlineActivityTotal = self.activityTotal
        self.onlineActivityTotal = 0

    def __init__(self, name, generator, userCount):
        self.name = name
        self.userCount = userCount
        self.loadUsers(generator)
