#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from google.appengine.ext import db
from google.appengine.ext.webapp import util
import urllib
import sgmllib
import logging
import string
import threading
from datetime import datetime

import flipkart
import landmarks
import rediff
import infibeam
import indiaplaza
import bookadda
import simplybooks
import utilities
import flipkart_search

logPrefix = "Main.py::"

class DetailDB(db.Model):
    vendor_name = db.StringProperty()
    price = db.StringProperty()
    discount = db.StringProperty()
    mrp = db.StringProperty()
    buy_now_url = db.TextProperty()

    

class IsbnDB(db.Model):
    isbn = db.StringProperty()
    name = db.StringProperty()
    author = db.StringProperty()
    publisher = db.StringProperty()
    all_vendors = db.ListProperty(db.Key)
    thumbnail_url = db.TextProperty()
    created = db.DateTimeProperty()

class IsbnMetricsDB(db.Model):
    isbn = db.StringProperty()
    hits = db.IntegerProperty()
    redirecttoflipkart = db.IntegerProperty()
    redirecttoindiaplaza = db.IntegerProperty()
    redirecttoinfibeam = db.IntegerProperty()
    redirecttorediff = db.IntegerProperty()
    redirecttobookadda = db.IntegerProperty()
    redirecttosimplybooks = db.IntegerProperty()
    redirecttolandmark = db.IntegerProperty()

class VendorMetricDB(db.Model):
    vendorname = db.StringProperty()
    resultcount = db.IntegerProperty()
    topresult = db.IntegerProperty()



