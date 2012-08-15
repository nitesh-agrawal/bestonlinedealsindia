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


logPrefix = "indiaplaza.py"





class IndiaplazaParser(sgmllib.SGMLParser):
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.data = None
        self.mrp = None
        self.mrpdata = None

    def start_span(self, attributes):
        for name,value in attributes:
            if name=="class" and value=="blueFont":
                self.data = 1

    def start_div(self, attributes):
        for name,value in attributes:
            if name=="class" and value=="mrp":
                self.mrpdata = 1


    def handle_data(self, data):
        if self.data==1:
            self.price = data
            logging.warn("raising exception now")
            raise ParsingComplete("parsing complete")
            self.data = None
        if self.mrpdata==1:
            self.mrp = data
            self.mrpdata = None

    def get_price(self):
        return self.price

    def get_mrp(self):
        return self.mrp

class IndiaplazaThread(threading.Thread):
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
            data = getIndiaplazaData(self.isbn)
            self.result = data
            logging.warn(logPrefix+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        except Exception:
            self.result = []

def getIndiaplazaData(isbn):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            filename='/tmp/myapp.log',
            filemode='w')
        logging.warn(logPrefix + 'start fetching data')
        
        isbn = isbn.decode("ASCII")

        indiaplaza_url = "http://www.indiaplaza.com/searchproducts.aspx?sn=books&affid=133884&q=" + isbn
        
        # Get a file-like object for the Python Web site's home page.
        try: f = urllib.urlopen(indiaplaza_url)
        except Exception:
            logging.warn('indiaplaza Exception in urlopen for isbn:'+isbn)
            return []
        


        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()

        try:
            myparser = IndiaplazaParser()
            try:
                myparser.parse(s)
            except Exception:
                logging.error( "Error in parsing " )

            #get the price
            price = myparser.get_price()
            if(price == None):
                logging.warn(logPrefix + " price is None for isbn:"+isbn)
                raise Exception(logPrefix + " price is None")

            price = price.split(".")[1]
            price = utilities.cleanInteger(price)
            price = int(price)

            #get the mrp
            mrp = myparser.get_mrp()
            if(mrp == None):
                logging.warn(logPrefix + " mrp is None for isbn:"+isbn)
                raise Exception(logPrefix + " mrp is None")

            mrp = mrp.split(".")[1]
            mrp = utilities.cleanInteger(mrp)
            mrp = int(mrp)

            indiaplaza_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=indiaplaza&url=" + indiaplaza_url.replace('&', "$")
            buynow_url = indiaplaza_url
            indiaplaza_data = ["Indiaplaza", "Rs. " + str(price), "Rs. " + str(mrp), buynow_url]
            logging.warn(indiaplaza_data)
            for s in indiaplaza_data:
                if len(s) == 0 or s == None:
                    logging.warn(logPrefix + s + " is empty for isbn:"+isbn)
                    raise Exception(logPrefix + s + " is empty")
            return indiaplaza_data
        except Exception:
            logging.warn("Error in parsing indiaplaza data for isbn:"+isbn)
            return []
            
