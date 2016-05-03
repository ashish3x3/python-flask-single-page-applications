var clothes_count_dry = 0;
var clothes_count_normal = 0;
var net_amount = 0;
var clothes = [];
var clothes_added = 0;
var cancel_order_id;
var order_form_data = {};
var clothes_input = $('form.submitClothes input[type="text"]').each(function() {
    $(this).data('original', '0');
});




var Actors = {

    init: function( config ) {
        this.config = config;
        this.bindEvents();
    },

    bindEvents: function() {
        this.config.addAddressListener.on('click', 'button#address_submit', this.pickup_address );
        this.config.orderScheduleListener.on('submit', 'form#submitorder', this.order_submit );
        this.config.applyCouponListener.on('submit', 'form#applycoupon', this.apply_coupon );

        this.config.reviewTermsListener.click( this.coupon_terms );

        this.config.reviewOrderListener.click(this.review_order);
        this.config.editOrderListener.click(this.edit_order);

        this.config.verifyPhoneListener.on('submit', 'form#verifyphone', this.verify_phone );
        this.config.verifyOtpListener.on('submit', 'form#verifyotp', this.verify_otp );

        this.config.addClothesListener.on('click', 'button#submit', this.submitClothes );
        this.config.addClothesListener.on('click', 'a.cancel', this.cancelClothes );
        this.config.addClothesListener.on('click', 'form.submitClothes button.plus', this.plus_clothes );
        this.config.addClothesListener.on('click', 'form.submitClothes button.minus', this.minus_clothes );


        this.config.RatingsListener.on('mouseover', '#coupon-hero span.stars-click', this.stars );
        this.config.RatingsListener.on('mouseout', '#coupon-hero span.stars-click', this.stars_hover );
        this.config.RatingsListener.on('click', '#coupon-hero span.stars-click', this.stars_click );

        this.config.cancelOrderListener.on('click', 'a#cancel-order', this.cancelOrder );
        this.config.cancelOrderModalListener.on('click', '#modal-cancel', this.cancelModalOrder );

        this.config.helpListener.on('click', 'table#help-table .help_link', this.help );

        this.config.updateOrderStatus.change(this.updateOrderStatus);

        this.config.phoneValidateListener.on("keyup", this.validatePhoneNumber);

    },


    validatePhoneNumber: function(event){
        var val = $(this).val();
        if (val.length > 10) $(this).val(val.substr(0,10));
        if (isNaN(val)) $(this).val(val.match(/\+?[0-9]*/));
    },

    updateOrderStatus: function(event) {
        var order_id = $(this).attr('data-id');
        var status = $(this).val();
        if (!status) return;

        $.ajax({
            url: "/updatestatus/" + order_id + "/" + status,
            type: "post",
            dataType: "json",
            success: function(data){
                if (data.body.status) location.reload();
            },
            error: function(xhr){

            }
        })
    },


    readurl: function(sParam){

        var sPageURL = window.location.search.substring(1);
        var sURLVariables = sPageURL.split('&');
        for (var i = 0; i < sURLVariables.length; i++)
        {
            var sParameterName = sURLVariables[i].split('=');
            if (sParameterName[0] == sParam)
            {
                return sParameterName[1];
            }
        }

    },

    pickup_address: function( e ) {

        e.preventDefault();
        var self = Actors;

        var data = $( "form#submitaddress" ).serializeArray();
        var json = {};

        jQuery.each(data, function() {
            json[this.name] = this.value || '';
        });



        $.ajax({
            type: 'POST',
            url: '/submitaddress',
            data: data,
            dataType: 'json',
            success: function(results) {
                var success = "<div class='success-message-block'><img class='error-img' src='/static/img/tick.png'><span class='success-message'>Address added sucessfully</span></div>"
                $('#addAddress .modal-body').html(success);
                setTimeout(function() {
                    $('#addAddress').modal('hide');
                    location.reload();
                }, 1000);



            }
        });

    },

    order_submit: function( e ) {
        e.preventDefault();
        var submit_button = $("#order_submit").button('loading');
        var coupon_field = $("#coupon").val();
        var data = $( "form#submitorder" ).serializeArray();

        var _pickupSelect = document.getElementById("pickup_time");
        var pickup_time_slot = _pickupSelect.options[_pickupSelect.selectedIndex].text;

        var _scheduleSelect = document.getElementById("schedule_time");
        var schedule_time_slot = _scheduleSelect.options[_scheduleSelect.selectedIndex].text;

        order_form_data['_pickup_time_slot'] = pickup_time_slot;
        order_form_data['_schedule_time_slot'] = schedule_time_slot;
        var _addressId = document.getElementById("address_id");
        var address_select = _addressId.options[_addressId.selectedIndex].index;

        var json = {}, washtypes = [];
        $("#washtype label.active").each(function(index, element){
            washtypes.push($(element).attr("value"));
        });

        $.each(data, function(index, value) {
            json[this.name] = this.value || '';
        });

        //console.log(json);
        //alert(json);

        data.push({
            name: "washtypes",
            value: washtypes
        })
        data.push({
            name: "schedule_time",
            value: $("#schedule_time").val()
        })

        $.each(data, function(index, value) {
            json[this.name] = this.value || '';
        });

        console.log(data)

        $.ajax({
            type: 'POST',
            url: '/submitorder',
            data: data,
            dataType: 'json',

            success: function(results) {

                if(results.body.status == true){
                    order_data = results.body.order_form_data;
                    
                    $.each(order_data, function(index,val){
                        order_form_data[index] = val;
                    })
                    
                    $("#orderSchedule").css("visibility","hide");
                    $("#orderSchedule").hide('slow');
                    $("#applyCoupon").show('slow');

                    $("#review_form_pick_up").empty();
                    $("#review_form_pick_up").append("<h4>Pick up</h4>");
                    $("#review_form_pick_up").append("<p>"+order_form_data['pickup_date']+"</p>");
                    $("#review_form_pick_up").append("<p>"+order_form_data['_pickup_time_slot']+"</p>");

                    $("#review_form_delivery_details").empty();
                    $("#review_form_delivery_details").append("<h4>Delivery</h4>");
                    $("#review_form_delivery_details").append("<p>"+order_form_data['schedule_date']+"</p>")
                    $("#review_form_delivery_details").append("<p>"+order_form_data['_schedule_time_slot']+"</p>");
                    $("#review_form_address_details").empty();
                    $("#review_form_address_details").append("<h4>Pickup/Delivery Address</h4>");
                    $("#review_form_address_details").append("<p>"+address_list[address_select]['apartment_number']+", "+address_list[address_select]['address_1']+"</p>");
                    $("#review_form_address_details").append("<p>"+address_list[address_select]['locality']['map_string']+"</p></br>");
                    
                    $("#review_form_address_details").append("<p>"+order_form_data['washtypes'].toUpperCase().bold()+"</p>");
                    $("#review_form_address_details").append("<p>"+order_form_data['service'].toUpperCase().bold()+"</p>");
                    
                    submit_button.button('reset');
                }else{

                    Toast.show({
                          message  :results.body.message,
                          duration    : Toast.DURATION_LONG,
                         // background:'#428bca',
                        }); 
                    submit_button.button('reset');
                    $( "form#submitorder span.loader_circle" ).hide();
                    $("#coupon").val("");

                }

            },
            error: function(){
                console.log('Something went wrong');
                submit_button.button('reset');
                $( "form#submitorder span.loader_circle" ).hide();

            }
        });
    },

    review_order: function( e ) {
        var submit_button = $("#accept_terms").button('loading');
        var coupon_field = $("#coupon").val();
        var data = $( "form#verifycoupon" ).serializeArray();

        $.each( order_form_data, function(index,val){
            data.push({
                name: index,
                value: val
            });
        });

        order_form_data = {};
        $.ajax({
            type: 'POST',
            url: '/completeorder',
            data: data,
            dataType: 'json',
            success: function(results) {

                if(results.body.status == true){
                    var order_id = results.body.order.id;
                    if(clothes_added == 1){
                        self.postOrderItems(order_id);
                    }

                    // initializes and invokes show immediately
                    setTimeout(function() {
                        location.href="/getorder/" + order_id;
                    }, 1000);                      
                }else{
                    Toast.show({
                          message  :results.body.message,
                          duration    : Toast.DURATION_LONG,
                         // background:'#428bca',
                        }); 
                    $("#coupon-conditions").modal('hide');
                    submit_button.button('reset');
                    $( "form#verifycoupon span.loader_circle" ).hide();
                    $("#coupon").val("");

                }
            },
            error: function(){
                console.log('Something went wrong');
                submit_button.button('reset');
                $( "form#verifycoupon span.loader_circle" ).hide();

            }
        });
    },
    edit_order: function(e) {
        $("#applyCoupon").hide('slow');
        $("#orderSchedule").show('slow');
    },

    coupon_terms: function( e ) {
        e.preventDefault();
        var submit_button = $("#validate_coupon").button('loading');
        var coupon_field = $("#coupon").val();
        var data = $( "form#verifycoupon" ).serializeArray();

        
        var json = {}, washtypes = [];
        $("#washtype label.active").each(function(index, element){
            washtypes.push($(element).attr("value"));
        });

        $.each(data, function(index, value) {
            json[this.name] = this.value || '';
        });

        //console.log(json);
        //alert(json);

        data.push(
            {order_value: net_amount}
        );
        data.push({
            name: "washtypes",
            value: washtypes
        });
        $.each( order_form_data, function(index,val){
            data.push({
                name: index,
                value: val
            });
        });
        if (coupon_field){
            $.ajax({
                type: 'POST',
                url: '/couponverify',
                data: data,
                dataType: 'json',

                success: function(results) {

                    if(results.body.status == true){
                        $("#terms_list").html('');
                        $.each(results.body.terms, function(i, field){
                            $("#terms_list").append("<li><p>"+field+"</p></li>")
                        });
                        
                        $("#coupon-conditions").modal({
                            backdrop: 'static',
                            keyboard: false,
                            show: true
                        });
                        submit_button.button('reset')
                    }else{

                        Toast.show({
                              message  :results.body.message,
                              duration    : Toast.DURATION_LONG,
                             // background:'#428bca',
                            }); 
                        submit_button.button('reset');
                        $( "form#verifycoupon span.loader_circle" ).hide();
                        $("#coupon").val("");

                    }

                },
                error: function(){
                    console.log('Something went wrong');
                    submit_button.button('reset');
                    $( "form#verifycoupon span.loader_circle" ).hide();

                }
            });
        }else{
            submit_button = $("#validate_coupon").button('loading');
            //alert("completing order");
            $.ajax({
            type: 'POST',
            url: '/completeorder',
            data: data,
            dataType: 'json',

            success: function(results) {

                if(results.body.status == true){
                    var order_id = results.body.order.id;
                    if(clothes_added == 1){
                        self.postOrderItems(order_id);
                    }

                    // initializes and invokes show immediately
                    setTimeout(function() {
                        location.href="/getorder/" + order_id;
                    }, 1000);                      
                }else{

                    Toast.show({
                          message  :results.body.message,
                          duration    : Toast.DURATION_LONG,
                         // background:'#428bca',
                        }); 
                    submit_button.button('reset');
                    $( "form#verifycoupon span.loader_circle" ).hide();
                    $("#coupon").val("");

                }

            },
            error: function(xhr, status, error){
                 Toast.show({
                          message  :error,
                          duration    : Toast.DURATION_LONG,
                         // background:'#428bca',
                        }); 
                console.log('Something went wrong');
                submit_button.button('reset');
                $( "form#verifycoupon span.loader_circle" ).hide();

            }
        });
        }
    },

    verify_phone: function( e ) {
        e.preventDefault();
        var submit_button = $("#send_otp").button('loading');
        var data= $( "form#verifyphone" ).serializeArray();

        //console.log(data);
        var json = {};

        $.each(data, function(index, value) {
            json[this.name] = this.value || '';
        });

        $.ajax({
            type: 'POST',
            url: '/validate_phone_otp',
            data: data,
            dataType: 'json',

            success: function(results) {

                if(results.body.status == true){
                    // initializes and invokes show immediately
                    location.reload();
                }else{

                    Toast.show({
                          message  :results.body.message,
                          duration    : Toast.DURATION_LONG,
                         // background:'#428bca',
                        }); 
                    submit_button.button('reset');
                    $( "form#verifyphone span.loader_circle" ).hide();
                    $("#phone").val("");

                }

            },
            error: function(){
                console.log('Something went wrong');
                submit_button.button('reset');
                $( "form#verifyphone span.loader_circle" ).hide();

            }
        });
    },
    verify_otp: function( e ) {
        e.preventDefault();
        var submit_button = $("#verify_otp").button('loading');
        var data= $( "form#verifyotp" ).serializeArray();
        //console.log(data);
        var json = {};

        $.each(data, function(index, value) {
            json[this.name] = this.value || '';
        });

        $.ajax({
            type: 'POST',
            url: '/validate_phone_otp',
            data: data,
            dataType: 'json',

            success: function(results) {

                if(results.body.status == true){
                    setTimeout(function() {
                        location.href="/order_schedule";
                    }, 1000);
                }else{

                    Toast.show({
                          message  :results.body.message,
                          duration    : Toast.DURATION_LONG,
                         // background:'#428bca',
                        }); 
                    submit_button.button('reset');
                    $( "form#verifyotp span.loader_circle" ).hide();
                    $("#otp").val("");

                }

            },
            error: function(){
                console.log('Something went wrong');
                submit_button.button('reset');
                $( "form#verifyotp span.loader_circle" ).hide();
            }
        });
    },

    postOrderItems: function(order_id) {
        var self = Actors;
        $.ajax({
            type: 'GET',
            url: '/additems?order_id=' + order_id + '&data=' +clothes,
            dataType: 'json',

            success: function(results) {

            }
        });
    },


    stars: function(e) {
        e.preventDefault();

        var self = Actors;
        $(this).prevAll('span').addClass( "star-hover" );

    },

    stars_hover: function(e) {
        e.preventDefault();

        var self = Actors;
        $(this).prevAll().removeClass( "star-hover" );

    },


    stars_click: function(e) {
        e.preventDefault();
        var self = Actors;

        var order_id = self.readurl('order_id');
        $(this).addClass( "star-clicked" );
        $(this).siblings().removeClass("stars-click");

        $(this).removeClass("stars-click");

        $(this).prevAll('span').addClass( "star-clicked" );
        $(this).prevAll('h2').append("<div><h3> Brilliant </h3></div>" );
        var abc = $(this).prevAll('h2').text('Thanks for rating us').fadeIn( "slow" );

        var stars = $(this).data( 'star' );
        $.ajax({
            type: 'GET',
            url: '/addrating?order_id=' + order_id + '&rating=' +stars,
            dataType: 'json',
            success: function(results) {

            }
        });



        if(stars == 3){
            $('.emotion').html("<span class='icon-smiley-1'></span> <h3>Brilliant!, that should keep us going! </h3>" );

        }else if(stars == 2){
            $('.emotion').html("<span class='icon-smiley-3'></span> <h3>Thanks, we shall work towards serving you better</h3>" );
        }else{
            $('.emotion').html("<span class='icon-smiley-2'></span> <h3>Sorry, we should have served you better. We will work on it</h3>" );
        }




    },


    help: function(e) {
        e.preventDefault();

        var self = Actors;

        $('#help .help_content').removeClass( "active" );
        $(this).next().addClass( "active" );

    },


    apply_coupon: function( e ) {
        e.preventDefault();


        var self = Actors;

        var data = $( "form#applycoupon" ).serializeArray();

        $.ajax({
            type: 'get',
            url: '/applycoupon',
            data: data,
            dataType: 'json',

            success: function(results) {
                if(results.body.status == true)
                {

                    var success = "<label class='control-label' for='coupon code'></label><a id='addclothes'><img class='error-img' src='/static/img/tick.png'>Coupon applied successfully</a>"
                    $( "form#applycoupon #success-failure-msg" ).html(success);
                    location.reload();
                }
                else{
                    var error_message = results.body.message;
                    var success = "<label class='control-label' for='coupon code'></label><a id='addclothes'><img class='error-img' src='/static/img/x.png'>" + error_message + "</a>"
                    $( "form#applycoupon #success-failure-msg" ).html(success);
                }
            },


            error: function(){

                console.log('Something went wrong');

            }
        });
    },



    submitClothes: function( e ) {
        e.preventDefault();
        var self = Actors;

        clothes_added = 1;

        data1 = $("form#wash" ).find('input.changed').serializeArray();
        data2 = $("form#drywash" ).find('input.changed').serializeArray();


        $.each(data1, function(i, data1)  {
            data1.type = "0";
        });

        $.each(data2, function(i, data2)  {
            data2.type = "1";
        });


        clothes =  $.merge( data1, data2);
        clothes = JSON.stringify(clothes);


        $('#addClothes').modal('hide');

    },



    cancelClothes: function( e ) {
        e.preventDefault();
        var self = Actors;
        $('#addClothes').modal('hide');
    },



    cancelOrder: function( e ) {
        e.preventDefault();
        var self = Actors;

        cancel_order_id = $(this).data( 'id' );

        $('#editOrderCancel').modal('show');
    },





    cancelModalOrder: function( e ) {
        e.preventDefault();
        var self = Actors;
        var cancel_button = $(this).button('loading');
        $.ajax({
            type: 'GET',
            url: '/cancelorder?order_id=' + cancel_order_id,
            dataType: 'json',
            success: function(results) {
                if(results.body.status == true){
                    // initializes and invokes show immediately
                    setTimeout(function() {
                        location.href="/order_schedule";
                    }, 1000);

                }
            },
            error: function(){

                console.log('Something went wrong');
                cancel_button.button('reset');

            }


        });


    },



    plus_clothes: function( e ) {
        e.preventDefault();


        var self = Actors;

        var cart_value = $(this).prev().val();
        var cart_value_filtered = + cart_value.replace(/,/g, '');

        var new_cart_value = parseInt(cart_value_filtered) + 1;
        var update_value = $(this).prev("input").attr({ value: new_cart_value, class:"changed" });

        var washtype = $(this).data( 'type' );
        var current_product_value = $(this).data( 'price' );

        if(washtype == 0){

            clothes_count_dry = clothes_count_dry + 1;
            $("div#addClothes .drywash").text(clothes_count_dry);

            net_amount = net_amount + current_product_value;
            $("div#addClothes .value").text(net_amount);
            $("div#addClothes .minorder").text('Your order value');

        }else{

            clothes_count_normal = clothes_count_normal + 1;
            $("div#addClothes .normalwash").text(clothes_count_normal);

            net_amount = net_amount + current_product_value;
            $("div#addClothes .value").text(net_amount);
            $("div#addClothes .minorder").text('Your order value');

        }



    },



    minus_clothes: function( e ) {
        e.preventDefault();


        var self = Actors;
        var cart_value = $(this).next().val();
        var washtype = $(this).data( 'type' );
        var current_product_value = $(this).data( 'price' );


        var cart_value_filtered = + cart_value.replace(/,/g, '');

        if(cart_value_filtered != 0){

            var new_cart_value = parseInt(cart_value_filtered) - 1;
            var update_value = $(this).next("input").attr('value', new_cart_value);

            if(washtype == 0){

                clothes_count_dry = clothes_count_dry - 1;
                $("div#addClothes .drywash").text(clothes_count_dry);

                net_amount = net_amount - current_product_value;
                $("div#addClothes .value").text(net_amount);
                $("div#addClothes .minorder").text('Your order value');

            }else if(washtype == 1){

                clothes_count_normal = clothes_count_normal - 1;
                $("div#addClothes .normalwash").text(clothes_count_normal);

                net_amount = net_amount - current_product_value;
                $("div#addClothes .value").text(net_amount);
                $("div#addClothes .minorder").text('Your order value');

            }




        }else{}

    },


};

Actors.init({

    addAddressListener: $('div#addAddress'),
    orderScheduleListener: $('div#orderSchedule'),
    applyCouponListener: $('div#applyCoupon'),
    addClothesListener: $('div#addClothes'),

    reviewTermsListener: $('#validate_coupon'),
    editOrderListener: $('#edit_order'),
    verifyPhoneListener: $('div#verifyPhone' ),
    verifyOtpListener: $('div#verifyOtp' ),

    reviewOrderListener: $('#accept_terms'),


    cancelOrderModalListener: $('div#editOrderCancel'),
    cancelOrderListener: $('div#order_status_info'),

    phoneValidateListener: $("#phone"),

    RatingsListener: $('div#ratings'),
    helpListener: $('div#help'),

    updateOrderStatus: $("#update-order-status"),

});


