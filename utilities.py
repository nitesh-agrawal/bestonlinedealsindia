def cleanInteger(inputdata):
    if inputdata is not None:
        return str(inputdata).replace(',','')
    else:
        return None

class ParsingComplete(Exception):
       def __init__(self, value):
           self.parameter = value
       def __str__(self):
           return repr(self.parameter)


