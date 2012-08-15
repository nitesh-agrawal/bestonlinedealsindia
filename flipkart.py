from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
import urllib
import sgmllib
import logging
import utilities
from time import gmtime
from time import strftime


logPrefix = "flipkart.py::"


class FlipkartParser(sgmllib.SGMLParser):
    "A simple parser class."
    def parse(self, s):
        "Parse the given string 's'."
        logging.warn(logPrefix+"starting to parse")
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.price = None
        self.mrp = None
        self.publishername = None
        self.bookname = None
        self.thumbnail = None
        self.authorname = []

        self.data = None
        self.mrpdata = None
        self.pricedata = None
        self.booknamedata = None
        self.publisherdata2 = None
        self.publisherdata = None
        self.authornamedata = None
        
        logging.warn(logPrefix+"init complete")

    def start_div(self, attributes):
        for name, value in attributes:
            if name == "id" and value == "productpage-price":
                self.data = 1
            if name == "id" and value == "product_specs":
                self.publisherdata = 1
            if name == "class" and value == "product_page_title":
                self.authornamedata = 1

    def start_h2(self, attributes):
        if self.authornamedata == 1:
            self.authornamedata = 2

    def start_b(self, attributes):
        if self.authornamedata == 2:
            self.authornamedata = 3

    def end_b(self):
        if self.authornamedata == 3:
            self.authornamedata = None

    def start_del(self, attributes):
        if self.data is not None:
           self.mrpdata = 1
               


    def start_span(self, attributes):
        for name, value in attributes:
            if self.data is not None:
                if name=="class" and value=="sp":
                    self.pricedata = 1
                    self.data = None
                    if self.mrp == None:
                        self.mrpdata = 1 
            if name=="property" and value=="dc:title":
                self.booknamedata = 1

    def start_img(self, attributes):
        found=None
        for name, value in attributes:
            if name == "class" and value == "search_page_image":
                found = True
        for name, value in attributes:
            if found == True and name == "src":
                self.thumbnail = value
                found = None

    def handle_data(self, data):
        if self.mrpdata is not None:
            self.mrp = data
            self.mrpdata = None
        if self.pricedata is not None:
            self.price = data
            self.pricedata = None
        if self.booknamedata is not None:
            self.bookname = data
            self.booknamedata = None
        if self.publisherdata2 is not None:
            self.publishername = data
            self.publisherdata = None
            self.publisherdata2 = None
        if self.publisherdata is not None:
            if data == "Publisher:":
                self.publisherdata2 = 1
        if self.authornamedata == 3:
            self.authorname.append(data.strip())
        

    def get_price(self):
        return self.price.strip()

    def get_mrp(self):
        return self.mrp.strip()

    def get_publishername(self):
        return self.publishername

    def get_bookname(self):
        return self.bookname

    def get_authorname(self):
        return self.authorname

    def get_thumbnail(self):
        return self.thumbnail

def getFlipkartData(isbn):
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/tmp/myapp.log',
                    filemode='w')
        logging.warn(logPrefix + ' starting flipkart parsing')

        isbn = isbn.decode("ASCII")
        flipkart_url = "http://www.flipkart.com/m/search-all?query="+isbn;
        # Get a file-like object for the Python Web site's home page.
        try:
            f = urllib.urlopen(flipkart_url)
            logging.warn('flipkart after urlopen')

        except Exception:
            logging.warn('flipkart Exception in urlopen')
            return []

        # Read from the object, storing the page's contents in 's'.
        s = f.read()
        f.close()
        logging.warn("read flipkart data")
        # Try and process the page.
        # The class should have been defined first, remember.
        try:
#        if True:
            myparser = FlipkartParser()
            logging.warn("starting the parser")
            myparser.parse(s)
            logging.warn("parsing complete")
            price = myparser.get_price()
            if(price == None):
                logging.warn(logPrefix + " price is None")
                raise Exception(logPrefix + " price is None")
            mrp = myparser.get_mrp()
            if(mrp == None):
                logging.warn(logPrefix + " mrp is None")
                raise Exception(logPrefix + " mrp is None")
            authornames = myparser.get_authorname()
            if(len(authornames) == 0):
                logging.warn(logPrefix + " author is None")
                raise Exception(logPrefix + " No author Names")
            display_author = None
            for author in authornames:
                if display_author == None:
                    display_author = author
                else:
                    display_author = display_author + " " + author
            bookname = myparser.get_bookname()
            if(bookname == None):
                logging.warn(logPrefix + " bookname is None")
                raise Exception(logPrefix + " bookname is None")
            thumbnail = myparser.get_thumbnail()
            if(thumbnail == None):
                logging.warn(logPrefix + " thumbnail is None")
                raise Exception(logPrefix + " thumbnail is None")

            flipkart_url = "http://www.flipkart.com/books/" + isbn + "?affid=vdhawalgma"
            flipkart_url = "http://bestonlinedealsindia.appspot.com/redirect?isbn="+isbn+"&vendor=flipkart&url=" + flipkart_url.replace('&', "$")
            buynow_url = flipkart_url

            price_val = int(price.split(" ")[1])
            price_val = utilities.cleanInteger(price_val)
            price_val = int(price_val)

            mrp_val = int(mrp.split(" ")[1])
            discount = (mrp_val - price_val)*100/mrp_val


            flipkart_data = [isbn,bookname,display_author,"",thumbnail,"Flipkart",str(price),str(mrp),str(discount)+"%", buynow_url]
            return flipkart_data
        except Exception:
            logging.warn("Error in parsing flipkart data")
            return []


