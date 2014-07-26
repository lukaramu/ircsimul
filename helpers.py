import os
import string
import sys
from random import random

import userTypes

messagesPerDay = 5000
debug = False

# create translation maps for modifying strings
removePunctuationMap = str.maketrans('', '', string.punctuation)
removePunctuationAndUpperCaseMap = str.maketrans(string.ascii_uppercase, string.ascii_lowercase, string.punctuation)
noVocalMap = str.maketrans('', '', 'aeiouAEIOU')

days = ['Mon', 'Tue', 'Wed', 'Thu','Fri', 'Sat', 'Sun']
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def debugPrint(text):
    if debug:
        sys.stderr.write(text)

def splitFileToList(filename):
    # split text in file to list of words
    f = open(filename, 'rt', encoding='utf8')
    splitList = f.read().split()
    f.close()
    return splitList

# user/host source files:
userfileName = os.path.join(os.path.dirname(__file__), 'users.txt')
prefixfileName = os.path.join(os.path.dirname(__file__), 'adjectives.txt')
nounfileName = os.path.join(os.path.dirname(__file__), 'nouns.txt')
placesfileName = os.path.join(os.path.dirname(__file__), 'places.txt')

userList = splitFileToList(userfileName)
prefixList = splitFileToList(prefixfileName)
nounList = splitFileToList(nounfileName)
placesList = splitFileToList(placesfileName)

def flavourText(text, user):
    # returns text with 'flavour'
    if random() < userTypes.useProbabilities[user.userType]:
        if user.userType == userTypes.lowercaseNoPunctuation:
            return text.translate(removePunctuationAndUpperCaseMap).lstrip()
        elif user.userType == userTypes.standard:
            return text.lstrip()
        elif user.userType == userTypes.lowercase:
            return text.lower().lstrip()
        elif user.userType == userTypes.uppercase:
            return text.upper().lstrip()
        elif user.userType == userTypes.noPunctuation:
            return text.translate(removePunctuationMap).lstrip()
        elif user.userType == userTypes.txtSpeech:
            return text.translate(noVocalMap).lstrip()
        else:
            sys.stderr.write("ERROR:   flavourType out of range")
            sys.exit(1)
            return "ERROR:   false flavourType assigned"
    else:
        return text.lstrip()

def _zf(arg):
    # zfills string to given argument
    return str(arg).zfill(2)

def generateFullTimeStamp(date):
    return "{0} {1} {2} {3}:{4}:{5} {6}".format(days[date.weekday()],
                                                months[date.month - 1],
                                                _zf(date.day),
                                                _zf(date.hour),
                                                _zf(date.minute),
                                                _zf(date.second),
                                                str(date.year))

def generateDate(date):
    return ' '.join([days[date.weekday()], months[date.month - 1], _zf(date.day), str(date.year)])
