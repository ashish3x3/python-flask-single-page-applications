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
    if (val.length > 13) $(this).val(val.substr(0,13));
    if (isNaN(val)) $(this).val(val.match(/\+?[0-9]*/));
});

$('#submitEditAddress_1').hide();
    $('#tag_1').click(function(event) {
        $('#submitEditAddress_1').toggle();
});

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
    //disable: [[2015,4,1], [2015,4,2], [2015,4,3]]
});


var from_$input = $('#pickup_date').pickadate(),
    from_picker = from_$input.pickadate('picker')

// from_picker.set('disable',[new Date(2015,6,1)]);

var to_$input = $('#schedule_date').pickadate(),
    to_picker = to_$input.pickadate('picker')

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
    return default_delta;
}

function setTurnAroundTime(){

    var delivery_date = moment($("#schedule_date").val());
    var pickup_date = moment($("#pickup_date").val());
    var slots;

    var default_delta = getScheduleTimeDelta();
    var delta = moment(delivery_date - pickup_date).date() - 1;
    var pickup_time_index = '0';

    if (delta == default_delta) {
        pickup_time_index = $('#pickup_time').val();
    }

    if (all_timeslots.timeslots_delivery.length) {
        $.each(all_timeslots.timeslots_delivery, function(index, value){
            if (value.date == delivery_date.format('YYYY-MM-DD')) {
                slots = value.slots_available
                return false;
            } else {
                slots = all_timeslots.data;
            }
        });
    } else {
        slots= all_timeslots.data;
    }

    if (selectedServiceType == "express") {

        pickup_time_index = parseInt($('#pickup_time').val());

        $("#schedule_time").html('');
    
        $.each(slots, function(key, value) {
            if (value != undefined || value != null){
                
                if (key == '0') {
                    $("#schedule_time").append($("<option/>", {
                        value: key,
                        text: value
                    }));
                    $("#schedule_time").prop('disabled', 'disabled');
                    return false;
                }

                if (key >= (pickup_time_index+4)%7) {
                    $("#schedule_time").append($("<option/>", {
                        value: key,
                        text: value
                    }));
                    $("#schedule_time").prop('disabled', false);
                } else {
                    $("#schedule_time").append($("<option/>", {
                        value: '0',
                        text: 'No Slots Are Available'
                    }));
                    $("#schedule_time").prop('disabled', 'disabled');
                    return false;
                }
            }
        });

        var selected_date = moment(from_picker.get('select', 'yyyy/mm/dd'));

        var moment_date = moment(selected_date.toDate());
        moment_date.add(1, 'days');

        if (pickup_time_index < 4 && pickup_time_index !=null) {
            to_picker.set('min', selected_date.toDate());
            to_picker.set('select', selected_date.toDate());
            setDeliveredTimeSlot();



        } else {
            to_picker.set('min', moment_date.toDate());
            to_picker.set('select', moment_date.toDate());
            setDeliveredTimeSlot();

        }
        return ;
    };
    
    $("#schedule_time").html('');
    
    $.each(slots, function(key, value) {
        if (value != undefined || value != null){
            
            if (key == '0') {
                $("#schedule_time").append($("<option/>", {
                    value: key,
                    text: value
                }));
                $("#schedule_time").prop('disabled', 'disabled');
                return false;
            }

            if (key >= pickup_time_index) {
                $("#schedule_time").append($("<option/>", {
                    value: key,
                    text: value
                }));
                $("#schedule_time").prop('disabled', false);
            } else {
                $("#schedule_time").append($("<option/>", {
                    value: '0',
                    text: 'No Slots Are Available'
                }));
                $("#schedule_time").prop('disabled', 'disabled');
                return false;
            }
        }
    });


    
}

function setDeliveredTimeSlot() {
    var delivery_date = moment($("#schedule_date").val());
    var date = to_picker.get('select', 'yyyy-mm-dd');

    if (date == all_timeslots.date_today) {
        slots = all_timeslots.filtered_slots;
    } else {
        if (all_timeslots.timeslots_pickup.length) {
            $.each(all_timeslots.timeslots_pickup, function(index, value){
                if (value.date == date) {
                    slots = value.slots_available
                }else{
                    slots = all_timeslots.data;
                }
            });
        } else {
            slots = all_timeslots.data;
        }
    }

    var date_picked = moment($("#pickup_date").val());
    var date_scheduled = moment($("#schedule_date").val());

    var date_diff = date_picked.date() - date_scheduled.date();

    if(date_diff == 0 ){
        $("#schedule_time").html('');
        pickup_time_index = parseInt($('#pickup_time').val());
        $.each(slots, function(key, value) {
            if (value != undefined || value != null){
                if (key >= (pickup_time_index+4)) {
                    $("#schedule_time").append($("<option/>", {
                        value: key,
                        text: value
                    }));
                    $("#schedule_time").prop('disabled', false);
                }
            }
        });
        if (!$("#schedule_time option").length) {
            $("#schedule_time").html("<option>Change pickup date<option/>");
            $("#schedule_time").prop('disabled', true);
        };
        return;
    }
    

    pickup_time_index = parseInt($('#pickup_time').val());
    $("#schedule_time").html('');
    
     $.each(slots, function(key, value) {
        if (value != undefined || value != null){
            if (key >= (pickup_time_index+4)%7) {
                $("#schedule_time").append($("<option/>", {
                    value: key,
                    text: value
                }));
                $("#schedule_time").prop('disabled', false);
            }
            
            if (key == '0') {
                $("#schedule_time").prop('disabled', 'disabled');
            }
            else {
                $("#schedule_time").prop('disabled', false);
            }
        }
    });

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
//    var date_picked = moment($("#pickup_date").val());
    var slots;
    var date = from_picker.get('select', 'yyyy-mm-dd');

    if ( all_timeslots !=null && date == all_timeslots.date_today) {
        slots = all_timeslots.filtered_slots;
    } else {
        if (all_timeslots.timeslots_pickup.length) {
            $.each(all_timeslots.timeslots_pickup, function(index, value){
                if (value.date == date) {
                    slots = value.slots_available
                }else{
                    slots = all_timeslots.data;
                }
            });
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
        var moment_date = moment(selected_date.toDate());
        moment_date.add(1, 'days');

        if (pickup_time < 4 && pickup_time !=null) {
            to_picker.set('min', selected_date.toDate());
            to_picker.set('select', selected_date.toDate());
            setDeliveredTimeSlot();
        }else {
            to_picker.set('min', moment_date.toDate());
            to_picker.set('select', moment_date.toDate());
            setDeliveredTimeSlot();
        }
        return;
    }

    /*here check what is the value of expressCounter if it is 4 the go for express service else go for 
    regular one, slots are as key and value pair e.g '1': '8am - 10am.... check if first 4 slots are available then
    got with same day delivery else save the key of greater than 4 slots value for next day delivery similarly change
    delivery dates too. */

    

    var schedule_delta = getScheduleTimeDelta();

    var selected_date = moment(from_picker.get('select', 'yyyy/mm/dd'));
    if (schedule_delta != -1)
        var moment_date = selected_date.add(schedule_delta, 'days');

    to_picker.set('min', moment_date.toDate());
    to_picker.set('select', moment_date.toDate());
    setDeliveredTimeSlot();
}



$('a.estimator').click();
$('#login').modal({backdrop: 'static'});


// $('select').customSelect();

function checkLocationHubAssigned(){
    return $("#address_id option:selected").attr('hub_assigned') == 'true' ? true : false;
}