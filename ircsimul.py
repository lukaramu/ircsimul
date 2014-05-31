import datetime
import logging
import cProfile
import string
from math import sin
from math import pi
from random import choice
from random import random
from random import randint
from random import uniform

from user import User

# TODO: check if activity is still correct
# TODO: (complete) refactor:
# TODO: less globals though objects
# TODO: spread out stuff over multiple files
# TODO: instead of/additionally to truncating lines at commas, spread message out over seperate messages
# TODO: ovent based lines: http://pastebin.com/Nw854kcf
# might be cool: having them ping each other in "conversations" where only the last N messages of the person they are pinging are used in the markov generator so the conversation is "topical"

# new features:
# TODO: nick changes
# TODO: channel modes (o and b)
# TODO: topics
# TODO: bans
# TODO: notices
# TODO: mentions
# TODO: urls
# TODO: log metadata (user activity & preferences)

# TODO: make them say hi sometimes?
# TODO: make kicks have an internal reason
# TODO: extract pprinted metadata

# TODO: different nicks, different behaviour (longshot):
# average word count (if possible)
# average word length (if possible)
# multiple exclamation marks !!!!!!!!!!!!!!
# times dumbfounded (???)
# aloof (doesn't mention often)
# apostrophe uses?
# negativity
# questions asked
# relationships
# variance in mentions
# times mentions i.e. popular
# many times in a row
# changing nicks often
# liking to kick
# being kicked often

# logging.basicConfig(filename='debug.log', level=logging.DEBUG)

# START flags and sizes
# TODO: Make some of them command line arguments?
lineMax = 200000
logfileName = 'ircsimul.log'
sourcefileName = 'ZARATHUSTRA.txt'
reasonsfileName = 'reasons.txt'
channelName = 'channel'
userCount = 40                  # make sure this is less than the number of names in userfileName
nicksPerUser = 3
minNickLenght = 6
minOnline = 5
minOffline = 5
initialPopulation = 10
logInitialPopulation = True

# user/host source files:
userfileName = 'users.txt'
prefixfileName = 'adjectives.txt'
nounfileName = 'nouns.txt'
placesfileName = 'places.txt'

lowercaseNickProbability = 0.5

# possibility that a user quits instead of just leaving
# TODO: make consistent among user
quitProbability = 0.75

# cumulative, so actionProbability is 0.008 in reality
kickProbability = 0.002
actionProbability = 0.008 + kickProbability
joinPartProbability = 0.04 + actionProbability
# difference to 1: normal message

# probabilities for various user types
lowercaseNoPunctuationUserProbability = 0.4                                 # type 0
standardUserProbability = 0.22 + lowercaseNoPunctuationUserProbability      # type 1
lowercaseUserProbability = 0.15 + standardUserProbability                   # type 2
uppercaseUserProbability = 0.1 + lowercaseUserProbability                   # type 3
noPunctuationUserProbability = 0.05 + uppercaseUserProbability              # type 4
txtSpeechUserProbability = 0.08 + noPunctuationUserProbability              # type 5

# user type IDs
# TODO: make this an enum
lowercaseNoPunctuationID = 0
standardID = 1
lowercaseID = 2
uppercaseID = 3
noPunctuationID = 4
txtSpeechID = 5

# probability a user type shows his 'non-standard' behavior
# TODO: make functional
useLowercaseNoPunctuation = 0.99
useLowercase = 0.99
useUppercase = 0.2
useNoPunctuation = 0.99
useTxtSpeech = 0.5

# END flags and sizes

# TODO: create a function that simulates this behavior with fluid numbers after being given a general activity.
# TODO: tweak activity: currently 1,000,000 lines go from May 29 2014 to Apr 05 2023
# possible timedeltas after messages
timeSpan = [5, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 10, 10, 10, 10, 12, 15, 20, 30, 30, 30, 20, 60, 120, 300, 600, 1200, 2400]

# abbreviations of weekdays and months
days = ['Mon ', 'Tue ', 'Wed ', 'Thu ', 'Fri ', 'Sat ', 'Sun ']
months = ['Jan ', 'Feb ', 'Mar ', 'Apr ', 'May ', 'Jun ', 'Jul ', 'Aug ', 'Sep ', 'Oct ', 'Nov ', 'Dec ']

