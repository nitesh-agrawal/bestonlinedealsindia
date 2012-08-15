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


logPrefix = "landmarks.py::"

class LandMarkParser(sgmllib.SGMLParser):
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.data = None
        self.counter = None
        self.mrp = None
        self.mrpdata = None
        self.mrpcounter = None
        
    def start_span(self, attributes):
        for name, value in attributes:
            if(self.counter is not None):
                self.counter = self.counter+1
            if name == "class" and value == "current-price":
                self.counter = 1
            if(self.mrpcounter is not None):
                self.mrpcounter = self.mrpcounter+1
            if name == "class" and value == "old-price":
                self.mrpcounter = 1

    def end_span(self):
        if(self.counter is not None):
            self.counter = self.counter-1
        if(self.mrpcounter is not None):
            self.mrpcounter = self.mrpcounter-1
        
    def handle_data(self, data):
        if(self.counter == 1):
            self.price = data
            self.counter = None
            raise ParsingComplete("parsing complete")
        if(self.mrpcounter == 1):
            self.mrp = data
            self.mrpcounter = None

    def get_mrp(self):
        return self.mrp
    def get_price(self):
        return self.price


class LandmarkThread(threading.Thread):
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
            data = getLandmarkData(self.isbn)
            self.result = data
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        except Exception:
            self.result = []

def getLandmarkData(isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.warn(logPrefix + 'start fetching data')
        
        isbn = isbn.decode("ASCII")

        landmark_url = "http://www.landmarkonthenet.com/books/search/?q=" + isbn
        
	# Get a file-like object for the Python Web site's home page.
        try:f = urllib.urlopen(landmark_url)
        except Exception:
            logging.warn('landmarks Exception in urlopen for isbn'+isbn)
            return []

        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()

        try:
            myparser = LandMarkParser()
            try:
                myparser.parse(s)
            except:
                logging.warn("landmarks parsing complete")
            
            #get the price
            price = myparser.get_price()
            if(price == None):
                logging.warn(logPrefix + " price is None for isbn:"+isbn)
                raise Exception(logPrefix + " price is None")

            price = utilities.cleanInteger(price)
            price = int(price)

            #get the mrp
            mrp = myparser.get_mrp()
            if(mrp == None):
                logging.warn(logPrefix + " mrp is None for isbn:"+isbn)
                raise Exception(logPrefix + " mrp is None")

            mrp = utilities.cleanInteger(mrp)
            mrp = int(mrp)

            landmark_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=landmark&url=" + landmark_url.replace('&', "$")
            buynow_url = landmark_url
            landmark_data = ["Landmark", "Rs. " + str(price), "Rs. " + str(mrp), buynow_url]
            logging.warn(landmark_data)
            for s in landmark_data:
                if len(s) == 0 or s == None:
                    logging.warn(logPrefix + s + " is empty for isbn:"+isbn)
                    raise Exception(logPrefix + s + " is empty")
            return landmark_data
        except Exception:
            logging.warn("Error in parsing landmark data for isbn:"+isbn)
            return []  

