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
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'ofd-tabs',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                var ofd_self = this;
                this.order_status = new can.Map({});
                this.timeslots = new can.Map({})
                this.total_quantity = can.compute(0);
                this.row_count = can.compute(0);

                this.nanobar = new Nanobar({
                    id: 'mybar',
                    bg: "#FF6600"
                })

                var statuses = JSON.parse(localStorage.getItem("statuses"));
                $.each(statuses, function(index, value){
                    ofd_self.order_status.attr(index, value);
                })
                
                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                $.each(timeslots_temp, function(index, value){
                    ofd_self.timeslots.attr(index, value);
                })

            },

            orderData: new can.Map({}),
            loaded: false,
            failureReasons: new can.List([]),

            cleaningItems: new can.List([]),
            modalCustomerDetails: new can.Map({}),
            allCosts: new can.Map({}),
            deliveryRescheduleOldValue: new can.Map({}),
            deliveryFailureReasons: new can.List([]),

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

            captureEnterKey: function(context, element, event) {
                if (event.keyCode == 13) $("#ofd-orders .btn-search-go").trigger('click');
            },

            searchOrders: function(context, element, event) {
                this._searchOrders();
                this._searchOrdersDeferred();
            },

            getOrderDataKey: function(order_id){
                var arr_id;
                this.orderData.each(function(order, key){
                    if(order.attr(order_id)) arr_id = key;
                })
                return arr_id;
            },

            _searchOrders: function() {
                var search_term = $.trim($("#ofd-orders .search-input").val()).toUpperCase();
                if(search_term == ""){
                    this.orderRefresh();
                    return;
                }
                this.ofd_search_defer = $.ajax({
                    url: "/api/order/" + search_term,
                    type: 'put',
                    dataType: 'json',
                    context: this,
                    data: {
                        status: 'delivery_progress'
                    }
                })
            },

            _searchOrdersDeferred: function() {
                this.ofd_search_defer.done(function(data){
                    $("#ofd-orders .search-input").val('');
                    this.orderRefresh();
                })

                this.ofd_search_defer.fail(function(xhr, status, error){
                    this.nanobar.go(100);
                    toastr.error(xhr.responseJSON['error'])
                })
            },
            
            orderRefresh: function(context, element, event) {
                var current_date = moment(this.orderDate());
                this._pollData();
            },

            getTotalQuantity: function(){
                return this.total_quantity();
            },

            deliveryTimeSlotChange: function(context, element, event){
                var index = $(element).val();
                if (index == 0) {
                    index = $(element).attr('value');
                };
                var value = this.timeslots.attr(index);
                var oldValue = this.modalCustomerDetails.attr("data.schedules.delivery.schedule");
                this.deliveryRescheduleOldValue.attr('timeslot', oldValue);
                this.modalCustomerDetails.attr("data.schedules.delivery.schedule", value);
            },

            saveDeliveryReschedule: function(context, element, event){
                var order_id = $("#ofd-details-modal").attr("index");
                var date = this.modalCustomerDetails.attr("data.schedules.delivery.schedule_date");
                var timeslot = this.modalCustomerDetails.attr("data.schedules.delivery.schedule");
                $.ajax({
                    url: "/api/delivery",
                    type: 'put',
                    dataType: "json",
                    context: this,
                    data: {
                        order_id: order_id,
                        time: value
                    },
                    success: function(data){
                        toastr.success("Reschedule successful.")
                    },
                    error: function(xhr, status, error){
                        toastr.success("Reschedule unsuccessful.")
                        this.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", this.deliveryRescheduleOldValue.attr('date'));
                        this.modalCustomerDetails.attr("data.schedules.delivery.schedule", this.deliveryRescheduleOldValue.attr('timeslot'));
                    }
                })
            },
            
            _addData: function(list){
                this.row_count(list.length);
                var map_keys = can.Map.keys(this.orderData);
                var ofd_self = this;
                var data = {}

                // Put the new values into the map.
                $.each(list, function(index, value){
                    var status_details = ofd_self.getStatusDetails(value['status']);
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
                var ofd_self = this;
                var temp = {};
                $.each(list, function(index, value){
                    temp[value['order_id']] = value['schedule_time'];
                    var status_details = ofd_self.getStatusDetails(value['status']);
                    value['status'] = status_details.formal_name;
                    value['status_color'] = status_details.color;
                    value['user_info']['name'] = value['user_info']['name'].trim();
                    if (!ofd_self.orderData.attr(value['schedule_time']))
                        ofd_self.orderData.attr(value['schedule_time'], {});
                    if(!ofd_self.orderData.attr(value['schedule_time']).attr(value['order_id'])){
                        ofd_self.orderData.attr(value['schedule_time']).attr(value['order_id'], value);
                    }else{
                        if(!ofd_self.orderData.attr(value['schedule_time']).attr(value['order_id']).attr('status') != value['status']){
                            ofd_self.orderData.attr(value['schedule_time']).attr(value['order_id']).attr('status', value['status']);
                            ofd_self.orderData.attr(value['schedule_time']).attr(value['order_id']).attr('status_color', value['status_color']);
                        }
                    }
                })

                // Collect obsolete objects
                var delete_map = {}
                this.orderData.each(function(value, key){
                    value.each(function(inner_value, inner_key){
                        if(!temp[inner_key] || temp[inner_key] != inner_value.attr('schedule_time')){
                            delete_map[key] = inner_key;
                        } 
                    })
                })

                // Delete obsolete objects
                $.each(delete_map, function(key, value){
                    ofd_self.orderData.attr(key).removeAttr(value);
                })
            },

            _pollData: function(refresh){
                if(!refresh) refresh = false;
                var pollUrl = "/api/ofd";
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

                var failure_reason_defer = $.ajax({
                    url: "/api/failurereason/partial_payment",
                    type: 'get',
                    dataType: 'json',
                })

                var delivery_failure_reason_defer = $.ajax({
                    url: "/api/failurereason/delivery",
                    type: 'get',
                    dataType: 'json',
                })

                var ofd_self = this;
                $.when(item_defer, failure_reason_defer, delivery_failure_reason_defer).done(function(item_data, reason_data, delivery_data){
                    item_data = item_data[0];
                    reason_data = reason_data[0];
                    delivery_data = delivery_data[0];

                    ofd_self.deliveryFailureReasons.replace(delivery_data.data);
                    
                    ofd_self.failureReasons.attr(reason_data.data);
                    ofd_self.nanobar.go(50);
                    ofd_self.cleaningItems.replace(item_data.data);
                    item_data.customer_details['status'] = ofd_self.getStatusDetails(item_data.customer_details['status']).attr('name_id')

                    ofd_self.modalCustomerDetails.attr('data', item_data.customer_details);
                    if (!ofd_self.modalCustomerDetails.attr('data.failure_reason.partial_payment')){
                        ofd_self.modalCustomerDetails.attr('data.failure_reason.partial_payment', {'type': ''});
                    } else {
                        ofd_self.modalCustomerDetails.attr('data.failure_reason.partial_payment').attr('type', '');
                    }

                    var reason_others = true;

                    if (ofd_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason")) {
                        ofd_self.failureReasons.each(function(value, index){
                            if (ofd_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason") == value.attr('str_id')){
                                ofd_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason",value.attr('str_id'));
                                reason_others = false;
                            }
                        })
                        if (reason_others){
                            ofd_self.modalCustomerDetails.attr('data.failure_reason.partial_payment.type', 'others');
                        }
                    }

                    $("#ofd-details-modal").attr('index', index);
                    var summernote = $("#ofd-details-modal .summernote");
                    summernote.html(ofd_self.modalCustomerDetails.attr('data.remark'));
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
                            ofd_self.modalCustomerDetails.attr('data.remark', $("#ofd-details-modal .summernote").code());
                        }
                    });

                    $("#ofd-details-modal").modal({
                        backdrop: 'static',
                        keyboard: false,
                        show: true
                    });
                    ofd_self.nanobar.go(100);
                    $("#ofd-details-modal table").focus();
                    ofd_self._update_total_cost();
                    ofd_self._update_total_quantity();
                    //ofd_self.changePaymentStatus();
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
                var service_type = this.modalCustomerDetails.attr('data.service_type');
                var service_tax = this.modalCustomerDetails.attr('data.service_tax').attr();
                var min_order = this.modalCustomerDetails.attr("data.discount.min_order") ||0;

                this.allCosts.attr('sub_total_cost', sub_total_cost);

                if (this.modalCustomerDetails.attr("data.discount.percentage")) {
                    //condition to check if minimum order exists, implies discount_amount
                    if (min_order) {
                        if(sub_total_cost>=min_order){
                            discount = sub_total_cost * discount_amount/100;
                        }else{
                            discount =0;
                        }
                    }else{
                        discount = sub_total_cost * discount_amount/100;
                    }
                    
                }else{
                    if (min_order) {
                        if(sub_total_cost>=min_order){
                            discount = discount_amount;
                        }else{
                            discount =0;
                        }
                    }else{
                        discount = discount_amount;
                    }
                }

                // Check if discount is inside max discount limit
                if (max_discount_amount) {
                    max_discount_amount = parseInt(max_discount_amount);
                    if (discount > max_discount_amount){
                        discount = max_discount_amount;
                    }
                };

                if (!this.modalCustomerDetails.attr("data.discount.percentage")) {
                    this.modalCustomerDetails.attr("data.discount.amount", discount);
                }

                var total_cost = sub_total_cost - discount;
                var service_tax_amount = Math.round(total_cost * service_tax['rate']/100);

                if (this.modalCustomerDetails.attr("data.service_tax.type") == 'inclusive') {
                    this.allCosts.attr('service_tax', service_tax_amount)
                } else if(this.modalCustomerDetails.attr("data.service_tax.type") == 'exclusive') {
                    total_cost += service_tax_amount;
                    this.allCosts.attr('service_tax', service_tax_amount)
                }

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
                var max_discount_amount = $('#ofd-details-modal .modal-discount-max-amount').val() || 0;
                this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
                this._update_total_cost();
            },

            changeDiscount: function(context, element, event){
                var discount_type = $('#ofd-details-modal .modal-discount-type li.active');
                this.applyDiscount(context, discount_type, event);
            },

            applyDiscount: function(context, element, event){
                var is_percentage = $(element).hasClass('modal-discount-percentage');
                var discount_amount = $('#ofd-details-modal .modal-discount-amount').val() || 0;

                if (is_percentage) {
                    this.modalCustomerDetails.attr("data.discount.percentage", true);
                }else{
                    this.modalCustomerDetails.attr("data.discount.percentage", false);
                }
                this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
                this._update_total_cost();
            },

            saveOrderChanges: function(context, element, event){
                var index = $("#ofd-details-modal").attr('index');
                $(element).button('loading');

                var discount_data = this.modalCustomerDetails.attr("data.discount").attr()
                var bags = this.modalCustomerDetails.attr("data.bag").attr() || {}

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
            
            changeBagNumber: function(context, element, event){
                if(typeof this.modalCustomerDetails.attr('data').attr("bag") == 'undefined'){
                    this.modalCustomerDetails.attr('data').attr("bag", {})
                }
                if ($(element).hasClass("bag-laundry")) {
                    this.modalCustomerDetails.attr('data.bag').attr("laundry", $(element).val());
                } else if ($(element).hasClass("bag-dryclean")) {
                    this.modalCustomerDetails.attr('data.bag').attr("dryclean", $(element).val());
                } else if ($(element).hasClass("bag-iron")) {
                    this.modalCustomerDetails.attr('data.bag').attr("iron", $(element).val());
                };
            },

            changeOrderStatus: function(context, element, event){
                var new_value = $(element).val();
                this.modalCustomerDetails.attr("data.status", new_value);
                if (new_value != 'delivery_failed') {
                    this.saveOrderStatus(context, element, event);
                }
            },

            changeDeliveryFailedReason: function(context, element, event) {
                if (this.modalCustomerDetails.attr("data.failure_reason.delivery")) 
                    this.modalCustomerDetails.attr("data.failure_reason").attr("delivery", {});
                this.modalCustomerDetails.attr("data.failure_reason.delivery", {
                    'full_reason': $(element).text(),
                    'reason': $(element).val()
                });
            },

            saveOrderStatus: function(context, element, event){
                var new_value = this.modalCustomerDetails.attr("data.status");
                var order_id = $("#ofd-details-modal").attr('index');
                var data = {
                    status: new_value,
                }

                if (new_value == 'delivery_failed') {
                    if (!this.modalCustomerDetails.attr('data.failure_reason.delivery.reason')) {
                        toastr.error("No reason selected.")
                        return;
                    };
                    data['failure_reason'] = JSON.stringify({
                        reason: this.modalCustomerDetails.attr('data.failure_reason.delivery.reason'),
                        type: 'delivery'
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
                        toastr.success("Status changed successfully!")
                    }
                })
            },

            closeModal: function(context, element, event){
                $("#ofd-details-modal .summernote").destroy();
                this.orderRefresh();
                this.deliveryRescheduleOldValue.attr({}, true);
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
        }),

        helpers: $.extend(BaseHelpers, {
            multiply: function(a, b, options){
                return a() * b();
            },
        }),

        events: {
            '{can.route} sidebarmenu': function(route){
                var now = moment();
                if (route.sidebarmenu == "main-content-ofd" && !this.scope.loaded) {
                    this.scope._pollData();
                    this.scope.loaded = true;
                };
            },

            '#ofd-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },

            'inserted': function(){
                var ofd_self = this;
                var options = {
                    format: "yyyy-mm-dd",
                    startdate: "2014-10-22",
                    autoclose: true,
                    todayBtn: true
                }

                // var selectize_order_id = $("#ofd-orders .search-input").selectize({
    //                 valueField: 'str_id',
    //                 labelField: 'name',
    //                 searchField: ['name', 'order_id'],
    //                 create: false,

    //                 render: {
    //                     item : function(item, escape){
    //                         return '<div>' + 
    //                                     '<span>' + escape(item.name) + '</span>&nbsp;' +
    //                                 '</div>';
    //                     },
    //                     option: function(item, escape) {
    //                         return '<div>' + 
    //                                     '<span>' + escape(item.name) + " <b>(" + item.order_id + ")</b>" + '</span>&nbsp;' +
    //                                 '</div>';
    //                     }
    //                 },
                    
    //                 load: function(query, callback){
    //                  console.log(query, query.length)
    //                     if(query.length < 3) return callback();
    //                     query = query.toUpperCase();
    //                     $.ajax({
    //                         url : "/api/ofd/search/" + query,
    //                         type : 'get',
    //                         context: this,
    //                         dataType : 'json',
    //                         success: function(data){
    //                             var arr = [];
    //                             $.each(data, function(index, value){
    //                                 arr.push({
    //                                     order_id: value.order_id,
    //                                     name: value.name,
    //                                     str_id: value.str_id
    //                                 })
    //                             })
    //                             console.log(arr)
    //                             callback(arr);
    //                         },
    //                         error: function(xhr, status, error){
    //                             callback();
    //                         }
    //                     });
    //                 },

    //                 onItemAdd: function(value, item){
    //                     console.log(value, item)
    //                     var selectize = this.$input[0].selectize;
    //                 },
    //             })
            },

            ".click-to-assign click": function(element, event){
                var ofd_self = this;
                var order_id = element.parents('tr').attr('index');
                var arr_id = null;
                ofd_self.scope.orderData.each(function(order, key){
                    if(order.attr(order_id)) arr_id = key;
                })
                var select = $('<select type="text" placeholder="Select staff">');
                $(element).parents('td').append(select);
                $(element).hide();
                var selectize_employee = $(select).selectize({
                    plugins : ['remove_button'],
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
                                var assigned_to = ofd_self.scope.orderData.attr(arr_id).attr(order_id + ".assigned_to");
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
                        url: "/api/delivery",
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
                            var order = ofd_self.scope.orderData.attr(arr_id).attr(order_id);
                            if(!order.attr("assigned_to"))
                                order.attr("assigned_to", {})
                            order.attr("assigned_to").attr("name", value['name']);
                            order.attr("assigned_to").attr("str_id", value['str_id']);
                            order.attr("status", ofd_self.scope.getStatusDetails('delivery_progress').formal_name);
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

            "#delivery-orders click": function(element, event){
                var arr = $("#delivery-orders .click-to-assign + .selectized");
                if (!arr.length) return false;
                arr.each(function(index, value){
                    if(!($(value).parents('tr').attr('index') == $(event.target).parents('tr').attr('index'))){
                        var selectize = $(value).selectize()
                        selectize = selectize[0].selectize;
                        selectize.destroy();
                        $(value).siblings('a').show();
                        $(value).remove();
                    }
                })
            }
        }
    })
})