# list with symbols that end a sentence
# add ':', ',' for shorter messages?
EOS = ['.', '?', '!', ':', '"', ':', ',', ';']

def selectUserByActivity(users, total):
    r = uniform(0, total)
    upto = 0
    for user in users:
        upto += user.activity
        if r <= upto:
            return user

def buildDict(words):
    # builds morkov dictionary from given words
    # based on http://pythonadventures.wordpress.com/2014/01/23/generating-pseudo-random-text-using-markov-chains/
    dictionary = {}
    for i, word in enumerate(words):
        try:
            first, second, third = words[i], words[i+1], words[i+2]
        except IndexError:
            break
        key = (first, second)
        if key not in dictionary:
            dictionary[key] = []
        dictionary[key].append(third)
    return dictionary

def buildStartlist(dictionary):
    # generates possible line starts (if the first letter is uppercase here)
    return [key for key in dictionary.keys() if key[0][0].isupper()]

def makeTransMaps():
    # creates translation maps for the various write functions
    global removePunctuationMap
    removePunctuationMap = str.maketrans('', '', string.punctuation)
    global removePunctuationAndUpperCaseMap
    removePunctuationAndUpperCaseMap = str.maketrans(string.ascii_uppercase, string.ascii_lowercase, string.punctuation)
    global noVocalMap
    noVocalMap = str.maketrans('', '', 'aeiou')

# writes to log with 'flavour'
def writeWithFlavour(text, flavourType):
    if flavourType == lowercaseNoPunctuationID:
        lf.write(text.translate(removePunctuationAndUpperCaseMap))
    if flavourType == standardID:
        lf.write(text)
    if flavourType == lowercaseID:
        lf.write(text.lower())
    if flavourType == uppercaseID:
        lf.write(text.upper())
    if flavourType == noPunctuationID:
        lf.write(text.translate(removePunctuationMap))
    if flavourType == txtSpeechID:
        lf.write(text.translate(noVocalMap))

def loadMessages():
    # loads up message dictionary and start list
    # read words from file and generate markov dictionary
    sourceFile = open(sourcefileName, 'rt')
    text = sourceFile.read()
    words = text.split()
    global messageDict
    messageDict = buildDict(words)

    # generate list of possible line starts
    global startList
    startList = buildStartlist(messageDict)
    sourceFile.close()

def loadReasons():
    # loads up reasons dictionary and start list
    # read words from file and generate markov dictionary
    reasonsFile = open(reasonsfileName, 'rt')
    text = reasonsFile.read()
    words = text.split()
    global reasonsDict
    reasonsDict = buildDict(words)

    # generate list of possible line starts
    global reasonsStartList
    reasonsStartList = buildStartlist(reasonsDict)
    reasonsFile.close()

def _joinHostmask(prefix, noun, place):
    # helper function for hostmask creation
    strList = []
    strList.append(prefix)
    strList.append(noun)
    strList.append("from")
    strList.append(place)
    return '.'.join(strList)

