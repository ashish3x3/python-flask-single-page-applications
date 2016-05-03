define([
    'jquery',
    'can',
    '../../lib/mywash/constructs/map.helpers',
    '../../lib/mywash/components/tabs',
    'toastr',
    'nanobar',
    'datepicker',
    'momentjs',
    'summernote',
    'selectize',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'pickup-tabs',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                var pickup_self = this;
                this.order_status = new can.Map({});
                this.timeslots = new can.Map({});
                this.datepickers_initialised = false;
                this.total_quantity = can.compute(0);
                this.row_count = can.compute(0);
                this.number_print_copies = can.compute(2);

                this.nanobar = new Nanobar({
                    id: 'mybar',
                    bg: "#FF6600"
                })
                
                var statuses = JSON.parse(localStorage.getItem("statuses"));
                $.each(statuses, function(index, value){
                    pickup_self.order_status.attr(index, value);
                })
                
                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                $.each(timeslots_temp, function(index, value){
                    pickup_self.timeslots.attr(index, value);
                })
                

            },

            intervalFunc: function(){
                var now = moment();
                var current_date = moment(this.orderDate());
                if (now.format("YYYY-MM-DD") == current_date.format("YYYY-MM-DD")) {
                    this._pollData('order', now);
                };
            },

            orderData: new can.Map({}),
            loaded: false,

            cleaningItems: new can.List([]),
            modalCustomerDetails: new can.Map({}),
            allCosts: new can.Map({}),
            selectize: {},
            pickupRescheduleOldValue: new can.Map({}),
            pickupFailureReasons: new can.List([]),

            variableDate: new Date(),
            orderDate: can.compute(function(){
                return this.attr('variableDate');
            }),

            rowCount: function(){
                return this.row_count();
            },

            getFormattedDate: function(date){
                return date.format("YYYY-MM-DD");
            },

            getFormattedTime: function(date){
                return date.format("HH-mm");
            },

            orderStatusHash: function(){
                return this.order_status;
            },

            getTimeSlots: function(){
                return this.timeslots;
            },

            getNumberPrintCopies: function(){
                return this.number_print_copies();
            },

            changeNumberPrintCopies: function(context, element, event){
                this.number_print_copies(parseInt(element.val()));
            },

            _editOrderData: function(match, update){
                this.orderData.each(function(time_range_value, time_range){
                    time_range_value.each(function(value, key){
                        if (value.attr(match['key']) == match['value']) {
                            value.attr(update['key'], update['value']);
                        };
                    })
                })
            },

            orderRefresh: function(context, element, event) {
                var current_date = moment(this.orderDate());
                this._pollData('order', current_date, false, true);
            },

            getTotalQuantity: function(){
                return this.total_quantity();
            },

            pickupPrevday: function(context, element, event){
                var date = moment(this.attr('variableDate'));
                date.subtract(1, 'days');
                this.attr('variableDate', date.toDate());
                this._pollData('order', this.orderDate());
            },

            pickupTimeSlotChange: function(context, element, event){
                var index = $(element).val();
                var value = this.timeslots.attr(index);
                var oldValue = this.modalCustomerDetails.attr("data.schedules.pickup.schedule_time");
                this.pickupRescheduleOldValue.attr('timeslot', oldValue);
                this.modalCustomerDetails.attr("data.schedules.pickup.schedule_time", value);
            },

            savePickupReschedule: function(context, element, event){
                var order_id = $("#pickup-order-details-modal").attr("index");
                var date = this.modalCustomerDetails.attr("data.schedules.pickup.schedule_date");
                var timeslot = this.modalCustomerDetails.attr("data.schedules.pickup.schedule_time");
                $.ajax({
                    url: "/api/pickup",
                    type: 'put',
                    dataType: "json",
                    context: this,
                    data: {
                        order_id: order_id,
                        time: timeslot,
                        date: date
                    },
                    success: function(data){
                        toastr.success("Reschedule successful.")
                    },
                    error: function(xhr, status, error){
                        toastr.error("Reschedule unsuccessful.")
                        this.modalCustomerDetails.attr("data.schedules.pickup.schedule_date", this.pickupRescheduleOldValue.attr('date'));
                        this.modalCustomerDetails.attr("data.schedules.pickup.schedule", this.pickupRescheduleOldValue.attr('timeslot'));
                    }
                })
            },

            pickupNextday: function(context, element, event){
                var date = moment(this.attr('variableDate'));
                date.add(1, 'days');
                this.attr('variableDate', date.toDate());
                this._pollData('order', this.orderDate());
            },

            _addData: function(list){
                this.row_count(list.length);
                var map_keys = can.Map.keys(this.orderData);
                var pickup_self = this;
                var data = {}
                
                // Put the new values into the map.
                $.each(list, function(index, value){
                    var status_details = pickup_self.getStatusDetails(value['status']);
                    value['status'] = status_details.formal_name;
                    value['status_color'] = status_details.color;
                    value['user_info']['name'] = value['user_info']['name'].trim();
                    if(!data[value['schedule_time']])
                        data[value['schedule_time']] = {};
                    data[value['schedule_time']][value['order_id']] = value;
                });
                this.orderData.attr(data, true);
            },

            _updateData: function(list){
                this.row_count(list.length);
                var pickup_self = this;
                var temp = {};
                $.each(list, function(index, value){
                    temp[value['order_id']] = value['schedule_time'];
                    var status_details = pickup_self.getStatusDetails(value['status']);
                    value['status'] = status_details.formal_name;
                    value['status_color'] = status_details.color;
                    value['user_info']['name'] = value['user_info']['name'].trim();
                    var schedule_time = pickup_self.orderData.attr(value['schedule_time']);
                    if (!schedule_time)
                        pickup_self.orderData.attr(value['schedule_time'], {});
                    if(!schedule_time.attr(value['order_id'])){
                        schedule_time.attr(value['order_id'], value);
                    }else{
                        if(schedule_time.attr(value['order_id']).attr('status') != value['status']){
                            schedule_time.attr(value['order_id']).attr('status', value['status']);
                            schedule_time.attr(value['order_id']).attr('status_color', value['status_color']);
                        }

                        if(schedule_time.attr(value['order_id']).attr('pickup_sheet_printed') != value['pickup_sheet_printed']){
                            schedule_time.attr(value['order_id']).attr('pickup_sheet_printed', value['pickup_sheet_printed']);
                        }

                        if(schedule_time.attr(value['order_id']).attr('hub')){
                            if(schedule_time.attr(value['order_id']).attr('hub.short') != value['hub']['short']){
                                schedule_time.attr(value['order_id']).attr('hub', value['hub']);
                            }
                        }
                    }
                })
                
                // Collect obsolete objects
                var delete_map = {}
                this.orderData.each(function(value, key){
                    value.each(function(inner_value, inner_key){
                        if(!temp[inner_key] || temp[inner_key] != inner_value.attr('schedule_time')){
                            delete_map[inner_key] = key;
                        }
                    })
                })
                // Delete obsolete objects
                $.each(delete_map, function(key, value){
                    pickup_self.orderData.attr(value).removeAttr(key);
                })
            },

            _pollData: function(pickup_type, date, time, refresh){
                if(date) date = this.getFormattedDate(moment(date));
                if(time) time = this.getFormattedTime(moment(time));
                if(!refresh) refresh = false;
                var pollUrl = "";
                if(time){
                    pollUrl = "/api/pickup/" + date + "/" + time;
                }else{
                    pollUrl = "/api/pickup/" + date;
                }
                this.nanobar.go(30);
                
                $.ajax({
                    url: pollUrl,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                    success: function(data){
                        this.nanobar.go(50);
                        if (data.data){
                            if (refresh) {
                                this._updateData(data.data);
                            } else {
                                this._addData(data.data);
                            }
                            
                        }
                        this.nanobar.go(100);
                    }
                });
            },

            selectWashType: function(context, element, event){
                var quantity = element.parents('tr').find('input[type="number"]');
                quantity = parseInt(quantity.val());
                
                var itemIndex = element.parents('tr').attr('item-index');
                var item = this.cleaningItems.attr(itemIndex);
                if (element.hasClass('choice-laundry')) {
                    item.attr('cleaning_type','laundry');
                }else if(element.hasClass('choice-dryclean')){
                    item.attr('cleaning_type','dry_cleaning');
                }
                this._update_total_cost();
            },

            quantityChange: function(context, element, event){

                var type = element.parent();
                var quantity = parseInt(element.val());
                var cost = element.parents('tr').find('.item-cost'), final_cost = 0;
                if (quantity > -1) {
                    var itemIndex = element.parents('tr').attr('item-index');
                    var item = this.cleaningItems.attr(itemIndex);
                    
                    if (!item.attr('price.iron')) {
                        item.attr('price.iron', 0)
                    };

                    if (!item.attr('quantity'))
                        item.attr('quantity', {});


                    if (type.hasClass('laundry-quantity')) {
                        if (!item.attr('quantity.laundry'))
                            item.attr('quantity.laundry', 0);
                        item.attr('quantity.laundry', quantity);
                    }else if (type.hasClass('dryclean-quantity')) {
                        if (!item.attr('quantity.dryclean'))
                            item.attr('quantity.dryclean', 0)
                        item.attr('quantity.dryclean', quantity);
                    }else{
                        if (!item.attr('quantity.iron'))
                            item.attr('quantity.iron', 0)
                        item.attr('quantity.iron', quantity);
                    }

                    
                    
                    var laundry = (item.attr('quantity.laundry') * item.attr('price.laundry')) || 0;
                    var dryclean = (item.attr('quantity.dryclean') * item.attr('price.dry_cleaning')) || 0;
                    var iron = (item.attr('quantity.iron') * item.attr('price.iron')) || 0;

                    item.attr('final_cost', laundry + dryclean + iron);
                }
                this._update_total_cost();
                this._update_total_quantity();
            },

            openOrderModal: function(context, element, event){
                var index = $(element).parents('tr').attr('index');
                var final_data = null;
                this.nanobar.go(30);
                var item_defer = $.ajax({
                    url: "/api/orderitem/" + index,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                })

                var pickup_failure_reason_defer = $.ajax({
                    url: "/api/failurereason/pickup",
                    type: 'get',
                    dataType: 'json',
                })
                
                var pickup_self = this;
                $.when(item_defer, pickup_failure_reason_defer).then(function(item_data, reason_data){
                    item_data = item_data[0];
                    reason_data = reason_data[0];
                    pickup_self.pickupFailureReasons.replace(reason_data.data);
                    
                    pickup_self.nanobar.go(50);
                    pickup_self.cleaningItems.replace(item_data.data);
                    item_data.customer_details['status'] = pickup_self.getStatusDetails(item_data.customer_details['status']).attr('name_id')
                    pickup_self.modalCustomerDetails.attr('data', item_data.customer_details);

                    if(pickup_self.modalCustomerDetails.attr('data.bag.laundry')){
                        pickup_self.modalCustomerDetails.attr('data.bag.laundry').each(function(value, index){
                            pickup_self.selectize['laundry'].addOption({
                                value: value,
                                text: value
                            });
                            pickup_self.selectize['laundry'].addItem(value, true);
                        })
                    }
                    
                    
                    if (pickup_self.modalCustomerDetails.attr('data.bag.dryclean')) {
                        pickup_self.modalCustomerDetails.attr('data.bag.dryclean').each(function(value, index){
                            pickup_self.selectize['dryclean'].addOption({
                                value: value,
                                text: value
                            });
                            pickup_self.selectize['dryclean'].addItem(value, true);
                        })
                    };
                    
                    if (pickup_self.modalCustomerDetails.attr('data.bag.iron')) {
                        pickup_self.modalCustomerDetails.attr('data.bag.iron').each(function(value, index){
                            pickup_self.selectize['iron'].addOption({
                                value: value,
                                text: value
                            });
                            pickup_self.selectize['iron'].addItem(value, true);
                        })
                    };
                    

                    $("#pickup-order-details-modal").attr('index', index);
                    var summernote = $("#pickup-order-details-modal .summernote");
                    summernote.html(pickup_self.modalCustomerDetails.attr('data.remark'));
                    $(summernote).summernote({
                        height: 250,
                        focus: true,
                        placeholder: "Write notes!",
                        toolbar: [
                            ['style', ['style']],
                            ['font', ['bold', 'italic', 'underline', 'clear']],
                            ['color', ['color']],
                            ['para', ['ul', 'ol', 'paragraph']],
                            ['insert', ['link', 'picture', 'hr']],
                          ],
                        onChange: function(){
                            pickup_self.modalCustomerDetails.attr('data.remark', $("#pickup-order-details-modal .summernote").code());
                        }
                    });

                    $("#pickup-order-details-modal").modal({
                        backdrop: 'static',
                        keyboard: false,
                        show: true
                    });
                    pickup_self.nanobar.go(100);
                    $("#pickup-order-details-modal table").focus();
                    pickup_self._update_total_cost();
                    pickup_self._update_total_quantity();
                })

            },

            _get_sub_total_cost: function(){
                var total_cost = 0;
                this.cleaningItems.each(function(element, index){
                    var item = element;
                    var laundry = (item.attr('quantity.laundry') * item.attr('price.laundry')) || 0;
                    var dryclean = (item.attr('quantity.dryclean') * item.attr('price.dry_cleaning')) || 0;
                    var iron = (item.attr('quantity.iron') * item.attr('price.iron')) || 0;
                    total_cost += laundry + dryclean + iron;
                });
                return total_cost;
            },

            _update_total_quantity: function(){
                var total = 0;
                this.cleaningItems.each(function(element, index){
                    var item = element;
                    var laundry = item.attr('quantity.laundry') || 0;
                    var dryclean = item.attr('quantity.dryclean') || 0;
                    var iron = item.attr('quantity.iron') || 0;
                    total += laundry + dryclean + iron;
                });
                this.total_quantity(total);
            },
            
            _update_total_cost: function(){
                var sub_total_cost = this._get_sub_total_cost(), discount = null;
                var discount_amount = this.modalCustomerDetails.attr("data.discount.amount") || 0;
                var max_discount_amount = this.modalCustomerDetails.attr("data.discount.max") || 0;
                this.allCosts.attr('sub_total_cost', sub_total_cost);

                if (this.modalCustomerDetails.attr("data.discount.percentage")) {
                    discount = sub_total_cost * discount_amount/100;

                    // Check if discount is inside max discount limit
                    if (max_discount_amount) {
                        max_discount_amount = parseInt(max_discount_amount);
                        if (discount > max_discount_amount)
                            discount = max_discount_amount;
                    };
                }else{
                    discount = discount_amount;
                }

                var total_cost = sub_total_cost - discount;

                // Deduct credits if available
                var available_credits = this.modalCustomerDetails.attr("data.credits.available");
                if (!available_credits){
                    available_credits = this.modalCustomerDetails.attr("data.user.credits");
                    this.modalCustomerDetails.attr("data.credits.available", available_credits);
                }
                var used_credits = null;
                if (available_credits >= total_cost) {
                    used_credits = total_cost;
                    
                }else{
                    used_credits = available_credits;
                }
                total_cost -= used_credits;
                this.modalCustomerDetails.attr("data.credits.used", used_credits);

                this.allCosts.attr('total_cost', Math.round(total_cost));
            },

            changeMaxDiscount: function(context, element, event){
                var max_discount_amount = $('#pickup-order-details-modal .modal-discount-max-amount').val() || 0;
                this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
                this._update_total_cost();
            },

            changeDiscount: function(context, element, event){
                var discount_type = $('#pickup-order-details-modal .modal-discount-type li.active');
                this.applyDiscount(context, discount_type, event);
            },

            changePaymentStatus: function(context, element, event){
                var new_value = $(element).val();
                var order_id = $("#pickup-order-details-modal").attr('index');
                $.ajax({
                    url: "/api/order/" + order_id,
                    type: "put",
                    dataType: 'json',
                    context: this,
                    data:{
                        is_paid: new_value,
                    },
                    success: function(data){
                        toastr.success("Payment status change successful.")
                        if ($(element).val() == 'paid') {
                            this.modalCustomerDetails.attr("data.is_paid", true);
                        }else{
                            this.modalCustomerDetails.attr("data.is_paid", false);
                        }
                    },
                    error: function(xhr, status, error){
                        toastr.error("Payment status change failed.")
                    }
                })
                
            },

            applyDiscount: function(context, element, event){
                var is_percentage = $(element).hasClass('modal-discount-percentage');
                var discount_amount = $('#pickup-order-details-modal .modal-discount-amount').val() || 0;

                if (is_percentage) {
                    this.modalCustomerDetails.attr("data.discount.percentage", true);
                }else{
                    this.modalCustomerDetails.attr("data.discount.percentage", false);
                }
                this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
                this._update_total_cost();
            },

            saveOrderChanges: function(context, element, event){
                var index = $("#pickup-order-details-modal").attr('index');
                $(element).button('loading');

                var discount_data = this.modalCustomerDetails.attr("data.discount").attr()
                var bags = this.modalCustomerDetails.attr("data.bag").attr() || {};

                $.ajax({
                    url: "/api/orderitem/" + index,
                    type: "post",
                    context: this,
                    data: {
                        data: JSON.stringify(this.cleaningItems.attr()),
                        remark: this.modalCustomerDetails.attr('data.remark'),
                        discount: JSON.stringify(discount_data),
                        bag: JSON.stringify(bags),
                    },
                    success: function(data){
                        toastr.success("Saved successfully.")
                        $(element).button('reset');
                    },
                    error: function(xhr, status, error){
                        toastr.error("Saving unsuccessful. Try again.")
                        $(element).button('reset');
                    }
                })
            },

            changeOrderStatus: function(context, element, event){
                var new_value = $(element).val();
                this.modalCustomerDetails.attr("data.status", new_value);
                if (new_value != 'pickup_failed') {
                    this.saveOrderStatus(context, element, event);
                }
            },

            changePickupFailedReason: function(context, element, event) {
                if (this.modalCustomerDetails.attr("data.failure_reason.pickup")) 
                    this.modalCustomerDetails.attr("data.failure_reason").attr("pickup", {});
                this.modalCustomerDetails.attr("data.failure_reason.pickup", {
                    'full_reason': $(element).text(),
                    'reason': $(element).val()
                });
            },

            saveOrderStatus: function(context, element, event){
                var new_value = this.modalCustomerDetails.attr("data.status");
                var order_id = $("#pickup-order-details-modal").attr('index');
                var data = {
                    status: new_value,
                }

                if (new_value == 'pickup_failed') {
                    if (!this.modalCustomerDetails.attr('data.failure_reason.pickup.reason')) {
                        toastr.error("No reason selected.")
                        return;
                    };
                    data['failure_reason'] = JSON.stringify({
                        reason: this.modalCustomerDetails.attr('data.failure_reason.pickup.reason'),
                        type: 'pickup'
                    })
                }

                $.ajax({
                    url: "/api/order/" + order_id,
                    type: "put",
                    dataType: 'json',
                    context: this,
                    data: data,
                    success: function(data){
                        this.modalCustomerDetails.attr("data.status", new_value);
                        toastr.success("Status change successful.")
                    },
                    error: function(xhr, status, error){
                        toastr.error("Status change failed.")
                    }
                })
            },

            closeModal: function(context, element, event){
                this.selectize['laundry'].clear(true);
                this.selectize['laundry'].clearOptions();
                this.selectize['dryclean'].clear(true);
                this.selectize['dryclean'].clearOptions();
                this.selectize['iron'].clear(true);
                this.selectize['iron'].clearOptions();
                this.pickupRescheduleOldValue.attr({}, true);
                $("#pickup-order-details-modal .summernote").destroy();
                $("pickup-tabs .btn-refresh").trigger('click');
            },
            
            toggleRowCheck: function(context, element, event){
                if ($(element).find('i').hasClass("check-all")) {
                    var checkBoxes = $(element).parents('table').find("button i.fa-check").parent();
                    if($(element).hasClass("btn-default")){
                        $.each(checkBoxes, function(index, value){
                            $(value).addClass("btn-success");
                            $(value).removeClass("btn-default");
                        });
                    }else{
                        $.each(checkBoxes, function(index, value){
                            $(value).removeClass("btn-success");
                            $(value).addClass("btn-default");
                        });
                    }
                    
                }else{
                    if($(element).hasClass("btn-default")){
                        $(element).addClass("btn-success");
                        $(element).removeClass("btn-default");

                        // Check if all rows are now checked. If true also check the 
                        // check-all checkbox.
                        var tbodyRows = element.parents('tbody').find(".fa-check").parent();
                        var tbodyCheckedRows = element.parents('tbody').find(".fa-check")
                                                .parents('button.btn-success');
                        if (tbodyRows.length == tbodyCheckedRows.length) {
                            var checkAllToggle = element.parents('table').find(".check-all").parent();
                            checkAllToggle.removeClass("btn-default");
                            checkAllToggle.addClass("btn-success");
                        };
                    }else{
                        $(element).removeClass("btn-success");
                        $(element).addClass("btn-default");

                        // Uncheck the check-all checkbox.
                        var checkAllToggle = element.parents('table').find(".check-all").parent();
                        checkAllToggle.removeClass("btn-success");
                        checkAllToggle.addClass("btn-default");
                    }
                }
            },

            
            showPrintConfirmDialog: function(context, element, event){
                $("#pickup-print-settings-modal").modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                })
            },

            printPickupSheet: function(context, element, event){
                var rows = $(".pickup-checkbox.btn-success").parents("tr");
                var order_ids = [];
                $.each(rows, function(index, value){
                    order_ids.push($(value).attr('index'));
                })
                if (rows.length) {
                    $.ajax({
                        url: "/api/pickupsheetinfo/" + JSON.stringify(order_ids),
                        type: 'get',
                        context: this,
                        dataType: 'json',
                        success: function(data){
                            var pickup_self = this;
                            var time_interval = 3000, time_arg = 0;
                            $.each(data.data, function(key, value){
                                
                                var final_diva = $("<div>");
                                var address_div = $("<div>");
                                address_div.append($('<h5>').text("Customer details"));
                                address_div.append($('<p>').text("Order id: #" + value.real_order_id));
                                address_div.append($('<p>').text(value.user.name));
                                address_div.append($('<p>').text(
                                    value.address.apartment_number + ", "
                                    + value.address.address_1 + ", "
                                    + value.address.address_2
                                ));
                                address_div.append($('<p>').text(value.address.city + ", " + value.address.state));
                                address_div.append($('<p>').text(value.address.pincode || ""));
                                address_div.append($('<p>').text("Ph- " + value.user.phone));
                                
                                var pickup_div = $("<div>");
                                pickup_div.append($('<h5>').text("Pickup"));
                                pickup_div.append($('<p>').text("Date: " + value.schedules[0].pickup.schedule_date))
                                pickup_div.append($('<p>').text("Time: " + value.schedules[0].pickup.schedule_time))

                                var delivery_div = $("<div>");
                                delivery_div.append($('<h5>').text("Delivery"));
                                delivery_div.append($('<p>').text("Date: " + value.schedules[0].delivery.schedule_date))
                                delivery_div.append($('<p>').text("Time: " + value.schedules[0].delivery.schedule_time))


                                final_diva.append(address_div);
                                final_diva.append("<hr>");
                                final_diva.append(pickup_div);
                                final_diva.append("<hr>");
                                final_diva.append(delivery_div);
                                
                                var final_div = $("<div>").addClass("container-fluid pickup-sheet-font").css({"padding": "50px", "margin-top": "20px", "font-size": "10px"}).append(final_diva);

                                setTimeout(function(){
                                    for (var i = 0; i < pickup_self.getNumberPrintCopies(); i++) {
                                        final_div.print({
                                            mediaPrint: true
                                        })
                                    };

                                    $.ajax({
                                        url: "/api/order/" + value.order_id,
                                        type: 'put',
                                        dataType: 'json',
                                        context: pickup_self,
                                        data: {
                                            pickup_sheet_printed: true
                                        },
                                        success: function(data){
                                            pickup_self._editOrderData(
                                                {
                                                    'key': 'order_id',
                                                    'value': value.order_id
                                                },
                                                {
                                                    'key': 'pickup_sheet_printed',
                                                    'value': true
                                                }
                                            )
                                        }
                                    })

                                }, time_arg)
                                time_arg += time_interval;
                            })

                            $("#pickup-print-settings-modal").modal('hide');
                        }
                    })
                }else{
                    toastr.warning("Select an order first.")
                }
            },
        }),

        helpers: $.extend(BaseHelpers, {
            multiply: function(a, b, options){
                return a() * b();
            },

        }),

        events: {
            '{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-pickup" && !this.scope.loaded) {
                    // this context for setInterval()
                    this.scope._pollData('order', moment());
                    setInterval(this.scope.intervalFunc.bind(this.scope), 5*60*1000)
                    this.scope.loaded = true;
                }
            },

            '#pickup-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },


            'inserted': function(){
                var pickup_self = this;
                var options = {
                    format: "yyyy-mm-dd",
                    startdate: "2014-10-22",
                    autoclose: true,
                    todayBtn: true
                }
                $("pickup-tabs .order-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    var order_id = $("#pickup-order-details-modal").attr("index");
                    var formatted_value = selectedDate.format("YYYY/MM/DD");
                    pickup_self.scope._pollData('order', selectedDate);
                    pickup_self.scope.attr('variableDate', selectedDate.toDate());
                })
                
                $("#pickup-order-details-modal .modal-pickup-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    var order_id = $("#pickup-order-details-modal").attr("index");
                    var formatted_value = selectedDate.format("YYYY/MM/DD");
                    var oldValue = pickup_self.scope.modalCustomerDetails.attr("data.schedules.pickup.schedule_date")
                    pickup_self.scope.pickupRescheduleOldValue.attr('date', oldValue);
                    pickup_self.scope.modalCustomerDetails.attr("data.schedules.pickup.schedule_date", selectedDate.format("YYYY/MM/DD"))
                })

                //------------------------- SELECTIZE LAUNDRY------------------------------
                var selectize_laundry = $('#pickup-modal-others .bag-laundry').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: function(input) {
                        return {
                            value: input.toUpperCase(),
                            text: input.toUpperCase()
                        }
                    },

                    onItemAdd: function(value, item, silent){
                        if(!silent){
                            this.addedItem = value;
                            this.addEvent = true;
                        }
                        var item = pickup_self.scope.modalCustomerDetails.attr('data');
                        if(typeof item.attr("bag") == 'undefined'){
                            item.attr("bag", {})
                        }
                        if (!item.attr('bag').attr("laundry"))
                            item.attr('bag').attr("laundry", []);

                        if(item.attr('bag').attr("laundry").indexOf(value) == -1)
                            item.attr('bag').attr("laundry").push(value);
                    },

                    onItemRemove: function(value, item, silent){
                        if(!silent){
                            this.removeEvent = true;
                            this.removedItem = value;
                        }
                        var item = pickup_self.scope.modalCustomerDetails.attr('data.bag').attr("laundry");
                        var index = item.indexOf(value);
                        item.removeAttr(index);
                    },

                    onChange: function(value){
                        var alter_bags = [], action = 'add';
                        if (this.addEvent) {
                            alter_bags.push(this.addedItem);
                        }else if (this.removeEvent){
                            action = 'remove';
                            alter_bags.push(this.removedItem);
                        }
                        $.ajax({
                            url: "/api/order/" + pickup_self.scope.modalCustomerDetails.attr('data._id'),
                            type: 'put',
                            dataType: 'json',
                            data: {
                                bags: JSON.stringify([
                                    {
                                        type: 'laundry',
                                        name: alter_bags,
                                        action: action
                                    }
                                ])
                            },
                            success: function(data){
                                
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })

                        this.addEvent = false;
                        this.removeEvent = false;
                    }

                });

                //------------------------- SELECTIZE DRYCLEAN------------------------------
                var selectize_dryclean = $('#pickup-modal-others .bag-dryclean').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: function(input) {
                        return {
                            value: input.toUpperCase(),
                            text: input.toUpperCase()
                        }
                    },

                    onItemAdd: function(value, item, silent){
                        if(!silent){
                            this.addedItem = value;
                            this.addEvent = true;
                        }
                        var item = pickup_self.scope.modalCustomerDetails.attr('data');
                        if(typeof item.attr("bag") == 'undefined'){
                            item.attr("bag", {})
                        }
                        if (!item.attr('bag').attr("dryclean"))
                            item.attr('bag').attr("dryclean", []);

                        if(item.attr('bag').attr("dryclean").indexOf(value) == -1)
                            item.attr('bag').attr("dryclean").push(value);
                    },

                    onItemRemove: function(value, item, silent){
                        if(!silent){
                            this.removeEvent = true;
                            this.removedItem = value;
                        }
                        var item = pickup_self.scope.modalCustomerDetails.attr('data.bag').attr("dryclean");
                        var index = item.indexOf(value);
                        item.removeAttr(index);
                    },

                    onChange: function(value){
                        var alter_bags = [], action = 'add';
                        if (this.addEvent) {
                            alter_bags.push(this.addedItem);
                        }else if (this.removeEvent){
                            action = 'remove';
                            alter_bags.push(this.removedItem);
                        }
                        $.ajax({
                            url: "/api/order/" + pickup_self.scope.modalCustomerDetails.attr('data._id'),
                            type: 'put',
                            dataType: 'json',
                            data: {
                                bags: JSON.stringify([
                                    {
                                        type: 'dryclean',
                                        name: alter_bags,
                                        action: action
                                    }
                                ])
                            },
                            success: function(data){
                                
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })

                        this.addEvent = false;
                        this.removeEvent = false;
                    }

                });
                

                //------------------------- SELECTIZE IRON------------------------------
                var selectize_iron = $('#pickup-modal-others .bag-iron').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: function(input) {
                        return {
                            value: input.toUpperCase(),
                            text: input.toUpperCase()
                        }
                    },

                    onItemAdd: function(value, item, silent){
                        if(!silent){
                            this.addedItem = value;
                            this.addEvent = true;
                        }
                        var item = pickup_self.scope.modalCustomerDetails.attr('data');
                        if(typeof item.attr("bag") == 'undefined'){
                            item.attr("bag", {})
                        }
                        if (!item.attr('bag').attr("iron"))
                            item.attr('bag').attr("iron", []);

                        if(item.attr('bag').attr("iron").indexOf(value) == -1)
                            item.attr('bag').attr("iron").push(value);
                    },

                    onItemRemove: function(value, item, silent){
                        if(!silent){
                            this.removeEvent = true;
                            this.removedItem = value;
                        }
                        var item = pickup_self.scope.modalCustomerDetails.attr('data.bag').attr("iron");
                        var index = item.indexOf(value);
                        item.removeAttr(index);
                    },

                    onChange: function(value){
                        var alter_bags = [], action = 'add';
                        if (this.addEvent) {
                            alter_bags.push(this.addedItem);
                        }else if (this.removeEvent){
                            action = 'remove';
                            alter_bags.push(this.removedItem);
                        }
                        $.ajax({
                            url: "/api/order/" + pickup_self.scope.modalCustomerDetails.attr('data._id'),
                            type: 'put',
                            dataType: 'json',
                            data: {
                                bags: JSON.stringify([
                                    {
                                        type: 'iron',
                                        name: alter_bags,
                                        action: action
                                    }
                                ])
                            },
                            success: function(data){
                                
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })

                        this.addEvent = false;
                        this.removeEvent = false;
                    }

                });

                

                pickup_self.scope.selectize = {
                    'laundry': selectize_laundry[0].selectize,
                    'dryclean': selectize_dryclean[0].selectize,
                    'iron': selectize_iron[0].selectize,
                }

            },

            ".click-to-assign click": function(element, event){
                var pickup_self = this;
                var order_id = element.parents('tr').attr('index');
                var arr_id = null;
                pickup_self.scope.orderData.each(function(order, key){
                    if(order.attr(order_id)) arr_id = key;
                })
                var select = $('<select type="text" placeholder="Select staff">');
                $(element).parents('td').append(select);
                $(element).hide();
                var selectize_employee = $(select).selectize({
                    valueField: 'str_id',
                    labelField: 'name',
                    searchField: ['name', 'emp_id'],
                    preload: true,
                    create: false,
                    dataAttr: 'data-data',

                    render: {
                        item : function(item, escape){
                            return '<div>' + 
                                        '<span>' + escape(item.name) + '</span>&nbsp;' +
                                    '</div>';
                        },
                        option: function(item, escape) {
                            return '<div>' + 
                                        '<span>' + escape(item.name) + " <b>(" + item.emp_id + ")</b>" + '</span>&nbsp;' +
                                    '</div>';
                        }
                    },
                    
                    load: function(query, callback){
                        // if(!query.length) return callback();
                        // query = query.toLowerCase();
                        $.ajax({
                            url : "/api/employee",
                            type : 'get',
                            context: this,
                            dataType : 'json',
                            success: function(data){
                                var arr = [];
                                $.each(data.data, function(index, value){
                                    arr.push({
                                        emp_id: value.emp_id,
                                        name: value.data.name,
                                        str_id: value.str_id
                                    })
                                })
                                callback(arr);
                                var assigned_to = pickup_self.scope.orderData.attr(arr_id).attr(order_id + ".assigned_to");
                                var selectize = this.$input[0].selectize;
                                if (assigned_to){
                                    selectize.addItem(assigned_to['str_id'], true);
                                }

                            },
                            error: function(xhr, status, error){
                                callback();
                            }
                        });
                    },

                    onItemAdd: function(value, item){
                        
                    },
                }).change(function(event){
                    $.ajax({
                        url: "/api/pickup",
                        type: 'put',
                        dataType: 'json',
                        context: this,
                        data: {
                            order_id: order_id,
                            assign_to: select.val()
                        },
                        success: function(data){
                            var selectize = selectize_employee[0].selectize;
                            toastr.success("Assigned " + selectize.getItem(selectize.getValue()).text())
                            var value = {
                                'name': selectize.getItem(selectize.getValue()).text().toLowerCase().trim(),
                                'str_id': selectize.getValue()
                            }
                            var order = pickup_self.scope.orderData.attr(arr_id).attr(order_id);
                            if(!order.attr("assigned_to"))
                                order.attr("assigned_to", {})
                            order.attr("assigned_to").attr("name", value['name']);
                            order.attr("assigned_to").attr("str_id", value['str_id']);
                            order.attr("status", pickup_self.scope.getStatusDetails('pickup_progress').formal_name);
                            selectize.destroy();
                            $(element).siblings('select').remove();
                            $(element).show();
                        },
                        error: function(){
                            toastr.error("Unable to update.")
                        }
                    })
                })
              

            },

            "#pickup-orders click": function(element, event){
                var staff_arr = $("#pickup-orders .click-to-assign + .selectized");
                var hub_arr = $("#pickup-orders .click-to-assign-hub + .selectized");
                if (staff_arr.length) {
                    staff_arr.each(function(index, value){
                        if(!($(value).parents('tr').attr('index') == $(event.target).parents('tr').attr('index'))){
                            var selectize = $(value).selectize()
                            selectize = selectize[0].selectize;
                            selectize.destroy();
                            $(value).siblings('a').show();
                            $(value).remove();
                        }
                    })
                }

                if (hub_arr.length) {
                    hub_arr.each(function(index, value){
                        if(!($(value).parents('tr').attr('index') == $(event.target).parents('tr').attr('index'))){
                            var selectize = $(value).selectize()
                            selectize = selectize[0].selectize;
                            selectize.destroy();
                            $(value).siblings('span.label').show();
                            $(value).remove();
                        }
                    })
                }
                
            },

            ".click-to-assign-hub click": function(element, event){
                var pickup_self = this;
                var order_id = element.parents('tr').attr('index');
                var arr_id = null;
                pickup_self.scope.orderData.each(function(order, key){
                    if(order.attr(order_id)) arr_id = key;
                })
                var select = $('<select type="text" placeholder="Select hub">');
                $(element).parents('td').append(select);
                $(element).hide();
                var selectize_employee = $(select).selectize({
                    valueField: 'str_id',
                    labelField: 'name',
                    searchField: ['name', 'short'],
                    preload: true,
                    create: false,

                    render: {
                        item : function(item, escape){
                            return '<div>' + 
                                        '<span>' + escape(item.name) + '</span>&nbsp;' +
                                    '</div>';
                        },
                        option: function(item, escape) {
                            return '<div>' + 
                                        '<span>' + escape(item.name) + " <b>(" + item.short + ")</b>" + '</span>&nbsp;' +
                                    '</div>';
                        }
                    },
                    
                    load: function(query, callback){
                        // if(!query.length) return callback();
                        // query = query.toLowerCase();
                        $.ajax({
                            url : "/api/hub",
                            type : 'get',
                            context: this,
                            dataType : 'json',
                            success: function(data){
                                var arr = [];
                                $.each(data.data, function(index, value){
                                    arr.push({
                                        short: value.short,
                                        name: value.name,
                                        str_id: value.str_id
                                    })
                                })
                                callback(arr);
                                var assigned_hub = pickup_self.scope.orderData.attr(arr_id).attr(order_id + ".hub");
                                var selectize = this.$input[0].selectize;
                                if (assigned_hub){
                                    selectize.addItem(assigned_hub['str_id'], true);
                                }

                            },
                            error: function(xhr, status, error){
                                callback();
                            }
                        });
                    },

                    onChange: function(value){
                        var order = pickup_self.scope.orderData.attr(arr_id).attr(order_id);
                        $.ajax({
                            url: "/api/address/" + order.attr('address_id'),
                            type: 'put',
                            dataType: 'json',
                            context: this,
                            data: {
                                assigned_hub: value
                            },
                            success: function(data){
                                var hub = data.update_data.assigned_hub;
                                var selectize = this.$input[0].selectize;
                                toastr.success("Assigned to " + hub.name);
                                if(!order.attr("hub"))
                                    order.attr("hub", {})
                                order.attr("hub", hub);
                                selectize.destroy();
                                $(element).siblings('select').remove();
                                $(element).show();
                            },
                            error: function(){
                                toastr.error("Unable to update.")
                            }
                        })
                    },
                })

            }
        }
    })
})