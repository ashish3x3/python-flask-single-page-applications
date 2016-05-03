var active_timeslots = [];
var pickup_disabled_dates = [];
var delivery_disabled_dates = [];
var blocked_timeslots;

var all_timeslots = null;


var washtype_selected_arr = ['laundry'];


var enErrorDialogs = {
    requiredFields : '*',
};

$.validate({
    language : enErrorDialogs
});

$('.validate-phone').keypress(function(event) {
    var val = $(this).val();
    if (val.length > 10) $(this).val(val.substr(0,10));
    if (isNaN(val)) $(this).val(val.match(/\+?[0-9]*/));
});

$('#submitEditAddress_1').hide();
    $('#tag_1').click(function(event) {
        $('#submitEditAddress_1').toggle();
});




function setPickupDatepicker(){
    $('#pickup_date').pickadate({
        // An integer (positive/negative) sets it relative to today.
        min: true,
        // `true` sets it to today. `false` removes any limits.
        max: 30,
        format: ' dd mmm, yyyy  (dddd)',
        formatSubmit: 'yyyy/mm/dd',
        onStart: function ()
        {
            var date = new Date();
            this.set('select', [date.getFullYear(), date.getMonth(), date.getDate()]);
        },
        disable: [[2015,5,12],]
    });
    var from_$input = $('#pickup_date').pickadate();
    return from_$input.pickadate('picker');

}

function setDeliveryDatepicker(){
    $('#schedule_date').pickadate({
        // An integer (positive/negative) sets it relative to today.
        min: +3,
        // `true` sets it to today. `false` removes any limits.
        max: 30,
        format: ' dd mmm, yyyy  (dddd)',
        formatSubmit: 'yyyy/mm/dd',
        onStart: function ()
        {
            var date = new Date();
            date.setDate(date.getDate() + 3);
            this.set('select', [date.getFullYear(), date.getMonth(), date.getDate()]);
        },
    });

    var to_$input = $('#schedule_date').pickadate();
    return to_$input.pickadate('picker');
}

var from_picker = setPickupDatepicker();
var to_picker = setDeliveryDatepicker();

// to_picker.set('disable',[new Date(2015,6,1)]);

// Handler for .ready() called.
$(".menu-toggle").click(function() {
    $(".wrapper").toggleClass("active");
});



$(".toggle-btns a").click(function() {
    $(".toggle-btns a").removeClass("active");
    $(this).addClass("active");

});



$('tr.item-drywash:gt(4)').hide().last().after(
    $('<a />').attr({
        href:"#",
        class:"showmore"
    }).text('Show more').click(function(){
        var a = this;
        $('tr.item-drywash:not(:visible):lt(4)').fadeIn(function(){
            if ($('tr.item-drywash:not(:visible)').length == 0) $(a).remove();
        }); return false;
    })
);


$('tr.item-washing:gt(4)').hide().last().after(
    $('<a />').attr({
        href:"#",
        class:"showmore"
    }).text('Show more').click(function(){
        var a = this;
        $('tr.item-washing:not(:visible):lt(4)').fadeIn(function(){
            if ($('tr.item-washing:not(:visible)').length == 0) $(a).remove();
        }); return false;
    })
);


$('#dry_schedule_date').css( "display", "none" );

function getScheduleTimeDelta(selected_wash_types){
    var default_delta;
    var raw_active_elements = $("#washtype label.active");
    if (washtype_selected_arr.length) {
        default_delta = washtype_selected_arr.indexOf("dryclean") != -1 ? 5 : 3;
    }else{
        default_delta = -1;
    }

    if (default_delta > -1) {
        var pickup_date = moment(from_picker.get('select', 'yyyy/mm/dd'));
        if (['2015-09-24', '2015-09-25','2015-09-26', '2015-09-27', '2015-09-28'].indexOf(pickup_date.format('YYYY-MM-DD')) != -1)
            default_delta += 1;
    };
    return default_delta;
}

function setTurnAroundTime(){
    $("#schedule_time").attr('disabled', false);
    var delivery_date = moment($("#schedule_date").val());
    var pickup_date = moment(from_picker.get('select', 'yyyy/mm/dd'));
    var slots;

    var default_delta = getScheduleTimeDelta();
    var delta = moment(delivery_date - pickup_date).date() - 1;
    var pickup_time_index = '0';

    if (delta == default_delta) {
        pickup_time_index = $('#pickup_time').val();
    }
    if (delivery_date.format("YYYY-MM-DD") in all_timeslots.timeslots_delivery) {
        $.each(all_timeslots.timeslots_delivery[delivery_date.format("YYYY-MM-DD")], function(index, value){
            if (index == 'date' & value.date == delivery_date.format('YYYY-MM-DD')) {
                slots = value.slots_available
                return false;
            } else {
                slots = all_timeslots.data;
            }
        });
        slots = all_timeslots.timeslots_delivery[delivery_date.format("YYYY-MM-DD")]['slots_available']
    } else {
        slots= all_timeslots.data;
    }

    $("#schedule_time").html('');

    if (selectedServiceType == "express") {
        delivery_date = moment($("#schedule_date").val());
        pickup_time_index = parseInt($('#pickup_time').val());
        $.each(slots, function(key, value) {
            if (value != undefined || value != null){
                var new_delivery_time = pickup_time_index;
                if (new_delivery_time == 0) new_delivery_time = 7;
                if (key >= new_delivery_time){
                    $("#schedule_time").append($("<option/>", {
                        value: key,
                        text: value
                    }));
                }
            }
        });

        if(($("#pickup_time option").length == 1 && $("#pickup_time option:selected").val() == '0') || ('0' in slots)){
            $("#schedule_time").html('<option>Pick next date</option>');
            $("#schedule_time").attr('disabled', 'disabled');
        }

        var new_delivery_date = moment(pickup_date.toDate());
        new_delivery_date.add(1, 'days')
        to_picker.set('min', new_delivery_date.toDate());
        to_picker.set('max', new_delivery_date.toDate());
        to_picker.set('select', new_delivery_date.toDate());
        if(delivery_date.format("YYYY-MM-DD") == '2015-10-02'){
            console.log('---------');
            $("#schedule_time").html('');
            $("#schedule_time").html('<option>Pick next date</option>');
            $("#schedule_time").attr('disabled', 'disabled');   
        }
        return ;
    };

    $.each(slots, function(key, value) {
        if (value != undefined || value != null){
            if (key >= pickup_time_index) {
                $("#schedule_time").append($("<option/>", {
                    value: key,
                    text: value
                }));
            }
        }
    });


    if(($("#pickup_time option").length == 1 && $("#pickup_time option:selected").val() == '0') || ('0' in slots)){
        $("#schedule_time").html('<option>Pick next date</option>');
        $("#schedule_time").attr('disabled', 'disabled');
    }

    if(delivery_date.format("YYYY-MM-DD") == '2015-10-02'){
        $("#schedule_time").html('');
        $("#schedule_time").html('<option>Pick next date</option>');
        $("#schedule_time").attr('disabled', 'disabled');   
    }
    
}

