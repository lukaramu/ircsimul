import argparse
import datetime
import logging
import cProfile
import sys
from math import sin, pi
from random import choice, random

import helpers
import markov
from channel import Channel
from user import User
from log import Log
import userTypes

# TODO: event based system: http://pastebin.com/Nw854kcf
# event roadmap (will also nearly obliterate globals):
# create event class
# create event subclasses
# move current system to be event-based
# implement per-user event creation (e.g.)

# TODO: check if activity is correct
# TODO: instead of/additionally to truncating lines at commas, spread message out over seperate messages
# might be cool: having them ping each other in "conversations" where only the last N messages of the person they are pinging are used in the generator so the conversation is "topical"

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

# TODO: make subclass of Event
def leaveEvent(user):
    log.writeLeave(user, channel.name, markovGenerator.generateReason())
    channel.setOffline(user)

# TODO: make subclass of Event
def quitEvent(user):
    log.writeQuit(user, markovGenerator.generateReason())
    channel.setOffline(user)

# TODO: make subclass of Event
def joinEvent(user):
    # writes join message to log
    log.writeJoin(user, channel.name)
    channel.setOnline(user)

# TODO: move to channel class later
def populateChannel():
    # populates channel with initialPopulation users
    if logInitialPopulation:
        while channel.onlineUsers < initialPopulation:
            joinEvent(channel.selectOfflineUser())
    else:
        while channel.onlineUsers < initialPopulation:
            channel.setOnline(channel.selectOfflineUser())

# TODO: make deterministic, replace with leaveEvent and quitEvent
def joinPartEvent(user):
    if user in channel.online:
        if random() < quitProbability:
            quitEvent(user)
        else:
            leaveEvent(user)
    else:
        joinEvent(user)

    # make sure some amount of peeps are online or offline
    checkPopulation()

# TODO: move to channel class later
def checkPopulation():
    # makes sure some amount of peeps are online or offline
    while channel.onlineUsers <= minOnline:
        joinPartEvent(channel.selectOfflineUser())
    while (channel.userCount - channel.onlineUsers) <= minOffline:
        joinPartEvent(channel.selectOnlineUser())

# TODO: make subclass of Event
def kickEvent(kickee, kicker):
    log.writeKick(kickee, kicker, channel.name, markovGenerator.generateReason())
    channel.setOffline(kickee)

    # make sure some amount of peeps are online or offline
    checkPopulation()

# TODO: make subclass of Event
def messageEvent(user):
    log.writeMessage(user, markovGenerator.generateMessage())

# TODO: make subclass of Event
def userActionEvent(user):
    # TODO: implement variable user action text (best with leading space)
    log.writeAction(user, "does action")

def main():
    # create character maps for various text processing/writing functions
    helpers.makeTransMaps()

    # load up markov generator
    global markovGenerator
    markovGenerator = markov.MarkovGenerator(sourcefileName, reasonsfileName)

    # load channel
    global channel
    channel = Channel(channelName, markovGenerator, initialUserCount)

    # open log
    global log
    fileObjectList = []
    fileObjectList.append(open(logfileName, 'wt', encoding='utf8'))
    if writeStdOut:
        fileObjectList.append(sys.stdout)
    log = Log(fileObjectList)

    daycache = log.date.day

    # write opening of log
    log.writeLogOpening()

    # initial population of channel
    populateChannel()

    # bulk of messages
    while log.totalLines < lineMax - 1:
        # check if day changed, if so, write day changed message
        if daycache != log.date.day:
            log.writeDayChange()
            daycache = log.date.day

        # generate line
        determineType = random()
        if determineType > joinPartProbability:
            # user message
            messageEvent(channel.selectOnlineUser())
        elif determineType > actionProbability:
            # random join/part event
            joinPartEvent(channel.selectUser())
        elif determineType > kickProbability:
            # user action
            userActionEvent(channel.selectOnlineUser())
        else:
            # kick event
            kickee = channel.selectOnlineUser()
            kicker = channel.selectOnlineUser()
            kickEvent(kickee, kicker)

    # write log closing message
    log.writeLogClosing()

    # close log file
    log.lfs[0].close()

def profileMain():
    cProfile.run('ircsimul.main()')

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        print("This script needs to be run on Python 3! (It's being tested on 3.3 currently)")
        sys.quit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lines", help="number of lines to be generated", type=int)
    parser.add_argument("-o", "--output", help="sets output file (if not given, logs to ircsimul.log)", type=str)
    parser.add_argument("--stdout", help="toggles output to stdout", action="store_true")
    args = parser.parse_args()

    # TODO: make this less messy
    global lineMax
    if args.lines:
        lineMax = args.lines
    else:
        lineMax = 50000
    global logfileName
    if args.output:
        logfileName = args.output
    else:
        logfileName = 'ircsimul.log'
    global writeStdOut
    if args.stdout:
        writeStdOut = True
    else:
        writeStdOut = False

    main()
