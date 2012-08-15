from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
import urllib
import sgmllib
import logging
import threading
import utilities
from time import gmtime
from time import strftime

logPrefix = "infibeam.py::"

class InfibeamParser(sgmllib.SGMLParser):
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.captureprice = None
        self.mrp = None
        self.capturemrp = None
        self.data = None
        self.searchresult = 0
    
    def start_div(self, attributes):
        if self.searchresult > 0:
            logging.warn("incrementing from "+str(self.searchresult))
            self.searchresult = self.searchresult + 1
            
        for name, value in attributes:
            if name == "id" and value == "search_result":
                logging.warn("found search_div")
                self.searchresult = 1

    def end_div(self):
        if self.searchresult > 0:
            logging.warn("decrementing from "+ str(self.searchresult))
            self.searchresult = self.searchresult - 1
        

    def start_span(self, attributes):
        if self.searchresult > 0:
            for name,value in attributes:
                if name=="class" and value=="normal":
                    self.captureprice = 1
                if name=="class" and value=="scratch":
                    self.capturemrp = 1


    def end_span(self):
        if self.capturemrp is not None:
            self.capturemrp = None
        if self.captureprice is not None:
            self.captureprice = None


    def handle_data(self, data):
        if self.captureprice == 1:
            self.price = data
            raise ParsingComplete("infibeam parsing complete")
        if self.capturemrp == 1:
            self.mrp = data

    def get_price(self):
        return self.price

    def get_mrp(self):
        return self.mrp


class InfibeamThread(threading.Thread):
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
            data = getInfibeamData(self.isbn)
            self.result = data
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        except Exception:
            self.result = []



def getInfibeamData(isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.warn(logPrefix + 'getting infibeam data')
        isbn = isbn.decode("ASCII")

        infibeam_url = "http://www.infibeam.com/search?q=" + isbn
        
        # Get a file-like object for the Python Web site's home page.
        try: f = urllib.urlopen(infibeam_url)
        except Exception:
            logging.warn('infibeam Exception in urlopen for isbn:'+isbn)
            return []

        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()

        try: 
            myparser = InfibeamParser()
            try:
                myparser.parse(s)
            except Exception:
                logging.warn("infibeam parsing complete")

            price = myparser.get_price()
            if(price == None):
                logging.warn(logPrefix + " price is None for isbn:"+isbn)
                raise Exception(logPrefix + " price is None")
            price = utilities.cleanInteger(price)
            price = int(price)

            mrp = myparser.get_mrp()
            if(mrp == None):
                logging.warn(logPrefix + " mrp is None for isbn:"+isbn)
                mrp = price
            mrp = utilities.cleanInteger(mrp)
            mrp = int(mrp)

            infibeam_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=infibeam&url="+ infibeam_url.replace('&', "$")
            buynow_url = infibeam_url
            infibeam_data = ["Infibeam", "Rs. "+str(price), "Rs. "+str(mrp), buynow_url]
            logging.warn(infibeam_data)
            for s in infibeam_data:
                if len(s) == 0 or s == None:
                    logging.warn(logPrefix + s + " is empty for isbn:" + isbn)
                    raise Exception(logPrefix + s + " is empty")
            return infibeam_data
        except Exception:
            logging.warn(logPrefix+"exception in parsing for isbn:" + isbn)
            return []
            