class MainHandler(webapp2.RequestHandler):
    def get(self):
        inputisbn = self.request.get("isbn")
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/tmp/myapp.log',
                    filemode='w')

        #log the metric for this request
        metricquery = IsbnMetricsDB.gql("WHERE isbn = :1",inputisbn)
        isbnmetricsdata = metricquery.get()
        if(not isbnmetricsdata):
            isbnmetricsdata = IsbnMetricsDB()
            isbnmetricsdata.hits = 0
            isbnmetricsdata.isbn = inputisbn            
            isbnmetricsdata.redirecttoflipkart = 0
            isbnmetricsdata.redirecttoindiaplaza = 0
            isbnmetricsdata.redirecttoinfibeam = 0
            isbnmetricsdata.redirecttorediff = 0
            isbnmetricsdata.redirecttobookadda = 0
            isbnmetricsdata.redirecttosimplybooks = 0
            isbnmetricsdata.redirecttolandmark = 0
        isbnmetricsdata.hits += 1
        isbnmetricsdata.put()

        #check in isbn DB first
        query = IsbnDB.gql("WHERE isbn = :1", inputisbn)
        isbndata = query.get()
        current_time = datetime.now()
        fetchDataAgain = False
        if(isbndata):
            date_created = isbndata.created
            if (current_time-date_created).days > 3:
                #delete the older entry along with all the associated entries in DetailDB table
                db.delete(isbndata.all_vendors)
                isbndata.all_vendors = []
                fetchDataAgain = True
            
            
        newBook = None
        if(fetchDataAgain == True or not isbndata):
            logging.warn("calling flipkart")
            flipkart_data = flipkart.getFlipkartData(inputisbn)
            logging.warn("called flipkart")
            logging.warn(flipkart_data)
            if(len(flipkart_data)>0):
                logging.warn(flipkart_data)
                
                #if this is the first time for this book, persist all info
                if (not isbndata):
                    newBook = IsbnDB()
                    newBook.isbn = flipkart_data[0]
                    newBook.name = flipkart_data[1].strip('\n')
                    newBook.author = flipkart_data[2].strip('\n')
                    newBook.thumbnail_url = flipkart_data[4]
                    
                #else reuse the old data
                else:
                    newBook = isbndata

                newBook.created = current_time

                flipkartmetricquery = VendorMetricDB.gql("WHERE vendorname = :1", "flipkart")
                flipkartmetricdata = flipkartmetricquery.get()
                if(not flipkartmetricdata):
                    flipkartmetricdata = VendorMetricDB()
                    flipkartmetricdata.vendorname = "flipkart"
                    flipkartmetricdata.resultcount = 0
                    flipkartmetricdata.topresult = 0
                flipkartmetricdata.resultcount += 1
                flipkartmetricdata.put()

                flipkart_details = DetailDB()
                flipkart_details.vendor_name = flipkart_data[5].strip('\n')
                flipkart_details.price = flipkart_data[6]
                flipkart_details.mrp = flipkart_data[7]
                flipkart_details.discount = flipkart_data[8]
                flipkart_details.buy_now_url = flipkart_data[9]
                flipkart_details.put()
                newBook.all_vendors.append(flipkart_details.key())                

                #spawn all the parsing threads
                landmarkThread = landmarks.LandmarkThread(inputisbn)
                rediffThread = rediff.RediffThread(inputisbn)
                infibeamThread = infibeam.InfibeamThread(inputisbn)
                indiaplazaThread = indiaplaza.IndiaplazaThread(inputisbn)
                bookaddaThread = bookadda.BookaddaThread(inputisbn)
                simplybooksThread = simplybooks.SimplybooksThread(inputisbn)

                landmarkThread.start()
                simplybooksThread.start()
                bookaddaThread.start()
                indiaplazaThread.start()
                infibeamThread.start()
                rediffThread.start()
                
                #wait for all threads
                simplybooksThread.join()
                bookaddaThread.join()
                indiaplazaThread.join()
                infibeamThread.join()     
                rediffThread.join()
                landmarkThread.join()

         




                #gather data from landmark
                #landmark_data = landmarks.getLandMarkData(inputisbn)
                landmark_data = landmarkThread.get_result()
                if(len(landmark_data)>0):
                    landmark_details = DetailDB()
                    landmark_details.vendor_name = landmark_data[0]
                    landmark_details.price = landmark_data[1]
                    landmark_details.mrp = landmark_data[2]
                    landmark_details.buy_now_url = landmark_data[3]   
                    landmark_price = (landmark_details.price.split(" ")[1])
                    price_val = int(utilities.cleanInteger(landmark_price))
                    mrp_val = int(landmark_details.mrp.split(" ")[1])
                    landmark_details.discount = str((mrp_val - price_val)*100/mrp_val)+"%"
                    landmark_details.put()
                    newBook.all_vendors.append(landmark_details.key())

                    landmarkmetricquery = VendorMetricDB.gql("WHERE vendorname = :1", "landmark")
                    landmarkmetricdata = landmarkmetricquery.get()
                    if(not landmarkmetricdata):
                        landmarkmetricdata = VendorMetricDB()
                        landmarkmetricdata.vendorname = "landmark"
                        landmarkmetricdata.resultcount = 0
                        landmarkmetricdata.topresult = 0
                    landmarkmetricdata.resultcount += 1
                    landmarkmetricdata.put()

                #gather data from rediff
                #rediff_data = rediff.getRediffData(inputisbn)
                rediff_data = rediffThread.get_result()
                if(len(rediff_data)>0):
                    rediff_details = DetailDB()
                    rediff_details.vendor_name = rediff_data[0]
                    rediff_details.price = rediff_data[1]
                    rediff_details.buy_now_url = rediff_data[2]   
                    rediff_details.mrp = flipkart_details.mrp
                    rediff_price = (rediff_details.price.split(" ")[1])
                    price_val = int(utilities.cleanInteger(rediff_price))
                    mrp_val = int(rediff_details.mrp.split(" ")[1])
                    rediff_details.discount = str((mrp_val - price_val)*100/mrp_val)+"%"
                    rediff_details.put()
                    newBook.all_vendors.append(rediff_details.key())

                    rediffmetricquery = VendorMetricDB.gql("WHERE vendorname = :1", "rediff")
                    rediffmetricdata = rediffmetricquery.get()
                    if(not rediffmetricdata):
                        rediffmetricdata = VendorMetricDB()
                        rediffmetricdata.vendorname = "rediff"
                        rediffmetricdata.resultcount = 0
                        rediffmetricdata.topresult = 0
                    rediffmetricdata.resultcount += 1
                    rediffmetricdata.put()

                #gather infibeam data
                #infibeam_data = infibeam.getInfibeamData(inputisbn)
                infibeam_data = infibeamThread.get_result()
                if(len(infibeam_data)>0):
                    infibeam_details = DetailDB()
                    infibeam_details.vendor_name = infibeam_data[0]
                    infibeam_details.price = infibeam_data[1]   
                    infibeam_details.mrp = infibeam_data[2]
                    infibeam_details.buy_now_url = infibeam_data[3]
                    infibeam_price = (infibeam_details.price.split(" ")[1])
                    price_val = int(utilities.cleanInteger(infibeam_price))
                    mrp_val = int(infibeam_details.mrp.split(" ")[1])
                    infibeam_details.discount = str((mrp_val - price_val)*100/mrp_val)+"%"
                    infibeam_details.put()
                    newBook.all_vendors.append(infibeam_details.key())

                    infibeammetricquery = VendorMetricDB.gql("WHERE vendorname = :1", "infibeam")
                    infibeammetricdata = infibeammetricquery.get()
                    if(not infibeammetricdata):
                        infibeammetricdata = VendorMetricDB()
                        infibeammetricdata.vendorname = "infibeam"
                        infibeammetricdata.resultcount = 0
                        infibeammetricdata.topresult = 0
                    infibeammetricdata.resultcount += 1
                    infibeammetricdata.put()
                
                #gather indiaplaza data
                #indiaplaza_data = indiaplaza.getIndiaplazaData(inputisbn)
                indiaplaza_data = indiaplazaThread.get_result()
                if(len(indiaplaza_data)>0):
                    indiaplaza_details = DetailDB()
                    indiaplaza_details.vendor_name = indiaplaza_data[0]
                    indiaplaza_details.price = indiaplaza_data[1]
                    indiaplaza_details.mrp = indiaplaza_data[2] 
                    indiaplaza_details.buy_now_url = indiaplaza_data[3]   
                    indiaplaza_price = (indiaplaza_details.price.split(" ")[1])
                    price_val = int(utilities.cleanInteger(indiaplaza_price))
                    mrp_val = int(indiaplaza_details.mrp.split(" ")[1])
                    indiaplaza_details.discount = str((mrp_val - price_val)*100/mrp_val)+"%"
                    indiaplaza_details.put()
                    newBook.all_vendors.append(indiaplaza_details.key())

                    indiaplazametricquery = VendorMetricDB.gql("WHERE vendorname = :1", "indiaplaza")
                    indiaplazametricdata = indiaplazametricquery.get()
                    if(not indiaplazametricdata):
                        indiaplazametricdata = VendorMetricDB()
                        indiaplazametricdata.vendorname = "indiaplaza"
                        indiaplazametricdata.resultcount = 0
                        indiaplazametricdata.topresult = 0
                    indiaplazametricdata.resultcount += 1
                    indiaplazametricdata.put()


                simplybooks_data = simplybooksThread.get_result()
                if(len(simplybooks_data)>0):
                    simplybooks_details = DetailDB()
                    simplybooks_details.vendor_name = simplybooks_data[0]
                    simplybooks_details.price = simplybooks_data[1]
                    simplybooks_details.mrp = simplybooks_data[2]
                    simplybooks_details.buy_now_url = simplybooks_data[3]    
                    simplybooks_price = (simplybooks_details.price.split(" ")[1])
                    price_val = int(utilities.cleanInteger(simplybooks_price))
                    mrp_val = int(simplybooks_details.mrp.split(" ")[1])
                    simplybooks_details.discount = str((mrp_val - price_val)*100/mrp_val)+"%"
                    simplybooks_details.put()
                    newBook.all_vendors.append(simplybooks_details.key())

                    simplybooksmetricquery = VendorMetricDB.gql("WHERE vendorname = :1", "simplybooks")
                    simplybooksmetricdata = simplybooksmetricquery.get()
                    if(not simplybooksmetricdata):
                        simplybooksmetricdata = VendorMetricDB()
                        simplybooksmetricdata.vendorname = "simplybooks"
                        simplybooksmetricdata.resultcount = 0
                        simplybooksmetricdata.topresult = 0
                    simplybooksmetricdata.resultcount += 1
                    simplybooksmetricdata.put()


                bookadda_data = bookaddaThread.get_result()
                if(len(bookadda_data)>0):
                    bookadda_details = DetailDB()
                    bookadda_details.vendor_name = bookadda_data[0]
                    bookadda_details.price = bookadda_data[1]
                    bookadda_details.mrp = bookadda_data[2] 
                    bookadda_details.buy_now_url = bookadda_data[3]   
                    bookadda_price = (bookadda_details.price.split(" ")[1])
                    price_val = int(utilities.cleanInteger(bookadda_price))
                    mrp_val = int(bookadda_details.mrp.split(" ")[1])
                    bookadda_details.discount = str((mrp_val - price_val)*100/mrp_val)+"%"
                    bookadda_details.put()
                    newBook.all_vendors.append(bookadda_details.key())

                    bookaddametricquery = VendorMetricDB.gql("WHERE vendorname = :1", "bookadda")
                    bookaddametricdata = bookaddametricquery.get()
                    if(not bookaddametricdata):
                        bookaddametricdata = VendorMetricDB()
                        bookaddametricdata.vendorname = "bookadda"
                        bookaddametricdata.resultcount = 0
                        bookaddametricdata.topresult = 0
                    bookaddametricdata.resultcount += 1
                    bookaddametricdata.put()
                           
                
                newBook.put()
        
        #by this time, the data should be present in the DB   
        updated_data = None
        if not newBook:
            query1 = IsbnDB.gql("WHERE isbn = :1", inputisbn)
            updated_data = query1.get()
        else:
            updated_data = newBook



        #read from DB & return the result
        self.response.out.write("<html><head></head><body>")
        if(updated_data):
                #sort the results
                all_vendors = []
                for vendor in updated_data.all_vendors:
                    all_vendors.append(db.get(vendor))

                all_vendors_sorted = sort(all_vendors)
                vendormetricquery = VendorMetricDB.gql("WHERE vendorname = :1", all_vendors_sorted[0].vendor_name.replace(' ','').lower())
                vendormetricdata = vendormetricquery.get()
                if(not vendormetricdata):
                    vendormetricdata = VendorMetricDB()
                    vendormetricdata.vendorname = all_vendors_sorted[0].vendor_name.replace(' ','').lower()
                    vendormetricdata.resultcount = 0
                    vendormetricdata.topresult = 0
                vendormetricdata.topresult += 1
                vendormetricdata.put()
                
                #write html to output stream
                html = "<div style='float: left;margin-right:10px;'><img height='100' id='bookThumbnail' src='" + updated_data.thumbnail_url + "'></div>"
                html += "<div style='float: left; word-wrap: break-word; width: 60%;'><div id='bookName' style='color:white;'>"+ updated_data.name + "</div>"
                html += "<div style='color:white' id = 'authorName'>" + updated_data.author +"</div>" 
                html += "</div><div style='clear:both'></div>"

                self.response.out.write(html)
                self.response.out.write("<br><ul id = 'priceGrid' data-count-theme='b' data-role='listview' data-theme='a'>")
                for vendor in all_vendors_sorted:
                    if(vendor):
                        self.response.out.write(getLi(vendor))
                self.response.out.write("</ul>")
        else:
             self.response.out.write("We are sorry, couldn't find any match")
        self.response.out.write("</body></html>")

