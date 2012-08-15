from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
import urllib
import sgmllib
import threading
import logging
import utilities
from time import gmtime
from time import strftime

logPrefix = "simplybooks.py::"

class SimplybooksParser(sgmllib.SGMLParser):
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.flag = None
        self.found = None
        self.mrp = None
        self.mrpfound = None
        self.mrpflag = None
        
    def start_span(self, attributes):
        for name, value in attributes:
            if name == "class" and value == "rupee":
                self.flag = True
            if name == "class" and value == "rupee2":
                self.mrpflag = True

    def end_span(self):
        if self.flag is not None:
            self.flag = None
        if self.mrpflag is not None:
            self.mrpflag = None
        
    def handle_data(self, data):
        if self.flag is not None and self.found is None:
            self.price = data
            self.found = True
            raise ParsingComplete("simplybooks parsing complete")
        if self.mrpflag is not None and self.mrpfound is None:
            self.mrp = data
            self.mrpfound = True


    def get_price(self):
        if self.price is not None:
            return self.price
        else:
            return None

    def get_mrp(self):
        if self.mrp is not None:
            return self.mrp
        else:
            return None


class SimplybooksThread(threading.Thread):
    def __init__(self,isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.debug(logPrefix+"init thread")
        self.isbn = isbn
        self.result =  None
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        try:
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            data = getSimplybooksData(self.isbn)
            self.result = data
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        except Exception:
            self.result = []

def getSimplybooksData(isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.warn(logPrefix + ' warn message')
        
        isbn = isbn.decode("ASCII")

        simplybooks_url = "http://www.simplybooks.in/search.php?search_keyword=" + isbn
        
	# Get a file-like object for the Python Web site's home page.
        try:f = urllib.urlopen(simplybooks_url)
        except Exception:
            logging.warn('simplybooks Exception: '+simplybooks_url)
            return []
        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()
	# Try and process the page.
        # The class should have been defined first, remember.
        try:
            myparser = SimplybooksParser()
            try:
                myparser.parse(s)
            except Exception:
                logging.warn("Parsing complete")

            price = myparser.get_price()
            if(price == None):
                logging.warn(logPrefix+"price is None")
                raise Exception(logPrefix + " price is None")
            price = utilities.cleanInteger(price)
            price = int(price)
       
            mrp = myparser.get_mrp()
            if(mrp == None):
                logging.warn(logPrefix+"mrp is None, setting this equal to price")
                mrp = price
            mrp = utilities.cleanInteger(mrp)
            mrp = int(mrp)

            simplybooks_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=simplybooks&url=" + simplybooks_url.replace('&', "$")
            buynow_url = simplybooks_url
            simplybooks_data = ["SimplyBooks", "Rs. "+str(price), "Rs. "+str(mrp), buynow_url]
            logging.warn(simplybooks_data)
            for s in simplybooks_data:
                if len(s) == 0 or s == None:
                    logging.warn(logPrefix + s + " is empty")
                    raise Exception(logPrefix + s + " is empty")
            return simplybooks_data
        except Exception:
            logging.warn("Error in parsing simplybooks data")
            return []  

