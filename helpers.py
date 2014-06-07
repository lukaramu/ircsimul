import string
import sys
from random import random

import userTypes

messagesPerDay = 5000
debug = False

# create translation maps for modifying strings
removePunctuationMap = str.maketrans('', '', string.punctuation)
removePunctuationAndUpperCaseMap = str.maketrans(string.ascii_uppercase, string.ascii_lowercase, string.punctuation)
noVocalMap = str.maketrans('', '', 'aeiou')

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
            return text.translate(removePunctuationAndUpperCaseMap)
        elif user.userType == userTypes.standard:
            return text
        elif user.userType == userTypes.lowercase:
            return text.lower()
        elif user.userType == userTypes.uppercase:
            return text.upper()
        elif user.userType == userTypes.noPunctuation:
            return text.translate(removePunctuationMap)
        elif user.userType == userTypes.txtSpeech:
            return text.translate(noVocalMap)
        else:
            return text
    else:
        return "ERROR: false flavourType assigned"