# TODO: make it possible to create additional users later?
def loadUsers():
    # load nicks from startList items, as they all have a uppercase starting letter
    # depends on startList already being generated
    startListLenght = len(startList)

    global users
    users = []

    nicks = []
    # generate list of possible nicks
    for i in range(0, userCount*nicksPerUser):
        # choose nick from list of possible starting words, remove punctuation from nick
        nick = startList[randint(0, startListLenght - 1)][0].translate(removePunctuationMap)

        # make sure nick isn't in nicks and of some lenght
        while (nick.lower() in [nick.lower() for nick in nicks]) or (len(nick) < minNickLenght):
            nick = startList[randint(0, startListLenght - 1)][0].translate(removePunctuationMap)

        # make some of them lowercase
        if random() < lowercaseNickProbability:
            nick = nick.lower()
        else:
            pass
        nicks.append(nick)

    # load lists for username and hostmask generation
    # load possible user names
    userFile = open(userfileName, 'r')
    userList = userFile.read().split()
    userFile.close()
    # load possible 'prefixes'
    prefixFile = open(prefixfileName, 'r')
    prefixList = prefixFile.read().split()
    prefixFile.close()
    # load possible nouns
    nounFile = open(nounfileName, 'r')
    nounList = nounFile.read().split()
    nounFile.close()
    # load possible places
    placesFile = open(placesfileName, 'r')
    placesList = placesFile.read().split()
    placesFile.close()

    # lists used to prevent the same username/hostmask appearing twice
    userNames = []
    hostmasks = []

    # TODO: find better solution???
    global offline
    offline = []
    global online
    online = []

    # choose values for each user, create user and append to users
    for i in range(0, userCount):
        # choose username
        userName = choice(userList)
        while userName in userNames:
            userName = choice(userList)
        userNames.append(userName)

        # choose hostmask
        hostmask = _joinHostmask(choice(prefixList), choice(nounList), choice(placesList))
        while hostmask in hostmasks:
            hostmask = _joinHostmask(choice(prefixList), choice(nounList), choice(placesList))
        hostmasks.append(hostmask)

        # create list of possible nicks for user from list of overall possible nicks
        userNicks = []
        for j in range(0, nicksPerUser):
            userNicks.append(nicks.pop())

        # choose user type
        # TODO: beautify (i.e. create a function for this type of selection? only if faster)
        # TODO: change when IDs are enum
        determineType = random()
        if determineType < lowercaseNoPunctuationUserProbability:
            userType = lowercaseNoPunctuationID
        elif determineType < standardUserProbability:
            userType = standardID
        elif determineType < lowercaseUserProbability:
            userType = lowercaseID
        elif determineType < uppercaseUserProbability:
            userType = uppercaseID
        elif determineType < noPunctuationUserProbability:
            userType = noPunctuationID
        elif determineType < txtSpeechUserProbability:
            userType = txtSpeechID

        # choose activity level
        # TODO: find better activity distribution
        activity = (sin(random() * pi) + 1) / 2

        # create User object, append to global user list
        # user is initially offline
        user = User(i, userName, hostmask, userNicks, userType, activity, False)
        users.append(user)
        offline.append(user)

    global onlineUsers
    onlineUsers = 0

    # sums of activity numbers for weighted choice
    global activityTotal
    activityTotal = sum(user.activity for user in users)
    global offlineActivityTotal
    offlineActivityTotal = activityTotal
    global onlineActivityTotal
    onlineActivityTotal = 0

def incrementLine():
    global totalLines
    totalLines += 1

    # TODO: better way to handle activity?
    global date
    date = date + datetime.timedelta(seconds = choice(timeSpan) * (sin((date.hour + 12) * pi / 24) + 1.5))

def writeReason():
    # generates a reason
    writeSentence(reasonsDict, reasonsStartList, standardID)

def setOnline(user):
    if user in offline:
        online.append(user)
        offline.remove(user)

        global onlineActivityTotal
        global offlineActivityTotal
        onlineActivityTotal += user.activity
        offlineActivityTotal -= user.activity
        global onlineUsers
        onlineUsers += 1

def setOffline(user):
    if user in online:
        online.remove(user)
        offline.append(user)

        global onlineActivityTotal
        global offlineActivityTotal
        onlineActivityTotal -= user.activity
        offlineActivityTotal += user.activity
        global onlineUsers
        onlineUsers -= 1

def selectUser():
    return selectUserByActivity(users, activityTotal)

def selectOnlineUser():
    return selectUserByActivity(online, onlineActivityTotal)

def selectOfflineUser():
    return selectUserByActivity(offline, offlineActivityTotal)

def writeTime():
    lf.write(str(date.hour).zfill(2))
    lf.write(":")
    lf.write(str(date.minute).zfill(2))

def _writeJoinPartQuitBeginning(user):
    writeTime()
    lf.write(" -!- ")
    lf.write(user.nick)
    lf.write(" [")
    lf.write(user.combinedUserAndHost)
    lf.write("] has ")

def writeLeaveOrQuit(user, isQuit):
    # writes leave or quit message to log
    _writeJoinPartQuitBeginning(user)
    if isQuit:
        lf.write("quit [")
    else:
        lf.write("left #")
        lf.write(channelName)
        lf.write(" [")
    writeReason()
    lf.write("]\n")

    setOffline(user)

    incrementLine()

def writeJoin(user):
    # writes join message to log
    _writeJoinPartQuitBeginning(user)
    lf.write("joined #")
    lf.write(channelName)
    lf.write("\n")

    setOnline(user)

    incrementLine()

def populateChannel():
    # populates channel with initialPopulation users
    if logInitialPopulation:
        while onlineUsers < initialPopulation:
            writeJoin(selectOfflineUser())
    else:
        while onlineUsers < initialPopulation:
            setOnline(selectOfflineUser())

