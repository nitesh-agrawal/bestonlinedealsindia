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

logPrefix = "bookadda.py::"

class BookaddaParser(sgmllib.SGMLParser):
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.data = None
        self.flag = None
        self.mrp = None
        self.mrpflag = None
        self.mrpdata = None
        
    def start_span(self, attributes):
        for name, value in attributes:
            if name == "class" and value == "new_price":
                self.flag = True
            if name == "class" and value == "old_price":
                self.mrpflag = True
            

    def end_span(self):
        self.flag = None

    def start_s(self, attributes):
        if self.mrpflag is not None:
            self.mrpdata = True

    def end_s(self):
        if self.mrpdata is not None:
            self.mrpdata = None
            self.mrpflag = None
        
    def start_strong(self, attributes):
        if self.flag == True:
            self.data = True

    def end_strong(self):
        if self.data is not None:
            self.data = None
        
    def handle_data(self, data):
        if self.data is not None:
            self.price = data
            raise ParsingComplete("parsing complete for bookadda")
        if self.mrpdata is not None:
            self.mrp = data

    def get_price(self):
        if self.price is not None:
            return self.price.split(".")[1]
        else:
            return None

    def get_mrp(self):
        if self.mrp is not None:
            return self.mrp.split(".")[1]
        else:
            return None


class BookaddaThread(threading.Thread):
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
            data = getBookaddaData(self.isbn)
            self.result = data
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        except Exception:
            self.result = []

def getBookaddaData(isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.warn(logPrefix + 'start fetching data')
        
        isbn = isbn.decode("ASCII")

        bookadda_url = "http://www.bookadda.com/general-search?searchkey=" + isbn
        # Get a file-like object for the Python Web site's home page.
        try:f = urllib.urlopen(bookadda_url)
        except Exception:
            logging.warn('bookadda Exception')
            return []

        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()

        try:
            myparser = BookaddaParser()
            try:
                myparser.parse(s)
            except:
                logging.warn("parsing complete for bookadda")
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
            
            bookadda_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=bookadda&url=" + bookadda_url.replace('&', "$")
            buynow_url = bookadda_url
            bookadda_data = ["BookAdda", "Rs. " + str(price), "Rs. " + str(mrp), buynow_url]
            logging.warn(bookadda_data)
            for s in bookadda_data:
                if len(s) == 0 or s == None:
                    logging.warn(logPrefix + s + " is empty for isbn:"+isbn)
                    raise Exception(logPrefix + s + " is empty")
            return bookadda_data
        except Exception:
            logging.warn(logPrefix+"Error in parsing bookadda data for isbn:"+isbn)
            return []  