def getLi(vendor_data):
    html = "<li><a href='"+vendor_data.buy_now_url+ "'>"
    html += "<h3>"+vendor_data.vendor_name+"</h3>"
    html += "<p><span class = 'price'>"+vendor_data.price+"</span>"
    if vendor_data.price != vendor_data.mrp:
        html += " (<span style='text-decoration:line-through'>"+vendor_data.mrp+"</span>)"
    html += "</p>"
    html += "<span style='padding:3px' class='ui-li-count'>"+vendor_data.discount+" off</span>"
    html += "</a></li>"
    
    return html

#custom bubble sort
def sort(all_vendors):
    length = len(all_vendors)-1
    sorted_ = False

    while not sorted_:
        sorted_ = True
        for i in range(0,length):
            if (getPriceNum(all_vendors[i].price) > getPriceNum(all_vendors[i+1].price)):
                sorted_ = False
                temp = all_vendors[i+1]
                all_vendors[i+1] = all_vendors[i]
                all_vendors[i] = temp
    
    return all_vendors


def getPriceNum(price):
    price = price.split(" ")[1]
    return int(price)
        




class RedirectHandler(webapp2.RequestHandler):
    def get(self):
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/tmp/myapp.log',
                    filemode='w')
        logging.warn("redirect url hit")
        #log the metrics
        isbn = str(self.request.get("isbn"))
        vendor = str(self.request.get("vendor"))

        query = IsbnMetricsDB.gql("WHERE isbn = :1",isbn)
        isbnmetricsdata = query.get()
        if(not isbnmetricsdata):
            isbnmetricsdata = IsbnMetricsDB()
            isbnmetricsdata.hits = 0
            isbnmetricsdata.isbn = isbn            
            isbnmetricsdata.redirecttoflipkart = 0
            isbnmetricsdata.redirecttoindiaplaza = 0
            isbnmetricsdata.redirecttoinfibeam = 0
            isbnmetricsdata.redirecttorediff = 0
            isbnmetricsdata.redirecttobookadda = 0
            isbnmetricsdata.redirecttosimplybooks = 0
            isbnmetricsdata.redirecttolandmark = 0

        if vendor=="flipkart":
            isbnmetricsdata.redirecttoflipkart += 1

        elif vendor=="bookadda":
            isbnmetricsdata.redirecttobookadda += 1

        elif vendor=="landmark":
            isbnmetricsdata.redirecttolandmark += 1

        elif vendor=="indiaplaza":
            isbnmetricsdata.redirecttoindiaplaza += 1

        elif vendor=="simplybooks":
            isbnmetricsdata.redirecttosimplybooks += 1

        elif vendor=="infibeam":
            isbnmetricsdata.redirecttoinfibeam += 1

        elif vendor=="rediffbooks":
            isbnmetricsdata.redirecttorediff += 1

        isbnmetricsdata.put()
     
        #get the url to redirect to
        urltoredirect = str(self.request.get("url")).replace('$', "&")
        if urltoredirect:
            self.redirect(urltoredirect)
        
class SearchHandler(webapp2.RequestHandler):
    def get(self):
        logging.warn("search url hit")
        
        query = str(self.request.get("q"))
        results = flipkart_search.getFlipkartSearchData(query)
        if len(results) > 0:
            self.response.out.write("<ul id='searchResultFound' data-theme='a' data-role='listview'>")
            for result in results:
                self.response.out.write("<li data-isbn='"+result[0]+"'>")
                self.response.out.write("<img style='margin-left:-1px;' src=\""+result[3]+"\" />")
                self.response.out.write("<h3 style='margin-left:-15px;' class='bookname'>"+result[1]+"</h3>")
                self.response.out.write("<p style='margin-left:-15px;' class='authorname'>"+result[2]+"</p>")
		
                self.response.out.write("</li>")
            self.response.out.write("</ul>")
        else:
            self.response.out.write("<ul id='searchResultNotFound' data-theme='a' data-role='listview'>")
            self.response.out.write("<li><h3 class='bookname'>"+"No search results"+"</h3></li>")

            self.response.out.write("</ul>")
      
        


    

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/redirect', RedirectHandler),
                               ('/search', SearchHandler)
                              ],
                              debug=True)

if __name__ == '__main__':
    main()