def checkPopulation():
    # makes sure some amount of peeps are online or offline
    while onlineUsers <= minOnline:
        writeJoin(selectOfflineUser())
    while (userCount - onlineUsers) <= minOffline:
        writeLeaveOrQuit(selectOnlineUser(), random() < quitProbability)

def joinPartEvent():
    # make sure someone is online at all times, or create a fallback
    user = selectUser()
    if user in online:
        writeLeaveOrQuit(user, random() < quitProbability)
    else:
        writeJoin(user)

    # make sure some amount of peeps are online or offline
    checkPopulation()

def kickEvent():
    # kicks some user
    kickee = selectOnlineUser()
    kicker = selectOnlineUser()
    while kicker == kickee:
        kicker = selectOnlineUser()

    writeTime()
    lf.write(" -!- ")
    lf.write(kickee.nick)
    lf.write(" was kicked from #")
    lf.write(channelName)
    lf.write(" by ")
    lf.write(kicker.nick)
    lf.write(" [")
    writeReason()
    lf.write("]\n")

    incrementLine()

    setOffline(kickee)

    # make sure some amount of peeps are online or offline
    checkPopulation()

def writeSentence(d, li, flavourType):
    # generates message from given markov dictionary and start list
    # based on http://pythonadventures.wordpress.com/2014/01/23/generating-pseudo-random-text-using-markov-chains/
    key = choice(li)

    first, second = key
    writeWithFlavour(first, flavourType)
    lf.write(' ')
    writeWithFlavour(second, flavourType)
    lf.write(' ')
    while True:
        try:
            third = choice(d[key])
        except KeyError:
            break
        writeWithFlavour(third, flavourType)
        if third[-1] in EOS:
            break
        lf.write(' ')
        key = (second, third)
        first, second = key

def writeMessage(user):
    writeTime()
    lf.write(" < ")
    # TODO: OP/Half-OP/Voice symbols
    lf.write(user.nick)
    lf.write("> ")
    writeSentence(messageDict, startList, user.userType)
    lf.write("\n")

    incrementLine()

def userAction():
    writeTime()
    lf.write("  * ")
    lf.write(selectOnlineUser().nick)

    # TODO: implement variable user action text (best with leading space)
    lf.write(" does action\n")

    incrementLine()

def _writeFullTimestamp():
    # writes full timestamp to log file
    lf.write(days[date.weekday()])
    lf.write(months[date.month - 1])
    lf.write(str(date.day).zfill(2))
    lf.write(" ")
    lf.write(str(date.hour).zfill(2))
    lf.write(":")
    lf.write(str(date.minute).zfill(2))
    lf.write(":")
    lf.write(str(date.second).zfill(2))
    lf.write(" ")
    lf.write(str(date.year))

def main():
    # create character maps for various text processing/writing functions
    makeTransMaps()

    # generate message dictionary and line start list
    loadMessages()

    # load users
    loadUsers()

    # load up reasons
    loadReasons()

    # get current date
    global date
    date = datetime.datetime.now()
    daycache = date.day

    # open log file
    global lf
    lf = open(logfileName, 'w')

    # number of total lines
    global totalLines
    totalLines = 0

    # write opening of log
    lf.write("--- Log opened ")
    _writeFullTimestamp()
    lf.write("\n")
    incrementLine()

    # initial population of channel
    populateChannel()

    # bulk of messages
    while totalLines < lineMax - 1:
        # check if day changed, if so, write day changed message
        if daycache != date.day:
            lf.write("--- Day changed " + days[date.weekday()] + months[date.month - 1] + 
            str(date.day).zfill(2) + " " + str(date.year) + "\n")
            daycache = date.day
            incrementLine()

        # generate line
        determineType = random()
        if determineType > joinPartProbability:
            # user message
            writeMessage(selectOnlineUser())
        elif determineType > actionProbability:
            # random join/part event
            joinPartEvent()
        elif determineType > kickProbability:
            # user action
            userAction()
        else:
            # kick event
            kickEvent()

    # write log closing message
    lf.write("--- Log closed ")
    _writeFullTimestamp()
    lf.write("\n")
    incrementLine()

    # close log file
    lf.close()

def profileMain():
    cProfile.run('ircsimul.main()')

if __name__ == "__main__":
    main()
