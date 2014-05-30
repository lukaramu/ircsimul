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

# TODO: find alternative to/optimize repeated choices, e.g. cache list lenghts? choice() runs 23.7% of the time
# TODO: faster version to fill in the zero (instead of zfill?) (might not be necessary)
# TODO: instead of/additionally to truncating lines at commas, spread message out over seperate messages

# new features:
# TODO: user adresses (e.g. water@like.from.the.toilet) (must be bound to nick and kept through nickchange)
# TODO: nick changes
# TODO: channel modes
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
# remove punctuation
# all lowercase
# average word count
# average word length (if possible)
# ALLCAPS MESSAGES
# multiple exclamation marks !!!!!!!!!!!!!!
# times dumbfounded (???)
# aloof (doesn't mention often)
# apostrophe uses?
# text speach
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
userCount = 40
minNickLenght = 6
minOnline = 5
minOffline = 5
initialPopulation = 10
logInitialPopulation = True

lowercaseNickProbability = 0.5

# cumulative, so actionProbability is 0.01 in reality
kickProbability = 0.002
actionProbability = 0.01
joinPartProbability = 0.05

# possibility that a user quits instead of just leaving
quitProbability = 0.75

# END flags and sizes

# TODO: create a function that simulates this behavior with fluid numbers after being given a general activity.
# TODO: tweak activity: currently 1,000,000 lines go from May 29 2014 to Apr 05 2023
# possible timedeltas after messages
timeSpan = [5, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 10, 10, 10, 10, 12, 15, 20, 30, 30, 30, 20, 60, 120, 300, 600, 1200, 2400, 2400]

# abbreviations of weekdays and months
days = ['Mon ', 'Tue ', 'Wed ', 'Thu ', 'Fri ', 'Sat ', 'Sun ']
months = ['Jan ', 'Feb ', 'Mar ', 'Apr ', 'May ', 'Jun ', 'Jul ', 'Aug ', 'Sep ', 'Oct ', 'Nov ', 'Dec ']

# list with symbols that end a sentence
# add ':', ',' for shorter messages?
EOS = ['.', '?', '!', ':', '"', ':', ',', ';']

def weightedChoice(choice, weights):
    total = 0
    for c in choices:
        total += weights[c]
    return weightedChoiceWithTotal(choice, weights, total)

def weightedChoiceWithTotal(choices, weights, total):
    r = uniform(0, total)
    upto = 0
    for c in choices:
        upto += weights[c]
        if r <= upto:
            return c

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

def writeLowercase(text):
    lf.write(text.lower())

def writeAllCaps(text):
    lf.write(text.upper())

def writeWithoutPunctuation(text):
    lf.write(text.translate(removePunctuationMap))

def writeLowercaseWithoutPunctuation(text):
    lf.write(text.translate(removePunctuationAndUpperCaseMap))

def writeTxtSpeech(text):
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

def loadNicks():
    # load nicks from startList items, as they all have a uppercase starting letter
    # depends on startList already being generated
    startListLenght = len(startList)

    global nicks
    nicks = []
    for i in range(0, userCount):
        nick = startList[randint(0, startListLenght - 1)][0]

        # make sure nick isn't in nicks and of some lenght
        while (nick in nicks) or (len(nick) < minNickLenght):
            nick = startList[randint(0, startListLenght - 1)][0]
        # remove punctuation from nick, make some of them lowercase
        if random() < lowercaseNickProbability:
            nicks.append(nick.translate(removePunctuationMap).lower())
        else:
            nicks.append(nick.translate(removePunctuationMap))

    global activity
    activity = {}
    global online
    online = []
    global offline
    offline = []
    global onlineNicks
    onlineNicks = 0
    for nick in nicks:
        # TODO: find better activity distribution
        activity[nick] = (sin(random() * pi) + 1) / 2
        offline.append(nick)

    # sums of activity numbers for weighted choice
    global activityTotal
    activityTotal = sum(activity[nick] for nick in nicks)
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
    writeSentence(reasonsDict, reasonsStartList)

def getUser():
    return "users@will.be.implemented.later"

def setOnline(nick):
    if nick in offline:
        online.append(nick)
        offline.remove(nick)

        global onlineActivityTotal
        global offlineActivityTotal
        onlineActivityTotal += activity[nick]
        offlineActivityTotal -= activity[nick]
        global onlineNicks
        onlineNicks += 1

def setOffline(nick):
    if nick in online:
        online.remove(nick)
        offline.append(nick)

        global onlineActivityTotal
        global offlineActivityTotal
        onlineActivityTotal -= activity[nick]
        offlineActivityTotal += activity[nick]
        global onlineNicks
        onlineNicks -= 1

