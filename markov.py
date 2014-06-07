from random import choice
import re

import helpers

# list with symbols that end a sentence
EOS = ['.', '?', '!', ':', '"']
EOL = [',', ';', '-']
EOSL = EOS + EOL

class MarkovGenerator(object):
    def __init__(self, messageFilename, reasonsFilename):
        self.messageDict = self._generateDictionary(messageFilename)
        self.messageStartList = self._generateStartList(self.messageDict)
        self.reasonsDict = self._generateDictionary(reasonsFilename)
        self.reasonsStartList = self._generateStartList(self.reasonsDict)

    def _generateDictionary(self, filename):
        # build morkov dictionary from words in given file
        words = helpers.splitFileToList(filename)
        dictionary = {}
        for i, word in enumerate(words):
            try:
                first, second, third = words[i], words[i+1], words[i+2]
            except IndexError:
                return dictionary
            key = (first, second)
            if key not in dictionary:
                dictionary[key] = []
            dictionary[key].append(third)

    def _generateStartList(self, dictionary):
        # generate possible line starts (if the first letter is uppercase)
        return [key for key in dictionary.keys() if key[0][0].isupper()]

    def _generateSentence(self, dictionary, startList, endList):
        # generates message sentence
        key = choice(startList)
        sentenceList = []

        first, second = key
        sentenceList.append(first)
        sentenceList.append(second)
        while True:
            try:
                third = choice(dictionary[key])
            except KeyError:
                return ' '.join(sentenceList)
            sentenceList.append(third)
            if third[-1] in endList:
                return ' '.join(sentenceList)
            key = (second, third)
            first, second = key

    def generateMessages(self):
        return [i for i in re.split("[,;\-]", self._generateSentence(self.messageDict, self.messageStartList, EOS)) if i]

    def generateMessage(self):
        return self._generateSentence(self.messageDict, self.messageStartList, EOSL)

    def generateReason(self):
        return self._generateSentence(self.reasonsDict, self.reasonsStartList, EOSL)
