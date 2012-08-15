from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
import urllib
import sgmllib
import logging
import utilities
from time import gmtime
from time import strftime


logPrefix = "flipkart_search.py::"


class FlipkartSearchParser(sgmllib.SGMLParser):
    "A simple parser class."
    def parse(self, s):
        "Parse the given string 's'."
        logging.warn(logPrefix+"starting to parse")
        self.feed(s)
        self.close()
    
    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."
        
        sgmllib.SGMLParser.__init__(self, verbose)
        self.bookname = []
        self.thumbnail = []
        self.authorname = []
        self.authornames = []
        self.isbns = []
        
        self.data = None
        self.captureName = None
        self.maindata = None
        self.captureAuthorName = None
        self.foundisbn = None

        self.searchcount = 0
        
        logging.warn(logPrefix+"init complete")
    
    def start_div(self, attributes):
        for name, value in attributes:
            if name == "id" and value == "search_results":
                self.data = 1
            if self.data is not None:
                if name == "class" and str(value).startswith("fk-srch-item"):
                    self.maindata = 1
                    logging.warn("inside maindata" + str(self.searchcount))
                    self.foundisbn = None
            if self.maindata is not None:
                if name == "class" and str(value).endswith("fk-sitem-info-section"):
                    self.authorname.append(",".join(self.authornames))
                    self.authornames = []
                    self.maindata = None
                    self.searchcount += 1
    
    
    def start_a(self, attributes):
        if self.maindata == 1:
            for name, value in attributes:
                if name == "class" and str(value).startswith("fk-srch-title-text"):
                    self.captureName = 1
                if name == "href":
                    if str(value).startswith("/author"):
                        self.captureAuthorName = 1
                    elif self.foundisbn is None:
                        startregex = "pid="
                        endregex = "&"
                        ISBN = value.split(startregex)[1].split(endregex)[0]
                        logging.warn("ISBN="+ISBN)
                        self.isbns.append(ISBN)
                        self.foundisbn = 1
                    
            
    
    def start_img(self, attributes):
        if self.maindata == 1:
            for name, value in attributes:
                if name == "src":
                    self.thumbnail.append(value)
    
    def handle_data(self, data):
        if self.captureName is not None:
            self.bookname.append(data)
            self.captureName = None
        
        if self.captureAuthorName is not None:
            self.authornames.append(data)
            self.captureAuthorName = None
    
    def get_isbn(self):
        return self.isbns
    
    def get_bookname(self):
        return self.bookname
    
    def get_authorname(self):
        return self.authorname
    
    def get_thumbnail(self):
        return self.thumbnail

    def get_searchcount(self):
        return self.searchcount


def getFlipkartSearchData(query):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='/tmp/myapp.log',
                        filemode='w')
    logging.warn(logPrefix + ' starting flipkart search parsing for query = ' + query)
    
    flipkartSearchUrl = "http://www.flipkart.com/search/a/books?vertical=books&query="+query
    # Get a file-like object for the Python Web site's home page.
    try:
        f = urllib.urlopen(flipkartSearchUrl)
        logging.warn('flipkart after urlopen')
    
    except Exception:
        logging.warn('flipkart Exception in urlopen')
        return []
    
    # Read from the object, storing the page's contents in 's'.
    s = f.read()
    f.close()
    logging.warn("read flipkart search data")
    # Try and process the page.
    # The class should have been defined first, remember.
    try:
#    if True:
        myparser = FlipkartSearchParser()
        logging.warn("starting the parser")
        myparser.parse(s)
        logging.warn("parsing complete")
        
        authornames = myparser.get_authorname()
        logging.warn(",".join(authornames))
        if(authornames == None):
            logging.warn(logPrefix + " authors is None")
            raise Exception(logPrefix + " No author Names")
        booknames = myparser.get_bookname()
        logging.warn(",".join(booknames))
        if(booknames == None):
            logging.warn(logPrefix + " bookname is None")
            raise Exception(logPrefix + " bookname is None")
        thumbnails = myparser.get_thumbnail()
        logging.warn(",".join(thumbnails))
        if(thumbnails == None):
            logging.warn(logPrefix + " thumbnail is None")
            raise Exception(logPrefix + " thumbnail is None")
        isbns = myparser.get_isbn()
        logging.warn(",".join(isbns))
        if(isbns == None):
            logging.warn(logPrefix + " isbn is None")
            raise Exception(logPrefix + " isbn is None")
        count = myparser.get_searchcount()

        result = []
        for i in range(count):
            flipkart_search_data = [isbns[i],booknames[i],authornames[i],thumbnails[i]]
            result.append(flipkart_search_data)

        return result
    except Exception:
        logging.warn("Error in parsing flipkart search data")
        return []


