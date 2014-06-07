import string

import userTypes

def makeTransMaps():
    # creates translation maps for modifying string
    global removePunctuationMap
    removePunctuationMap = str.maketrans('', '', string.punctuation)
    global removePunctuationAndUpperCaseMap
    removePunctuationAndUpperCaseMap = str.maketrans(string.ascii_uppercase, string.ascii_lowercase, string.punctuation)
    global noVocalMap
    noVocalMap = str.maketrans('', '', 'aeiou')

def splitFileToList(filename):
    # split text in file to list of words
    f = open(filename, 'rt', encoding='utf8')
    splitList = f.read().split()
    f.close()
    return splitList

def flavourText(text, user):
    # returns text with 'flavour'
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
        return "ERROR: false flavourType assigned"
