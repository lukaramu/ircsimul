import datetime
import logging
import cProfile
from math import sin, pi
from random import choice, randint, random, uniform

import helpers
import markov
from channel import Channel
from user import User
import userTypes

# event roadmap (will also nearly obliterate globals):
# create channel class
# create writer class
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

initialUserCount = 40                  # make sure this is less number of possible users
minOnline = 5
minOffline = 5
initialPopulation = 10
logInitialPopulation = True

# possibility that a user quits instead of just leaving
# TODO: make consistent among user (e.g. User value)
quitProbability = 0.75

# cumulative, so actionProbability is 0.008 in reality
kickProbability = 0.002
actionProbability = 0.008 + kickProbability
joinPartProbability = 0.04 + actionProbability
# difference to 1: normal message

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

# TODO: remove when obsolete (after events are implemented)
def selectUserByActivity(userList, total):
    r = uniform(0, total)
    upto = 0
    for user in userList:
        upto += user.activity
        if r <= upto:
            return user

# TODO: move to writer class later
def writeWithFlavour(text, flavourType):
    # writes to log with 'flavour'
    if flavourType == userTypes.lowercaseNoPunctuation:
        lf.write(text.translate(helpers.removePunctuationAndUpperCaseMap))
    if flavourType == userTypes.standard:
        lf.write(text)
    if flavourType == userTypes.lowercase:
        lf.write(text.lower())
    if flavourType == userTypes.uppercase:
        lf.write(text.upper())
    if flavourType == userTypes.noPunctuation:
        lf.write(text.translate(helpers.removePunctuationMap))
    if flavourType == userTypes.txtSpeech:
        lf.write(text.translate(helpers.noVocalMap))

# NOW: move to writer class later
# NOW: make this accept current date
# TODO: make lf.write("\n") part of incrementLine()
def incrementLine():
    # TODO: move to writer class later
    global totalLines
    totalLines += 1

    # TODO: move to main() as local when events are implemented?
    # TODO: make time independant of line w/ events
    global date
    date = date + datetime.timedelta(seconds = choice(timeSpan) * (sin((date.hour + 12) * pi / 24) + 1.5))

# NOW: move to writer class later
def writeReason():
    # generates a reason
    lf.write(reasonsGenerator.generateSentence())

# TODO: move to channel class later
def setOnline(user):
    global channel
    if user in channel.offline:
        channel.online.append(user)
        channel.offline.remove(user)

        channel.onlineActivityTotal += user.activity
        channel.offlineActivityTotal -= user.activity
        channel.onlineUsers += 1

# TODO: move to channel class later
def setOffline(user):
    global channel

    if user in channel.online:
        channel.online.remove(user)
        channel.offline.append(user)

        channel.onlineActivityTotal -= user.activity
        channel.offlineActivityTotal += user.activity
        channel.onlineUsers -= 1

# TODO: check if still necessary with new event system
def selectUser():
    return selectUserByActivity(channel.users, channel.activityTotal)

def selectOnlineUser():
    return selectUserByActivity(channel.online, channel.onlineActivityTotal)

def selectOfflineUser():
    return selectUserByActivity(channel.offline, channel.offlineActivityTotal)

# NOW: move to writer class later
def writeTime():
    lf.write(str(date.hour).zfill(2))
    lf.write(":")
    lf.write(str(date.minute).zfill(2))

# NOW: move to writer class later
def _writeJoinPartQuitBeginning(user):
    writeTime()
    lf.write(" -!- ")
    lf.write(user.nick)
    lf.write(" [")
    lf.write(user.combinedUserAndHost)
    lf.write("] has ")

# NOW: move to writer class later
# NOW: rename to leaveOrQuitEvent
def writeLeaveOrQuit(user, isQuit):
    # writes leave or quit message to log
    _writeJoinPartQuitBeginning(user)
    if isQuit:
        lf.write("quit [")
    else:
        lf.write("left #")
        lf.write(channel.name)
        lf.write(" [")
    writeReason()
    lf.write("]\n")

    setOffline(user)

    incrementLine()

# NOW: move to writer class later
# NOW: rename to joinEvent
def writeJoin(user):
    # writes join message to log
    _writeJoinPartQuitBeginning(user)
    lf.write("joined #")
    lf.write(channel.name)
    lf.write("\n")

    setOnline(user)

    incrementLine()

# TODO: move to channel class later
def populateChannel():
    # populates channel with initialPopulation users
    if logInitialPopulation:
        while channel.onlineUsers < initialPopulation:
            writeJoin(selectOfflineUser())
    else:
        while channel.onlineUsers < initialPopulation:
            setOnline(selectOfflineUser())

# TODO: move to channel class later
def checkPopulation():
    # makes sure some amount of peeps are online or offline
    while channel.onlineUsers <= minOnline:
        writeJoin(selectOfflineUser())
    while (channel.userCount - channel.onlineUsers) <= minOffline:
        writeLeaveOrQuit(selectOnlineUser(), random() < quitProbability)

# TODO: determine join or part in event selection
# TODO: make subclass of Event
def joinPartEvent(user):
    if user in channel.online:
        writeLeaveOrQuit(user, random() < quitProbability)
    else:
        writeJoin(user)

    # make sure some amount of peeps are online or offline
    checkPopulation()

# NOW: move writing to writer class later
# TODO: make subclass of Event
def kickEvent(kickee, kicker):
    writeTime()
    lf.write(" -!- ")
    lf.write(kickee.nick)
    lf.write(" was kicked from #")
    lf.write(channel.name)
    lf.write(" by ")
    lf.write(kicker.nick)
    lf.write(" [")
    writeReason()
    lf.write("]\n")

    incrementLine()

    setOffline(kickee)

    # make sure some amount of peeps are online or offline
    checkPopulation()

# NOW: move writing to writer class later
# NOW: rename to messageEvent
# TODO: make subclass of Event as messageEvent
def writeMessage(user):
    writeTime()
    lf.write(" < ")
    # TODO: OP/Half-OP/Voice symbols
    lf.write(user.nick)
    lf.write("> ")
    writeWithFlavour(messageGenerator.generateSentence(), user.userType)
    lf.write("\n")

    incrementLine()

# NOW: move writing to writer class later
# NOW: rename to actionEvent
# TODO: make subclass of Event as userActionEvent
def userAction(user):
    writeTime()
    lf.write("  * ")
    lf.write(user.nick)

    # TODO: implement variable user action text (best with leading space)
    lf.write(" does action\n")

    incrementLine()

# NOW: move to writer class later
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

    # load up message generator
    global messageGenerator
    messageGenerator = markov.MarkovGenerator(sourcefileName)

    # load channel
    global channel
    channel = Channel(channelName, messageGenerator, initialUserCount)

    # load up reasons generator
    global reasonsGenerator
    reasonsGenerator = markov.MarkovGenerator(reasonsfileName)

    # get current date
    # TODO: move to channel later??
    global date
    date = datetime.datetime.now()
    daycache = date.day

    # open log file
    # NOW: move to writer class later
    global lf
    lf = open(logfileName, 'w')

    # number of total lines
    # NOW: move to writer class later
    global totalLines
    totalLines = 0

    # write opening of log
    # NOW: move to writer class later
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
            # NOW: move to writer class later
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
    # NOW: move to writer class later
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
