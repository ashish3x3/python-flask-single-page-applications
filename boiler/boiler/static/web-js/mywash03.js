
  // Handler for .ready() called.
$("#navigation ul li").click(function() {
	$('#navigation li img').remove();
	$(this).append("<img id='onclick' src='/static/web-images/hanger-small.png'>");
	
});


$("#navigation #menu").click(function() {
	$('#navigation ul').toggle();
});


	if (document.documentElement.clientWidth < 768) {

		$("#navigation ul li").click(function() {
				$('#navigation ul').toggle();

		});
	}


$(window).on('scroll',function() {
  var scrolltop = $(this).scrollTop();

  if(scrolltop >= 215) {
    $('#nav-wrapper').addClass("scrolled");
  }
   
  else if(scrolltop <= 210) {
    $('#nav-wrapper').removeClass("scrolled");

  }
});




