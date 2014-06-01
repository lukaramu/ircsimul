import datetime
import logging
import cProfile
from math import sin
from math import pi
from random import choice
from random import random
from random import randint
from random import uniform

import helpers
import markov
from user import User

# event roadmap (will also nearly obliterate globals):
# move stuff to markov.py
# (optional) move stuff to helper.py
# create channel class
# create writer class
# move loadUsers to users.py to eventually later have user creation on the fly
# create event class
# create event subclasses
# implement event printing in writer
# move current system to be event-based
# implement per-user event creation (e.g.)
# implement event handling in event class (i.e. writing etc)
# migrate saduidghfbsdhgdsgbisfoigbsdnfgfdsg

# TODO: check if activity is correct
# TODO: spread out stuff over multiple files
# TODO: instead of/additionally to truncating lines at commas, spread message out over seperate messages
# TODO: event based system: http://pastebin.com/Nw854kcf
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
lineMax = 50000
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
# TODO: make consistent among user (e.g. User value)
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
# TODO: move to writer class later
days = ['Mon ', 'Tue ', 'Wed ', 'Thu ', 'Fri ', 'Sat ', 'Sun ']
months = ['Jan ', 'Feb ', 'Mar ', 'Apr ', 'May ', 'Jun ', 'Jul ', 'Aug ', 'Sep ', 'Oct ', 'Nov ', 'Dec ']

# list with symbols that end a sentence
EOS = ['.', '?', '!', ':', '"', ':', ',', ';']

# TODO: remove when obsolete (after events are implemented)
def selectUserByActivity(users, total):
    r = uniform(0, total)
    upto = 0
    for user in users:
        upto += user.activity
        if r <= upto:
            return user

# TODO: move to writer class later
def writeWithFlavour(text, flavourType):
    # writes to log with 'flavour'
    if flavourType == lowercaseNoPunctuationID:
        lf.write(text.translate(helpers.removePunctuationAndUpperCaseMap))
    if flavourType == standardID:
        lf.write(text)
    if flavourType == lowercaseID:
        lf.write(text.lower())
    if flavourType == uppercaseID:
        lf.write(text.upper())
    if flavourType == noPunctuationID:
        lf.write(text.translate(helpers.removePunctuationMap))
    if flavourType == txtSpeechID:
        lf.write(text.translate(helpers.noVocalMap))

# TODO: move to users.py with loadUsers?
def _chooseNick(dictionary, startListLen):
    # returns nick from list of possible starting words removes punctuation from nick
    return dictionary.startList[randint(0, startListLen - 1)][0].translate(helpers.removePunctuationMap)

# TODO: move to users.py with loadUsers?
def _joinHostmask(prefix, noun, place):
    # returns combined hostmask
    strList = []
    strList.append(prefix)
    strList.append(noun)
    strList.append("from")
    strList.append(place)
    return '.'.join(strList)

# TODO: make it possible to create additional users later?
# TODO: move to users.py?
def loadUsers():
    # load nicks from startList items, as they all have a uppercase starting letter
    # depends on startList already being generated
    startListLen = len(messageDict.startList)

    # TODO: move to channel class later:
    global users
    users = []

    nicks = []

    # generate list of possible nicks
    for i in range(0, userCount*nicksPerUser):
        # choose nick from list of possible starting words, remove punctuation from nick
        nick = _chooseNick(messageDict, startListLen)
        # make sure nick isn't in nicks and of some lenght
        while (nick.lower() in [nick.lower() for nick in nicks]) or (len(nick) < minNickLenght):
            nick = _chooseNick(messageDict, startListLen)

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

    # TODO: move to channel class later
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

    # TODO: move to channel class later
    global onlineUsers
    onlineUsers = 0

    # sums of activity numbers for weighted choice
    # TODO: move to channel class later (might not be necessary b/c of rework w/ events and such)
    global activityTotal
    activityTotal = sum(user.activity for user in users)
    global offlineActivityTotal
    offlineActivityTotal = activityTotal
    global onlineActivityTotal
    onlineActivityTotal = 0

# TODO: move to writer class later
# TODO: make lf.write("\n") part of incrementLine()
def incrementLine():
    # TODO: move to writer class later
    global totalLines
    totalLines += 1

    # TODO: move to main() as local when events are implemented?
    # TODO: make time independant of line w/ events
    global date
    date = date + datetime.timedelta(seconds = choice(timeSpan) * (sin((date.hour + 12) * pi / 24) + 1.5))

