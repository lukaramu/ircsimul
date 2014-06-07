import argparse
import datetime
import cProfile
import sys
import os
from random import choice, random
from queue import PriorityQueue, Empty
import time

import helpers
import markov
from channel import Channel
from user import User
from log import Log
from events import KickEvent, LeaveEvent, QuitEvent, JoinEvent, MessageEvent, UserActionEvent

# TODO: <starfire> loops are bad always put a base case!!

# new features:
# TODO: mentions
# TODO: x slaps y with around a bit with a large trout
# TODO: make users not join every day
# might be cool: having them ping each other in "conversations" where only the last N messages of the person they are pinging are used in the generator so the conversation is "topical"
# TODO: channel modes (o and b)
# TODO: topics
# TODO: bans
# TODO: notices
# TODO: urls
# TODO: idlers???

# TODO: make them say hi sometimes?
# TODO: make kicks have an internal reason

# TODO: different nicks, different behaviour (longshot):
# aloof (doesn't mention often)
# negativity
# questions asked
# relationships
# variance in mentions
# times mentions i.e. popular
# changing nicks often
# liking to kick
# being kicked often

# START flags and sizes
# TODO: Make some of them command line arguments?
sourcefileName = os.path.join(os.path.dirname(__file__), 'ZARATHUSTRA.txt')
reasonsfileName = os.path.join(os.path.dirname(__file__), 'reasons.txt')
metafileName = os.path.join(os.path.dirname(__file__), 'meta.log')
channelName = 'channel'

initialUserCount = 40                  # make sure this is less number of possible users

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

def generateMetaFile(channel):
    metaFile = open(metafileName, 'w')
    for user in channel.users:
        metaFile.write("\n".join([str(user.ID), 
                                  "    nicks:     {0}".format(', '.join(user.nicks)),
                                  "    user:      {0}".format(user.username),
                                  "    hostmask:  {0}".format(user.hostmask),
                                  "    activity:  {0}".format(str(user.activity)),
                                  "    userType:  {0}".format(str(user.userType)),
                                  "    isQuitter: {0}".format(str(user.isQuitter)),
                                  "    meanHour:  {0}".format(str(user.meanHour)),
                                  ""]))
    metaFile.close()

def main(lineMax=50000, logfileName='ircsimul.log', writeStdOut=False, realTime=False, 
    logInitialPopulation=False, meta=False, days=-1):
    # load up markov generator
    markovGenerator = markov.MarkovGenerator(sourcefileName, reasonsfileName)

    # load channel
    channel = Channel(channelName, markovGenerator, initialUserCount)

    # print metadata to file:
    if meta:
        generateMetaFile(channel)

    # open log
    fileObjectList = []
    fileObjectList.append(open(logfileName, 'wt', encoding='utf8'))
    if writeStdOut:
        fileObjectList.append(sys.stdout)
    log = Log(fileObjectList)

    # get current date
    date = datetime.datetime.utcnow()
    # if days are finite, reset time to 00:00:00
    if days > 0:
        date = datetime.datetime.combine(date.date(), datetime.time())

    daycache = date.day

    # create queue
    queue = PriorityQueue()

    # write opening of log
    log.writeLogOpening(date)

    # create list of users that should be put online
    toBePutOneline = []
    # check if mean online hour is within five hours of current time
    # if so, make user join
    for user in channel.users:
        timeDifference = (user.meanHour - date.hour) % 24
        if timeDifference < 6 or timeDifference > 18:
            toBePutOneline.append(user)

    # populate channel with users in toBePutOnline
    if logInitialPopulation:
        for user in channel.users:
            # create JoinEvent for this moment for users that are to be put online right now
            if user in toBePutOneline:
                event = JoinEvent(date, user, channel)
            # creates JoinEvents for offline users
            else:
                event = JoinEvent(user.getJoinDate(date), user, channel)
            queue.put(event)
    # same as 'if' case, but without creating JoinEvents for users from beginning
    else:
        for user in channel.users:
            if user in toBePutOneline:
                channel.setOnline(user)
                if user.isQuitter:
                    event = QuitEvent(user.getQuitDate(date), user, user.markovGenerator.generateReason(), channel)
                else:
                    event = LeaveEvent(user.getQuitDate(date), user, user.markovGenerator.generateReason(), channel)
            else:
                event = JoinEvent(user.getJoinDate(date), user, channel)
            queue.put(event)
    for user in channel.users:
        queue.put(MessageEvent(user.getMessageDate(date), user, helpers.flavourText(user.markovGenerator.generateMessage(), user), channel, True))

    # bulk of messages
    currentEvent = None
    day = 0
    while True:
        # if days are infinite
        if days == -1:
            # if lines aren't infinite
            if not lineMax == -1:
                # break when lines overflow total lines
                if log.totalLines >= lineMax - 1:
                    break
        try:
            currentEvent = queue.get()
            if currentEvent:
                # check if day changed, if so, write day changed message
                # TODO: make this event based?
                date = currentEvent.date
                if daycache != date.day:
                    log.writeDayChange(currentEvent.date)
                    daycache = date.day
                    day += 1
                    if days != -1 and day >= days:
                        break
                line = currentEvent.process(queue)
                if line:
                    now = datetime.datetime.utcnow()
                    if realTime and (date > now):
                        delta = date - datetime.datetime.utcnow()
                        helpers.debugPrint(str(delta.total_seconds()) + '\n')
                        time.sleep(delta.total_seconds())
                        log.write(line)
                        log.flush()
                    else:
                        log.write(line)
            else:
                sys.stderr.write("No event in queue :| (This *really* shouldn't happen)\n")
                sys.exit(1)
        except Empty:
            sys.stderr.write("No event in queue :| (This *really* shouldn't happen)\n")
            sys.exit(1)

    # write log closing message
    log.writeLogClosing(date)

    # close log file
    log.lfs[0].close()

def profileMain():
    cProfile.run('ircsimul.main()')

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        print("This script needs to be run on Python 3! (It's being tested on 3.3 currently)")
        sys.quit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--activity", help="sets intrinsic message activity per day", type=int)
    parser.add_argument("-d", "--days", help="number of days to generate, overwrites --lines", type=int)
    parser.add_argument("-l", "--lines", help="number of lines to be generated, -1 --> infinite lines", type=int)
    parser.add_argument("-m", "--metadata", help="prints metadata to file meta.log", action="store_true")
    parser.add_argument("-o", "--output", help="sets output file (if not given, logs to ircsimul.log)", type=str)
    parser.add_argument("--loginitpop", help="log initial population of channel, use Ctrl+C to quit", action="store_true")
    parser.add_argument("--debug", help="prints debug stuff", action="store_true")
    parser.add_argument("--realtime", help="toggles output to stdout", action="store_true")
    parser.add_argument("--stdout", help="toggles output to stdout", action="store_true")
    args = parser.parse_args()

    if args.lines:
        lineMax = args.lines
    else:
        lineMax = 50000

    if args.activity:
        helpers.messagesPerDay = args.activity

    if args.debug:
        helpers.debug = args.debug

    if args.output:
        logfileName = args.output
    else:
        logfileName = os.path.join(os.path.dirname(__file__), 'ircsimul.log')

    if args.days:
        days = args.days
    else:
        days = -1

    main(lineMax=lineMax, logfileName=logfileName, writeStdOut=args.stdout, realTime=args.realtime,
        logInitialPopulation=args.loginitpop, meta=args.metadata, days=days)
