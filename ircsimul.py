import datetime
import logging
from math import sin
from math import pi
from random import choice
from random import random
from random import randint
from random import uniform

# TODO: find alternative to/optimize repeated choices, e.g. cache list lenghts? choice() runs 37.5% of the time
# TODO: faster version to fill in the zero (instead of zfill?)
# TODO: flag to hide initial population joins/leaves/quits
# TODO: instead of truncating lines at commas, spread message out over seperate messages
# TODO: generate nicknames from proper nouns in text
# TODO: increment time during time increments
# TODO: add/subtract from onlineNicks, onlineActivityTotal and offlineActivityTotal in seperate function

# new features:
# TODO: user adresses (e.g. water@like.from.the.toilet) (must be bound to nick and kept through nickchange)
# TODO: nick changes
# TODO: channel modes
# TODO: topics
# TODO: bans
# TODO: notices
# TODO: mentions
# TODO: urls

# TODO: make them say hi sometimes?
# TODO: make kicks have an internal reason

# TODO: different nicks, different behaviour (longshot):
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

# flags and sizes, set by user
# TODO: Make some of them command line arguments?
lineMax = 200000
logfileName = 'ircsimul.log'
sourcefileName = 'ZARATHUSTRA.txt'
nickfileName = 'nicks.txt'
reasonsfileName = 'reasons.txt'
channelName = 'channel'
userCount = 40                      # still unused
minOnline = 5
minOffline = 5
initialPopulation = 10
logInitialPopulation = False

# cumulative, so actionProbability is 0.01 in reality
# TODO: make this not cumulative
kickProbability = 0.002
actionProbability = 0.01
joinPartProbability = 0.05

# possibility that a user quits instead of just leaving
quitProbability = 0.75

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
    # TODO: find better start list characteristic (e.g. follows an EOS character)
    return [key for key in dictionary.keys() if key[0][0].isupper()]

def loadNicks():
    # loads possible nicks from file
    nickFile = open(nickfileName, 'r')
    global nicks
    nicks = nickFile.read().split()
    nickFile.close()
    global nickNumber
    nickNumber = len(nicks)
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
    offlineActivityTotal = 0
    global onlineActivityTotal
    onlineActivityTotal = 0

def loadReasons():
    # loads up reasons dictionary and start list
    reasonsFile = open(reasonsfileName, 'rt')
    text = reasonsFile.read()
    words = text.split()
    global reasonsDict
    reasonsDict = buildDict(words)
    global reasonsStartList
    reasonsStartList = buildStartlist(reasonsDict)
    reasonsFile.close()

def incrementLineCount():
    global totalLines
    totalLines += 1

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

# TODO: optimize so that total probability is updated during joins/parts, making repeated summing redundant
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

    incrementLineCount()

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

    incrementLineCount()

def checkPopulation():
    # makes sure some amount of peeps are online or offline
    while onlineNicks <= minOnline:
        writeJoin(selectOfflineNick())
    while (nickNumber - onlineNicks) <= minOffline:
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

    incrementLineCount()

    setOffline(kickee)

    # make sure some amount of peeps are online or offline
    checkPopulation()

def writeSentence(d, li):
    # generates message from given markov dictionary
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
    # TODO: only 79.2% of time are spent writing --> if possible, increase that
    writeTime()
    lf.write(" <")
    lf.write(nick)
    lf.write("> ")
    writeSentence(messageDict, startList)
    lf.write("\n")

    incrementLineCount()

def userAction():
    writeTime()
    lf.write("  * ")
    lf.write(selectOnlineNick())

    # TODO: implement variable user action text (best with leading space)
    lf.write(" does action\n")

    incrementLineCount()

def main():
    # generate dictionary
    sourceFile = open(sourcefileName, 'rt')
    text = sourceFile.read()
    sourceFile.close()
    words = text.split()
    global messageDict
    messageDict = buildDict(words)

    # generate list of possible line starts
    global startList
    startList = buildStartlist(messageDict)

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

    incrementLineCount()

    # initial population of channel
    populateChannel()

    # bulk of messages
    while totalLines < lineMax - 1:
        # check if day changed, if so, write day changed message
        if daycache != date.day:
            lf.write("--- Day changed " + days[date.weekday()] + months[date.month - 1] + 
            str(date.day).zfill(2) + " " + str(date.year) + "\n")
            daycache = date.day
            incrementLineCount()

        # generate line
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

        # TODO: outsource timedelta function??? better way to handle activity?
        date = date + datetime.timedelta(seconds = choice(timeSpan) * (sin((date.hour + 12) * pi / 24) + 1.5))

    # write log closing message
    lf.write("--- Log closed " + days[date.weekday()] + months[date.month - 1] + 
        str(date.day).zfill(2) + " " + str(date.hour).zfill(2) + ":" + str(date.minute).zfill(2) + 
        ":" + str(date.second).zfill(2) + " " + str(date.year) + "\n")
    incrementLineCount()

    # close log file
    lf.close()

if __name__ == "__main__":
    main()