function deliveryDateChange(){
    var delivery_date = moment($("#schedule_date").val());
    var pickup_date = moment(from_picker.get('select', 'yyyy/mm/dd'));
    var slots;

    var default_delta = getScheduleTimeDelta();
    var delta = moment(delivery_date - pickup_date).date() - 1;
    var pickup_time_index = '0';
    
    if (delivery_date.format("YYYY-MM-DD") in all_timeslots.timeslots_delivery) {
        slots = all_timeslots.timeslots_delivery[delivery_date.format("YYYY-MM-DD")]['slots_available']
    } else {
        slots= all_timeslots.data;
    }

    var pickup_time_index = parseInt($('#pickup_time').val());
    if (delta == default_delta) {
        $('#pickup_time').change();
    }else{
        if (selectedServiceType == 'regular') {
            $("#schedule_time").html('');
            $.each(slots, function(key, value) {
                if (value != undefined || value != null){
                    if (pickup_time_index) {
                        $("#schedule_time").append($("<option/>", {
                            value: key,
                            text: value
                        }));
                    } else {
                        $("#schedule_time").append("<option>Pick next date</option>");
                    }
                } 
                
            });
        }
    }
}

function washtypeLabelChange(event){
    if ($(this).hasClass("active")) {
        if($("#washtype label.active").length == 1) return false;
    };
    var raw_active_elements = $("#washtype label.active");
    final_arr = new Array();
    if (!$(this).hasClass("active")){
        raw_active_elements.push(this);
        raw_active_elements.each(function(index, value){
            final_arr.push($(value));
        })
    }else{
        self = this;
        raw_active_elements.each(function(index, value){
            if (value != self)
                final_arr.push($(value));
        })
    }
    washtype_selected_arr = [];
    $.each(final_arr, function(index, element){
        washtype_selected_arr.push($(element).attr('value'));
    })

    if(selectedServiceType == "express"){
        var pickup_time = $("#pickup_time").val() - 1;
        return;
    }

    var schedule_delta = getScheduleTimeDelta(final_arr);
    var selected_date = moment(from_picker.get('select', 'yyyy/mm/dd'));
    if (schedule_delta != -1)
        var moment_date = selected_date.add(schedule_delta, 'days');
    to_picker.set('min', moment_date.toDate());
    to_picker.set('select', moment_date.toDate());
}


function pickupDateChange() {
    var slots;
    var date = from_picker.get('select', 'yyyy-mm-dd');

    if (date == all_timeslots.date_today) {
        slots = all_timeslots.filtered_slots;
    } else {
        if (date in all_timeslots.timeslots_pickup) {
            slots = all_timeslots.timeslots_pickup[date]['slots_available'];
        } else {
            slots = all_timeslots.data;
        }
    }

    $("#pickup_time").html('');
    $.each(slots, function(key, value) {
        if (value != undefined || value != null){
            $("#pickup_time").append($("<option/>", {
                value: key,
                text: value
            }));
            
            if (key == '0') {
                $("#pickup_time").prop('disabled', 'disabled');
            }
            else {
                $("#pickup_time").prop('disabled', false);
            }
        }
    });

    if(selectedServiceType == "express") {
        var pickup_time = $("#pickup_time").val() ;
        var selected_date = moment(from_picker.get('select', 'yyyy/mm/dd'));
        // var moment_date = moment(selected_date.toDate());
        var moment_date=selected_date.add(1,'days');
        $("#pickup_time").change();
        return;
    }

    /*here check what is the value of expressCounter if it is 4 the go for express service else go for 
    regular one, slots are as key and value pair e.g '1': '8am - 10am.... check if first 4 slots are available then
    got with same day delivery else save the key of greater than 4 slots value for next day delivery similarly change
    delivery dates too. */

    

    var schedule_delta = getScheduleTimeDelta();

    var selected_date = moment(from_picker.get('select', 'yyyy/mm/dd')), moment_date;
    if (schedule_delta != -1){
        moment_date = selected_date.add(schedule_delta, 'days');
    }

    if (moment_date.format("YYYY-MM-DD") == '2015-08-22') {
        moment_date.add(1, "days");
    } else {
        to_picker.set('min', moment_date.toDate());
    }
    
    to_picker.set('max', 30);
    to_picker.set('select', moment_date.toDate());
    
    $("#pickup_time").change();
}



$('a.estimator').click();
$('#login').modal({backdrop: 'static'});
