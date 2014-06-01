from random import choice

import helpers

# list with symbols that end a sentence
EOS = ['.', '?', '!', ':', '"', ':', ',', ';']

class MarkovGenerator(object):
    def __init__(self, filename):
        # build morkov dictionary from words in given file
        words = helpers.splitFileToList(filename)
        self.dictionary = {}
        for i, word in enumerate(words):
            try:
                first, second, third = words[i], words[i+1], words[i+2]
            except IndexError:
                break
            key = (first, second)
            if key not in self.dictionary:
                self.dictionary[key] = []
            self.dictionary[key].append(third)

        # generate possible line starts (if the first letter is uppercase)
        self.startList = [key for key in self.dictionary.keys() if key[0][0].isupper()]

    # TODO: create writeListWithFlavour to remove need to join up string?
    def generateSentence(self):
        # generates message sentence
        key = choice(self.startList)
        sentenceList = []

        first, second = key
        sentenceList.append(first)
        sentenceList.append(second)
        while True:
            try:
                third = choice(self.dictionary[key])
            except KeyError:
                return ' '.join(sentenceList)
            sentenceList.append(third)
            if third[-1] in EOS:
                return ' '.join(sentenceList)
            key = (second, third)
            first, second = key
