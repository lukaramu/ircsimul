import argparse
import datetime
import logging
import cProfile
import sys
from math import sin, pi
from random import choice, random
from queue import PriorityQueue, Empty
import time

import helpers
import markov
from channel import Channel
from user import User
from log import Log
import userTypes
from events import KickEvent, LeaveEvent, QuitEvent, JoinEvent, MessageEvent, UserActionEvent

# TODO: event based system: http://pastebin.com/Nw854kcf
# TODO: implement per-user event creation (e.g.)

# TODO: <starfire> loops are bad always put a base case!!
# TODO: check if activity is correct
# TODO: instead of/additionally to truncating lines at commas, spread message out over seperate messages
# might be cool: having them ping each other in "conversations" where only the last N messages of the person they are pinging are used in the generator so the conversation is "topical"

# new features:
# TODO: realtime output
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

# TODO: create a function that simulates this behavior with fluid numbers after being given a general activity.
# TODO: tweak activity: currently 1,000,000 lines go from May 29 2014 to Apr 05 2023
# possible timedeltas after messages
timeSpan = [5, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 10, 10, 10, 10, 12, 15, 20, 30, 30, 30, 20, 60, 120, 300, 600]

# END flags and sizes

# TODO: move flavouring to message generation in User
def flavourText(text, user):
    # returns text with 'flavour'
    if user.userType == userTypes.lowercaseNoPunctuation:
        return text.translate(helpers.removePunctuationAndUpperCaseMap)
    elif user.userType == userTypes.standard:
        return text
    elif user.userType == userTypes.lowercase:
        return text.lower()
    elif user.userType == userTypes.uppercase:
        return text.upper()
    elif user.userType == userTypes.noPunctuation:
        return text.translate(helpers.removePunctuationMap)
    elif user.userType == userTypes.txtSpeech:
        return text.translate(helpers.noVocalMap)
    else:
        return "ERROR: false flavourType assigned"

def main(lineMax=5000, logfileName='ircsimul.log', writeStdOut=False, realTime=False, 
    logInitialPopulation=False):
    # create character maps for various text processing/writing functions
    helpers.makeTransMaps()

    # load up markov generator
    markovGenerator = markov.MarkovGenerator(sourcefileName, reasonsfileName)

    # load channel
    channel = Channel(channelName, markovGenerator, initialUserCount)

    # open log
    fileObjectList = []
    fileObjectList.append(open(logfileName, 'wt', encoding='utf8'))
    if writeStdOut:
        fileObjectList.append(sys.stdout)
    log = Log(fileObjectList)

    # get current date
    date = datetime.datetime.utcnow()

    daycache = date.day

    # create queue
    queue = PriorityQueue()

    # write opening of log
    log.writeLogOpening(date)

    # populates channel with initialPopulation users
    if logInitialPopulation:
        for i in range(0, initialPopulation):
            event = JoinEvent(date, channel.selectOfflineUser(), channel)
            queue.put(event)
    else:
        for i in range(0, initialPopulation):
            channel.setOnline(channel.selectOfflineUser())

    # bulk of messages
    currentEvent = None
    while True:
        if not lineMax == -1:
            if log.totalLines >= lineMax - 1:
                break
        # empty queue
        try:
            while not queue.empty():
                currentEvent = queue.get()
                if currentEvent:
                    line = currentEvent.process()
                    if line:
                        now = datetime.datetime.utcnow()
                        if realTime and (currentEvent.date > now):
                            delta = currentEvent.date - datetime.datetime.utcnow()
                            print(str(delta.total_seconds()))
                            time.sleep(delta.total_seconds())
                            log.write(line)
                            log.flush()
                        else:
                            log.write(line)
                else: break
        except Empty:
            pass

        # check if day changed, if so, write day changed message
        # TODO: make this event based
        if daycache != date.day:
            log.writeDayChange(date)
            daycache = date.day

        # generate line
        determineType = random()
        if determineType > joinPartProbability:
            # user message
            user = channel.selectOnlineUser()
            event = MessageEvent(date, user, flavourText(markovGenerator.generateMessage(), user))
        elif determineType > actionProbability:
            # random join/part event
            user = channel.selectUser()
            if user in channel.online:
                if random() < quitProbability:
                    event = QuitEvent(date, user, markovGenerator.generateReason(), channel)
                else:
                    event = LeaveEvent(date, user, markovGenerator.generateReason(), channel)
            else:
                event = JoinEvent(date, user, channel)
        elif determineType > kickProbability:
            # user action
            # TODO: implement variable user action text
            event = UserActionEvent(date, channel.selectOnlineUser(), "does action")
        else:
            # kick event
            event = KickEvent(date, channel.selectOnlineUser(), channel.selectOnlineUser(), markovGenerator.generateReason(), channel)
        queue.put(event)

        # makes sure some amount of peeps are online or offline
        # TODO: check if population checks could be made obsolete by having the next join/parts already cached
        # TODO: move to channel class later?
        if channel.onlineUsers < minOnline:
            event = JoinEvent(date, channel.selectOfflineUser(), channel)
            queue.put(event)
        if (channel.userCount - channel.onlineUsers) < minOffline:
            if random() < quitProbability:
                event = QuitEvent(date, user, markovGenerator.generateReason(), channel)
            else:
                event = LeaveEvent(date, user, markovGenerator.generateReason(), channel)
            queue.put(event)

        # TODO: is += possible here?
        date = date + datetime.timedelta(seconds = choice(timeSpan) * (sin((date.hour) / 24 * pi) + 1.5))

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
    parser.add_argument("-l", "--lines", help="number of lines to be generated, -1 --> infinite lines", type=int)
    parser.add_argument("-o", "--output", help="sets output file (if not given, logs to ircsimul.log)", type=str)
    parser.add_argument("--stdout", help="toggles output to stdout", action="store_true")
    parser.add_argument("--realtime", help="toggles output to stdout", action="store_true")
    parser.add_argument("--loginitpop", help="log initial population of channel, use Ctrl+C to quit", action="store_true")
    args = parser.parse_args()

    # TODO: make this less messy
    if args.lines:
        lineMax = args.lines
    else:
        lineMax = 50000
    if args.output:
        logfileName = args.output
    else:
        logfileName = 'ircsimul.log'

    main(lineMax=lineMax, logfileName=logfileName, writeStdOut=args.stdout, realTime=args.realtime,
        logInitialPopulation=args.loginitpop)
