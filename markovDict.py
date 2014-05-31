class MarkovDict(object):
    def __init__(self, words):
        # build morkov dictionary from given words
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
