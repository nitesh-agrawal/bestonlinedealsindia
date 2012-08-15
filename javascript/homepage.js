	$(function(){
		
	  var inAjaxCall = false;
	  var blockUI = function()
				  {
					  inAjaxCall = true;
				  }
	  var unblockUI = function()
				  {
					  inAjaxCall = false;
				  }
	  var isUIBlocked = function()
				  {
					  return inAjaxCall == true;
				  }
	  var showMessage = function (stringToShow)
				  {
					  hideMessage();
					  $('body').append('<div id = "progress">'+ stringToShow + '</div>');
				  }
  	  var hideMessage = function ()
				  {
					  $('#progress').remove();
				  }
/*	  var messageTimer = $.timer(function() {
					hideMessage();
					messageTimer.stop();  
	  });
	  var showMessageWithAutoTimer = function (stringToShow, timerval)
				  {
		  			  hideMessage();
					  $('body').append('<div id = "progress">'+ stringToShow + '</div>');
  					  messageTimer.set({ time : timerval, autostart : true });
				  }*/

	  var toastDrawn = false;
	  var toastTimer = $.timer(function() {
		  var toastAlert = document.getElementById("toast");
		  if (toastAlert)
			  toastAlert.style.opacity = 0;
 		  $('#toast').remove();
	  	  toastDrawn = false;
		  toastTimer.stop();  
	  });
	  
	  var drawToast = function (message)
		  {
			  return drawToast (message, 3000);
		  }
		  
	  var drawToast = function (message, timerval){
		  if (toastDrawn)
		  	return;

		  toastDrawn = true;
		  var toastAlert = document.getElementById("toast");
		  if (toastAlert == null){
			  var toastHTML = '<div id="toast">' + message + '</div>';
			  $('body').append(toastHTML);
		  }
		  else{
			  toastAlert.style.opacity = .9;
		  }
		  //toastTimer.set({ time : timerval, autostart : true });
		  toastTimer.once(timerval);
	  }
	  
	  var timer = $.timer(function() {
			unblockUI();
			hideMessage();
			timer.stop();
            drawToast("Timeout :-(. Please try again", 3000);
       });
	  $('input#invokeBarcodeScanner').click(function(){
		  if (isUIBlocked())
		  {				
			drawToast("Waiting for Server....Please Wait", 3000);
		  	return;
		  }
		  drawToast("Launching Barcode Scanner", 2000);
		  window.plugins.barcodeScanner.scan( 
			  function(result) {
							 /* alert("We got a barcode\n" +
								  "Result: " + result.text + "\n" +
								  "Format: " + result.format + "\n" +
								  "Cancelled: " + result.cancelled);*/
							 if (!result.cancelled)
							 {
							  	$('input#inputISBN').val(result.text);
							 	$('input#getBestDeals').click();
							 }
							 else
							 {
								 drawToast("Barcode Scanning Cancelled o_0 !! Scan beats Type", 3000);
							 }

			  }, function(error) {
							  drawToast("Scanning failed: " + error, 3000);
			  }
		  );	
	  });

	  $('input#getBestDeals').click(function(){
		  if (isUIBlocked())
		  {
				drawToast("Waiting for Server....Please Wait", 3000);
		  		return;
		  }
				
		  var inputISBN = $('input#inputISBN').val();
		  var validInput = false;
		  inputISBN = inputISBN.trim();
		  if (inputISBN.length && (inputISBN.length == 10 || inputISBN.length == 13))
		  {
			  if (is_int(inputISBN))
			  {
				 if (inputISBN.length == 10)
				 {
     				 if (is_ISBN_valid(inputISBN))
					 {
		  			 	inputISBN = ISBN10to13(inputISBN);
					 }
					 else
					 {
						 inputISBN = '978' + inputISBN;
					 }
				 }

				 if (is_ISBN_valid(inputISBN))
				  {		
		  			showMessage("Loading...");
					blockUI();
					timer.set({ time : 60000, autostart : true });
					var serverURL = 'http://bestonlinedealsindia.appspot.com?isbn=' + inputISBN;

					$('#contentDivResultsPage').ajaxError(function(event, request, settings){
						unblockUI();
						hideMessage();
						timer.stop();
						drawToast("Unable to fetch the best prices. Please check your Internet Connection", 3000);
					});

					$('#contentDivResultsPage').load( serverURL,
									function() {
									  window.location = $('a#bestDeals').attr('href');
					  				  unblockUI();
									  hideMessage();
									  timer.stop();
									  AddEntryToLocalStorage(inputISBN);
								  });
	  
					return;
				  }
			  }
		  }
		  drawToast(':-# My creators will bash me if I send them an Invalid ISBN', 3000);
	  });
	  
	  $('input#inputISBN').keyup(function(event){
			if(event.keyCode == 13)
			{
				 $('input#getBestDeals').click();
			}
	  });

	  var AdjustStorageIfAlreadyPresent = function(inputISBN)
				  {
   					    var maxItemsHistory = 10;
		  				var items = $.jStorage.index();
						var itemFound = false;
						var j = maxItemsHistory - 1;
						for (; j >= maxItemsHistory - items.length; --j)
						{
							var curItem = $.jStorage.get("bookInHistory" + j);
							if (curItem.isbn == inputISBN) // already present in the storage
							{
								$.jStorage.deleteKey("bookInHistory" + j);
								itemFound = true;
								continue;
							}
							if (itemFound)
							{
								$.jStorage.set("bookInHistory" + (j + 1), curItem);
								$.jStorage.deleteKey("bookInHistory" + j);
							}
						}
				  }
	  var AddEntryToLocalStorage = function(inputISBN)
				  {
					  var bookName = $('#bookName').html();
					  var thumbNail = $('#bookThumbnail').attr('src');
					  var authorName = $('#authorName').html();
					  var bestPrice = $('#priceGrid .price:first').html();

					  if(!bookName || !thumbNail || !authorName ||!bestPrice)
					  	return;
					  
 					    var maxItemsHistory = 10;
					    AdjustStorageIfAlreadyPresent(inputISBN);
		  				var items = $.jStorage.index();
						var key = "bookInHistory"+ (maxItemsHistory - 1 - items.length);
						if (items.length == maxItemsHistory) // List MAX size achieved
						{
							key = "bookInHistory0";
							for (var j = maxItemsHistory - 2; j >=0; --j)
							{
								var itemtoShift = $.jStorage.get("bookInHistory" + j); 
								$.jStorage.set("bookInHistory" + (j + 1), itemtoShift);
							}
						}
						var ItemToPut = {isbn: inputISBN, bookname: bookName, thumbnail: thumbNail, authorname: authorName, bestprice: bestPrice};
						$.jStorage.set(key, ItemToPut);
				  }
	  var is_int = function(value)
				  {
					for (i = 0 ; i < value.length ; i++)
					{
						if ((value.charAt(i) < '0') || (value.charAt(i) > '9')) 
							return false;
					}
					return true;  
				  }
	  var calculateISBN13CheckDigit = function(value)
				  { 
				      // generate checkDigit using the 1st 12 digits
					  var i, digit = 0, checkSum = 0;
					  for (i = 0; i < 12; i++) {
			               digit = value[i] - '0';
 				           if (i % 2 == 1) {
                			    digit *= 3;
			               }
						checkSum += digit;
					  }
					  return (10 - checkSum % 10)%10;
				  }
  	  var is_ISBN_valid = function(value)
				  {
					  if (value.length == 10)
					  {
					      var i, a = 0, b = 0;
    						for (i = 0; i < 10; i++) {
						        a += (value[i] - '0');// converting from ASCII to 0..9
      							b += a;
						    }
						  return (b % 11) == 0;
					  }
					  else if (value.length == 13)
					  {
						  var checkDigit = calculateISBN13CheckDigit(value);
						  return checkDigit == (value[12] - '0');
					  }
					  else 
					  	return false;
				  }

	  String.prototype.replaceAt=function(index, char) {
		  if (index < 0 || index >= this.length)
		  	return this;
	      return this.substr(0, index) + char + this.substr(index+1, this.length-index-1);
	   }
	   
      String.prototype.trim=function(){return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');};

	  var ISBN10to13 = function(value)
				  {
					  value = '978' + value;
					  var checkDigit = calculateISBN13CheckDigit(value);
					  value = value.replaceAt(12, checkDigit);
					  return value;
				  }
	});