# TODO: move to writer class later
def writeReason():
    # generates a reason
    writeSentence(reasonsDict, standardID)

# TODO: move to channel class later
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

# TODO: move to channel class later
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

# TODO: check if still necessary with new event system
def selectUser():
    return selectUserByActivity(users, activityTotal)

def selectOnlineUser():
    return selectUserByActivity(online, onlineActivityTotal)

def selectOfflineUser():
    return selectUserByActivity(offline, offlineActivityTotal)

# TODO: move to writer class later
def writeTime():
    lf.write(str(date.hour).zfill(2))
    lf.write(":")
    lf.write(str(date.minute).zfill(2))

# TODO: move to writer class later
def _writeJoinPartQuitBeginning(user):
    writeTime()
    lf.write(" -!- ")
    lf.write(user.nick)
    lf.write(" [")
    lf.write(user.combinedUserAndHost)
    lf.write("] has ")

# TODO: move to writer class later
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

# TODO: move to writer class later
def writeJoin(user):
    # writes join message to log
    _writeJoinPartQuitBeginning(user)
    lf.write("joined #")
    lf.write(channelName)
    lf.write("\n")

    setOnline(user)

    incrementLine()

# TODO: move to channel class later
def populateChannel():
    # populates channel with initialPopulation users
    if logInitialPopulation:
        while onlineUsers < initialPopulation:
            writeJoin(selectOfflineUser())
    else:
        while onlineUsers < initialPopulation:
            setOnline(selectOfflineUser())

# TODO: move to channel class later
def checkPopulation():
    # makes sure some amount of peeps are online or offline
    while onlineUsers <= minOnline:
        writeJoin(selectOfflineUser())
    while (userCount - onlineUsers) <= minOffline:
        writeLeaveOrQuit(selectOnlineUser(), random() < quitProbability)

# TODO: determine join or part in event selection
# TODO: make subclass of Event
def joinPartEvent(user):
    if user in online:
        writeLeaveOrQuit(user, random() < quitProbability)
    else:
        writeJoin(user)

    # make sure some amount of peeps are online or offline
    checkPopulation()

# TODO: move writing to writer class later
# TODO: make subclass of Event
def kickEvent(kickee, kicker):
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

# move to markov.py?
def writeSentence(markovDict, flavourType):
    # generates message from given markov dictionary and start list
    # based on http://pythonadventures.wordpress.com/2014/01/23/generating-pseudo-random-text-using-markov-chains/
    key = choice(markovDict.startList)

    first, second = key
    writeWithFlavour(first, flavourType)
    lf.write(' ')
    writeWithFlavour(second, flavourType)
    lf.write(' ')
    while True:
        try:
            third = choice(markovDict.dictionary[key])
        except KeyError:
            break
        writeWithFlavour(third, flavourType)
        if third[-1] in EOS:
            break
        lf.write(' ')
        key = (second, third)
        first, second = key

# TODO: make subclass of Event as messageEvent
def writeMessage(user):
    writeTime()
    lf.write(" < ")
    # TODO: OP/Half-OP/Voice symbols
    lf.write(user.nick)
    lf.write("> ")
    writeSentence(messageDict, user.userType)
    lf.write("\n")

    incrementLine()

# TODO: make subclass of Event as userActionEvent
def userAction(user):
    writeTime()
    lf.write("  * ")
    lf.write(user.nick)

    # TODO: implement variable user action text (best with leading space)
    lf.write(" does action\n")

    incrementLine()

# TODO: move to writer class later
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
    helpers.makeTransMaps()

    # generate message dictionary and line start list
    # TODO: move to markov.py?
    global messageDict
    messageDict = markov.MarkovDict(sourcefileName)

    # load users
    loadUsers()

    # load up reasons
    # TODO: move to markov.py?
    global reasonsDict
    reasonsDict = markov.MarkovDict(reasonsfileName)

    # get current date
    # TODO: move to channel later??
    global date
    date = datetime.datetime.now()
    daycache = date.day

    # open log file
    # move to writer class later
    global lf
    lf = open(logfileName, 'w')

    # number of total lines
    # move to writer class later
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
            joinPartEvent(selectUser())
        elif determineType > kickProbability:
            # user action
            userAction(selectOnlineUser())
        else:
            # kick event
            kickee = selectOnlineUser()
            kicker = selectOnlineUser()
            while kicker == kickee:
                kicker = selectOnlineUser()
            kickEvent(kickee, kicker)

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
