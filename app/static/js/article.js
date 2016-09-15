$(function(){
  // document.getElementById("like-button").addEventListener("click", function(e) {
  $(".like-button").on("click", function(e)    {
    e.preventDefault();
    var article = $(this).val();
    var data = {"article": article};
    console.log(data);
    if(data){
      $.ajax({
        type: 'POST',
        contentType: 'application/json',
        url: '/article_liked',
        dataType : 'json',
        data : JSON.stringify(data),
        success: function (response) {
          success("Article was successfully liked.");
        }


      }).fail(function(response, exception){
        console.log("Action failed");

        if (response.status == 0) {
          failure("Not connecting, verify your network");
        } else if (response.status == 404) {
          failure("Requesting page not found [404]");
        } else if (response.status == 500) {
          failure("Internal Error [500]");
        } else if (exception === 'parsererror') {
          failure("Requested JSON parser failed");
        } else if (exception === 'timeout') {
          failure("Time Out Error");
        } else if (exception === 'abort') {
          failure("AJAX request aborted");
        } else {
          failure("Uncaught Error");
        }

      });
    }
    else {
      failure("No input data found in the post request.");
    }

    function success(msg){
        // $('#recordStatus').html("<div style='color:green'>"+msg+"</div>");
            window.setTimeout(function(){location.reload()}, 10);
      }
      
    function failure(msg){
      // $('#recordStatus').html("<div style='color:red'>"+msg+"</div>");            
        window.setTimeout(function(){location.reload()}, 10);
    }
  });

  // Unlike button

  // document.getElementById("unlike-button").addEventListener("click", function(e) {
  $(".unlike-button").on("click", function(e)    {
    e.preventDefault();
    var article = $(this).val();
    var data = {"article": article};
    console.log(data);
    if(data){
      $.ajax({
        type: 'POST',
        contentType: 'application/json',
        url: '/article_unliked',
        dataType : 'json',
        data : JSON.stringify(data),
        success: function (response) {
          success("Article was successfully unliked.");
        }

      }).fail(function(response, exception){
        console.log("Action failed");

        if (response.status == 0) {
          failure("Not connecting, verify your network");
        } else if (response.status == 404) {
          failure("Requesting page not found [404]");
        } else if (response.status == 500) {
          failure("Internal Error [500]");
        } else if (exception === 'parsererror') {
          failure("Requested JSON parser failed");
        } else if (exception === 'timeout') {
          failure("Time Out Error");
        } else if (exception === 'abort') {
          failure("AJAX request aborted");
        } else {
          failure("Uncaught Error");
        }

      });
    }
    else {
      failure("No input data found in the post request.");
    }

    function success(msg){
        // $('#recordStatus').html("<div style='color:green'>"+msg+"</div>");
            window.setTimeout(function(){location.reload()});
      }
      
    function failure(msg){
      // $('#recordStatus').html("<div style='color:red'>"+msg+"</div>");            
        window.setTimeout(function(){location.reload()});
    }
  });

});