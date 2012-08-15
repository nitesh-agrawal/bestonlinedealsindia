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


logPrefix = "rediff.py::"


class RediffParser(sgmllib.SGMLParser):
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.capture = None
        self.data = None

    def start_font(self, attributes):
        for name,value in attributes:
            if name=="id" and value=="book-pric":
                self.data = 1

    def end_font(self):
        if self.data is not None:
            self.data = None

    def start_b(self, attributes):
        if self.data is not None:
            self.capture = 1

    def end_b(self):
        if self.capture is not None:
            self.capture = None

    def handle_data(self, data):
        if self.capture==1:
            self.price = data
            raise ParsingComplete("parsing complete for rediff")

    def get_price(self):
        return self.price

class RediffThread(threading.Thread):
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
            data = getRediffData(self.isbn)
            self.result = data
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        except Exception:
            self.result = []


def getRediffData(isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.warn(logPrefix + 'start fetching data')
        isbn = isbn.decode("ASCII")

        rediff_url = "http://books.rediff.com/book/" + isbn
        
        # Get a file-like object for the Python Web site's home page.
        try: f = urllib.urlopen(rediff_url)
        except Exception:
            logging.warn('Rediff Exception while urlopen for isbn:'+isbn)
            return []

        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()

        try:
            myparser = RediffParser()
            try:
                myparser.parse(s)
            except Exception:
                logging.warn("parsing complete for rediff")
            price = myparser.get_price()
            if(price == None):
                logging.warn(logPrefix + " price is None for isbn:"+isbn)
                raise Exception(logPrefix + " price is None")
            price = price.split(".")[1]

            price = utilities.cleanInteger(price)
            price = int(price)
 
            rediff_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=rediffbooks&url=" + rediff_url.replace('&', "$")
            buynow_url = rediff_url
            rediff_data = ["Rediff Books","Rs. "+str(price),buynow_url]
            logging.warn(rediff_data)
            for s in rediff_data:
                if len(s) == 0 or s == None:
                    logging.warn(logPrefix + s + " is empty for isbn:"+isbn)
                    raise Exception(logPrefix + s + " is empty")
            return rediff_data
        except Exception:
            logging.warn("Error in parsing rediff data for isbn:"+isbn)
            return []
