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

def debugPrint(text):
    if debug:
        sys.stderr.write(text)

def splitFileToList(filename):
    # split text in file to list of words
    f = open(filename, 'rt', encoding='utf8')
    splitList = f.read().split()
    f.close()
    return splitList

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
            debugPrint("ERROR: false flavourType assigned")
            return "ERROR: false flavourType assigned"
    else:
        return text.lstrip()
