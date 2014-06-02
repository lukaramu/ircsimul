import string

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
