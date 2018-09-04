$('#mobile-nav').click(function(event) {
  $(this).toggleClass('active');
  $('nav').toggleClass('active');
  event.stopPropagation();
});
$("nav").click(function(e){
  e.stopPropagation();
});
$(document).click(function(){
  $('#mobile-nav').removeClass('active');
  $('nav').removeClass('active');
});