def populateChannel():
    # populates channel with initialPopulation users
    if logInitialPopulation:
        while onlineNicks < initialPopulation:
            writeJoin(selectOfflineNick())
    else:
        while onlineNicks < initialPopulation:
            setOnline(selectOfflineNick())

def selectNick():
    return weightedChoiceWithTotal(nicks, activity, activityTotal)

def selectOnlineNick():
    return weightedChoiceWithTotal(online, activity, onlineActivityTotal)

def selectOfflineNick():
    return weightedChoiceWithTotal(offline, activity, offlineActivityTotal)

def writeTime():
    lf.write(str(date.hour).zfill(2))
    lf.write(":")
    lf.write(str(date.minute).zfill(2))

def writeLeaveOrQuit(nick, isQuit):
    # writes leave or quit message to log
    writeTime()
    lf.write(" -!- ")
    lf.write(nick)
    lf.write(" [")
    lf.write(getUser())
    lf.write("]")
    if isQuit:
        lf.write(" has quit [")
    else:
        lf.write(" has left #")
        lf.write(channelName)
        lf.write(" [")
    writeReason()
    lf.write("]\n")

    setOffline(nick)

    incrementLine()

def writeJoin(nick):
    # writes join message to log
    writeTime()
    lf.write(" -!- ")
    lf.write(nick)
    lf.write(" [")
    lf.write(getUser())
    lf.write("]")
    lf.write(" has joined #")
    lf.write(channelName)
    lf.write("\n")

    setOnline(nick)

    incrementLine()

def checkPopulation():
    # makes sure some amount of peeps are online or offline
    while onlineNicks <= minOnline:
        writeJoin(selectOfflineNick())
    while (userCount - onlineNicks) <= minOffline:
        writeLeaveOrQuit(selectOnlineNick(), random() < quitProbability)

def joinPartEvent():
    # make sure someone is online at all times, or create a fallback
    nick = selectNick()
    if nick in online:
        writeLeaveOrQuit(nick, random() < quitProbability)
    else:
        writeJoin(nick)

    # make sure some amount of peeps are online or offline
    checkPopulation()

def kickEvent():
    # kicks some user
    kickee = selectOnlineNick()
    kicker = selectOnlineNick()
    while kicker == kickee:
        kicker = selectOnlineNick()

    writeTime()
    lf.write(" -!- ")
    lf.write(kickee)
    lf.write(" was kicked from #")
    lf.write(channelName)
    lf.write(" by ")
    lf.write(kicker)
    lf.write(" [")
    writeReason()
    lf.write("]\n")

    incrementLine()

    setOffline(kickee)

    # make sure some amount of peeps are online or offline
    checkPopulation()

def writeSentence(d, li):
    # generates message from given markov dictionary and start list
    # based on http://pythonadventures.wordpress.com/2014/01/23/generating-pseudo-random-text-using-markov-chains/
    key = choice(li)

    first, second = key
    lf.write(first)
    lf.write(' ')
    lf.write(second)
    lf.write(' ')
    while True:
        try:
            third = choice(d[key])
        except KeyError:
            break
        lf.write(third)
        if third[-1] in EOS:
            break
        lf.write(' ')
        key = (second, third)
        first, second = key

def writeMessage(nick):
    writeTime()
    lf.write(" <")
    lf.write(nick)
    lf.write("> ")
    writeSentence(messageDict, startList)
    lf.write("\n")

    incrementLine()

def userAction():
    writeTime()
    lf.write("  * ")
    lf.write(selectOnlineNick())

    # TODO: implement variable user action text (best with leading space)
    lf.write(" does action\n")

    incrementLine()

def main():
    # create character maps for various text processing/writing functions
    makeTransMaps()

    # generate message dictionary and line start list
    loadMessages()

    # load possible nicknames
    loadNicks()

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
    lf.write("--- Log opened " + days[date.weekday()] + months[date.month - 1] + 
        str(date.day).zfill(2) + " " + str(date.hour).zfill(2) + ":" + str(date.minute).zfill(2) + 
        ":" + str(date.second).zfill(2) + " " + str(date.year) + "\n")

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
        # TODO: make this choice with weightedChoice() and exec()
        determineType = random()
        if determineType > joinPartProbability:
            # user message
            writeMessage(selectOnlineNick())
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
    lf.write("--- Log closed " + days[date.weekday()] + months[date.month - 1] + 
        str(date.day).zfill(2) + " " + str(date.hour).zfill(2) + ":" + str(date.minute).zfill(2) + 
        ":" + str(date.second).zfill(2) + " " + str(date.year) + "\n")
    incrementLine()

    # close log file
    lf.close()

def profileMain():
    cProfile.run('ircsimul.main()')

if __name__ == "__main__":
    main()
