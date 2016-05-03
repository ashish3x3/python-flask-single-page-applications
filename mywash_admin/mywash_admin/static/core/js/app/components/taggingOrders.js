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
    'jqprint',
    'selectize',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'tagging-tabs',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                var tagging_self = this;
                this.order_status = new can.Map({});
                this.timeslots = new can.Map({})
                this.total_quantity = can.compute(0);
                this.row_count = can.compute(0);
                
                this.nanobar = new Nanobar({
                    id: 'mybar',
                    bg: "#FF6600"
                })
                
                this.statuses = JSON.parse(localStorage.getItem("statuses"));
                this.order_status.attr(this.statuses, true);
                
                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                this.timeslots.attr(timeslots_temp, true);
            },

            tabchange: function(context, element, event){
                event.preventDefault();
                var newValue = $(element).find('input').attr('href').substr(1);
                var elements = $('input[href="#' + newValue + '"]').parents('.btn-group').find('input');
                elements.each(function(){
                    var href = $(this).attr('href').substr(1);
                    if (href === newValue) {
                        if (newValue == "tagging-pane-bundles"){
                            $("#tagging-btn-add-bundle").show();
                            $("#tagging-btn-print-tags").hide();
                        }else{
                            $("#tagging-btn-add-bundle").hide();
                            $("#tagging-btn-print-tags").show();
                        }
                        $(this).parent().addClass("active");
                        $("#" + href).show();
                    }else{
                        $("#" + href).hide();
                        $(this).parent().removeClass("active");
                    }
                });
            },

            // this context for setInterval()
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
            tags: new can.List([]),
            selectize: {},

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

            getTotalQuantity: function(){
                return this.total_quantity();
            },

            
            orderRefresh: function(context, element, event) {
                var current_date = moment(this.orderDate());
                this._pollData('order', current_date, false, true);
            },

            taggingPrevday: function(context, element, event){
                var date = moment(this.attr('variableDate'));
                date.subtract(1, 'days');
                this.attr('variableDate', date.toDate());
                this._pollData('order', this.orderDate());
            },

            pickupTimeSlotChange: function(context, element, event){
                var order_id = $("#tagging-order-details-modal").attr("index");
                var index = $(element).val();
                var value = this.timeslots.attr(index);
                this.modalCustomerDetails.attr("data.schedules.pickup.schedule", value);
                $.ajax({
                    url: "/api/pickup",
                    type: 'put',
                    dataType: "json",
                    data: {
                        order_id: order_id,
                        time: value
                    },
                    success: function(data){
                        toastr.success("Timeslot changed.")
                    },
                    error: function(xhr, status, error){
                        toastr.error("Timeslot change error.")
                    }
                })
            },

            deliveryTimeSlotChange: function(context, element, event){
                var order_id = $("#tagging-order-details-modal").attr("index");
                var index = $(element).val();
                var value = this.timeslots.attr(index);
                this.modalCustomerDetails.attr("data.schedules.pickup.schedule", value);
                $.ajax({
                    url: "/api/delivery",
                    type: 'put',
                    dataType: "json",
                    data: {
                        order_id: order_id,
                        time: value
                    },
                    success: function(data){
                        toastr.success("Timeslot changed.")
                    },
                    error: function(xhr, status, error){
                        toastr.error("Timeslot change error.")
                    }
                })
            },

            taggingNextday: function(context, element, event){
                var date = moment(this.attr('variableDate'));
                date.add(1, 'days');
                this.attr('variableDate', date.toDate());
                this._pollData('order', this.orderDate());
            },

            getOrderDataKey: function(order_id){
                var arr_id;
                this.orderData.each(function(order, key){
                    if(order.attr(order_id)) arr_id = key;
                })
                return arr_id;
            },

            _addData: function(list, pickup_type){
                this.row_count(list.length);
                var map_keys = can.Map.keys(this.orderData);
                var tagging_self = this;
                var data = {}
                // Put the new values into the map.
                $.each(list, function(index, value){
                    var status_details = tagging_self.getStatusDetails(value['status']);
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
                var tagging_self = this;
                var temp = {};
                $.each(list, function(index, value){
                    temp[value['order_id']] = value['schedule_time'];
                    
                    var schedule_time = tagging_self.orderData.attr(value['schedule_time']);
                    if (!schedule_time)
                        tagging_self.orderData.attr(value['schedule_time'], {});
                    if(!schedule_time.attr(value['order_id'])){
                        var status_details = tagging_self.getStatusDetails(value['status']);
                        value['status'] = status_details.formal_name;
                        value['status_color'] = status_details.color;
                        value['user_info']['name'] = value['user_info']['name'].trim();
                        schedule_time.attr(value['order_id'], value);
                    }
                    // else{
                    //     var order = schedule_time.attr(value['order_id']);
                    //     if(!order.attr('status') != value['status']){
                    //         order.attr('status', value['status']);
                    //     }

                    //     if(!order.attr('total_quantity') != value['total_quantity']){
                    //         order.attr('total_quantity', value['total_quantity']);
                    //     }

                    //     order.attr('bag', value['bag']);
                    // }
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
                    tagging_self.orderData.attr(key).removeAttr(value);
                })
            },

            _pollData: function(pickup_type, date, time, refresh){
                var tagging_self = this;
                if(date) date = this.getFormattedDate(moment(date));
                if(time) time = this.getFormattedTime(moment(time));
                if(!refresh) refresh = false;
                var pollUrl = "";
                if(time){
                    pollUrl = "/api/tagging/" + pickup_type + "/" + date + "/" + time;
                }else{
                    pollUrl = "/api/tagging/" + pickup_type + "/" + date;
                }
                this.nanobar.go(30);
                
                var tagging_defer = $.ajax({
                    url: pollUrl,
                    type: 'get',
                    dataType: 'json',
                });

                var bundle_defer = $.ajax({
                    url: "/api/bundles/" + date,
                    type: 'get',
                    dataType: 'json',
                })

                $.when(tagging_defer, bundle_defer).done(function(tagging_data, bundle_data){
                    tagging_data = tagging_data[0].data;
                    bundle_data = bundle_data[0].data;
                    tagging_self.nanobar.go(50);
                    if (refresh) {
                        // Update the bundle data
                        $.each(bundle_data, function(index, value){
                            if (!tagging_self.allBundles.attr(index)) {
                                tagging_self.allBundles.attr(index, {
                                    'name': value['name'],
                                    'date': value['date'],
                                    'contents': value['contents'],
                                    'vendor': value['vendor'],
                                    'total_quantity': value['total_quantity'],
                                })
                            }else{
                                if (tagging_self.allBundles.attr(index).attr('name') != value['name'])
                                    tagging_self.allBundles.attr(index).attr('name', value['name'])
                                if (tagging_self.allBundles.attr(index).attr('total_quantity') != value['total_quantity'])
                                    tagging_self.allBundles.attr(index).attr('total_quantity', value['total_quantity'])
                                if (tagging_self.allBundles.attr(index).attr('contents') != value['contents'])
                                    tagging_self.allBundles.attr(index).attr('contents', value['contents'])
                                if (tagging_self.allBundles.attr(index).attr('date') != value['date'])
                                    tagging_self.allBundles.attr(index).attr('date', value['date'])
                                if (tagging_self.allBundles.attr(index).attr('vendor') != value['vendor'])
                                    tagging_self.allBundles.attr(index).attr('vendor', value['vendor'])
                                var update_bag = false;
                                tagging_self.allBundles.attr(index).attr('bags').each(function(bag, bag_index){
                                    if (value['bags'].indexOf(bag) == -1)
                                        update_bag = true;
                                })
                                if (update_bag)
                                    tagging_self.allBundles.attr(index).attr('bags', value['bags'])
                            }
                            
                        })
                    }else{
                        tagging_self.allBundles.attr(bundle_data, true);
                    }

                    if (tagging_data){
                        if (refresh) {
                            tagging_self._updateData(tagging_data);
                        } else {
                            tagging_self._addData(tagging_data);
                        }
                    }
                    tagging_self.nanobar.go(100);
                })
                
                
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

                    var service_type = this.modalCustomerDetails.attr('data.service_type');
                    
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
                    if (service_type == 'express') {
                        item.attr('final_cost', (laundry + dryclean + iron)*2);
                    } else {
                        item.attr('final_cost', laundry + dryclean + iron);
                    }
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

                item_defer.done(function(data){
                    var tagging_self = this;
                    this.nanobar.go(50);
                    this.cleaningItems.replace(data.data);
                    data.customer_details['status'] = this.getStatusDetails(data.customer_details['status']).attr('name_id')
                    this.modalCustomerDetails.attr('data', data.customer_details);

                    if(this.modalCustomerDetails.attr('data.bag.laundry')){
                        this.modalCustomerDetails.attr('data.bag.laundry').each(function(value, index){
                            tagging_self.selectize['laundry'].addOption({
                                value: value,
                                text: value
                            });
                            tagging_self.selectize['laundry'].addItem(value, true);
                        })
                    }
                    
                    
                    if (this.modalCustomerDetails.attr('data.bag.dryclean')) {
                        this.modalCustomerDetails.attr('data.bag.dryclean').each(function(value, index){
                            tagging_self.selectize['dryclean'].addOption({
                                value: value,
                                text: value
                            });
                            tagging_self.selectize['dryclean'].addItem(value, true);
                        })
                    };
                    
                    if (this.modalCustomerDetails.attr('data.bag.iron')) {
                        this.modalCustomerDetails.attr('data.bag.iron').each(function(value, index){
                            tagging_self.selectize['iron'].addOption({
                                value: value,
                                text: value
                            });
                            tagging_self.selectize['iron'].addItem(value, true);
                        })
                    };

                    $("#tagging-order-details-modal").attr('index', index);
                    var summernote = $("#tagging-order-details-modal .summernote");
                    summernote.html(this.modalCustomerDetails.attr('data.remark'));
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
                            tagging_self.modalCustomerDetails.attr('data.remark', $("#tagging-order-details-modal .summernote").code());
                        }
                    });

                    $("#tagging-order-details-modal").modal({
                        backdrop: 'static',
                        keyboard: false,
                        show: true
                    });
                    this.nanobar.go(100);
                    $("#tagging-order-details-modal table").focus();
                    this._update_total_cost();
                    this._update_total_quantity();
                })

            },

            _get_sub_total_cost: function(){
                var total_cost = 0;
                var service_type = this.modalCustomerDetails.attr('data.service_type');
                this.cleaningItems.each(function(element, index){
                    var item = element, laundry, dryclean, iron;
                    laundry = (item.attr('quantity.laundry') * item.attr('price.laundry')) || 0;
                    dryclean = (item.attr('quantity.dryclean') * item.attr('price.dry_cleaning')) || 0;
                    iron = (item.attr('quantity.iron') * item.attr('price.iron')) || 0;
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

                this.allCosts.attr('total_cost', Math.round(total_cost));
            },

            changeMaxDiscount: function(context, element, event){
                var max_discount_amount = $('#tagging-order-details-modal .modal-discount-max-amount').val() || 0;
                this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
                this._update_total_cost();
            },

            changeDiscount: function(context, element, event){
                var discount_type = $('#tagging-order-details-modal .modal-discount-type li.active');
                this.applyDiscount(context, discount_type, event);
            },

            changePaymentStatus: function(context, element, event){
                var new_value = $(element).val();
                var order_id = $("#tagging-order-details-modal").attr('index');
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
                var discount_amount = $('#tagging-order-details-modal .modal-discount-amount').val() || 0;

                if (is_percentage) {
                    this.modalCustomerDetails.attr("data.discount.percentage", true);
                }else{
                    this.modalCustomerDetails.attr("data.discount.percentage", false);
                }
                this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
                this._update_total_cost();
            },

            saveOrderChanges: function(context, element, event){
                var index = $("#tagging-order-details-modal").attr('index');
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
                        is_paid: this.modalCustomerDetails.attr("data.is_paid") || false,
                        credits_left: this.modalCustomerDetails.attr("data.credits.available")
                    },
                    success: function(data){
                        toastr.success("Saved successfully.");
                        var arr_id = this.getOrderDataKey(index);
                        var order = this.orderData.attr(arr_id).attr(index)
                        order.attr('total_quantity', this.total_quantity());
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
                var order_id = $("#tagging-order-details-modal").attr('index');
                $.ajax({
                    url: "/api/order/" + order_id,
                    type: "put",
                    dataType: 'json',
                    context: this,
                    data:{
                        status: new_value,
                    },
                    success: function(data){
                        this.modalCustomerDetails.attr("data.status", new_value);
                        toastr.success("Status change successful.")
                        var arr_id = this.getOrderDataKey(order_id);
                        var order = this.orderData.attr(arr_id).removeAttr(order_id);
                        // order.attr('total_quantity', this.total_quantity());
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
                $("#tagging-order-details-modal .summernote").destroy();
                // this.orderRefresh();
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

            openTagsModal: function(context, element, event){
                var rows = $(".tagging-checkbox.btn-success").parents("tr");
                var order_ids = []
                $.each(rows, function(index, value){
                    order_ids.push($(value).attr('index'));
                })

                if (!order_ids.length) {
                    toastr.warning("Select an order first.")
                    return false;
                };

                this.nanobar.go(30);

                $.ajax({
                    url: "/api/tags/" + JSON.stringify(order_ids),
                    type: 'get',
                    context: this,
                    dataType: 'json',
                    success: function(data){
                        this.nanobar.go(50);
                        // Do processing here
                        $.each(data.data, function(index, order){
                            order['laundryTags'] = [];
                            order['drycleanTags'] = [];
                            order['ironTags'] = [];
                            order['totalQuantity'] = order['dryclean']['quantity'] + order['laundry']['quantity'] + order['iron']['quantity']

                            for(var i = 0; i < order.laundry.quantity; i++){
                                var item = {}
                                item['name'] = order['name'];
                                item['phone'] = order['phone'];
                                item['bag'] = order['laundry']['bag'];
                                item['quantity'] = order['laundry']['quantity'];
                                item['pickup_date'] = moment(order['pickup_date']).format("DD-MM-YYYY");
                                item['delivery_date'] = moment(order['delivery_date']).format("DD-MM-YYYY");
                                item['pickup_time'] = order['pickup_time'];
                                item['delivery_time'] = order['delivery_time'];
                                order['laundryTags'].push(item);
                            }
                            
                            for(var i = 0; i < order.dryclean.quantity; i++){
                                var item = {}
                                item['name'] = order['name'];
                                item['phone'] = order['phone'];
                                item['bag'] = order['dryclean']['bag'];
                                item['quantity'] = order['dryclean']['quantity'];
                                item['pickup_date'] = moment(order['pickup_date']).format("DD-MM-YYYY");
                                item['delivery_date'] = moment(order['delivery_date']).format("DD-MM-YYYY");
                                item['pickup_time'] = order['pickup_time'];
                                item['delivery_time'] = order['delivery_time'];
                                order['drycleanTags'].push(item);
                            }
                            
                            for(var i = 0; i < order.iron.quantity; i++){
                                var item = {}
                                item['name'] = order['name'];
                                item['phone'] = order['phone'];
                                item['bag'] = order['iron']['bag'];
                                item['quantity'] = order['iron']['quantity'];
                                item['pickup_date'] = moment(order['pickup_date']).format("DD-MM-YYYY");
                                item['delivery_date'] = moment(order['delivery_date']).format("DD-MM-YYYY");
                                item['pickup_time'] = order['pickup_time'];
                                item['delivery_time'] = order['delivery_time'];
                                order['ironTags'].push(item);
                            }
                        })
                        this.tags.replace(data.data);
                        $("tagging-tabs .tags-print").modal('show')
                        this.nanobar.go(100);
                    },
                    error: function(xhr, status, error){

                    }
                })
                
            },

            printTags: function(context, element, event){
                $(element).parents(".modal-content").find(".modal-body").print();
            },










            /////////////////////// BUNDLES METHODS ///////////////////////////////

            allBundles: new can.Map({}),
            selectedBundle: new can.Map({}),

            openAddBundleModal: function(context, element, event){
                this.selectedBundle.attr('name', (can.Map.keys(this.allBundles).length + 1));
                this.selectedBundle.attr('date', moment(this.orderDate()).format("YYYY-MM-DD"));
                $("#tagging-bundles-modal").modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                })
            },

            bundleEditChange: function(context, element, event){
                if (element.attr('name') == 'name')
                    this.selectedBundle.attr('name', $(element).val().trim())
                
                if (element.attr('name') == 'date')
                    this.selectedBundle.attr('name', $(element).val().trim())
                
            },

            editBundleModal: function(context, element, event){
                var bundle_id = $(element).parents("tr").attr('index');
                $.ajax({
                    url: "/api/bundle/" + bundle_id,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                    success: function(data){
                        var tagging_self = this;
                        var bags = [];
                        this.selectedBundle.attr(data, true);
                        $.each(data.bags, function(index, value){
                            bags.push(value['bag'])
                            tagging_self.selectize['bundle'].addOption(value);
                            tagging_self.selectize['bundle'].addItem(value['bag']);
                        })
                        this.selectize['vendor'].addOption({
                            id: data.vendor.id,
                            name: data.vendor.name
                        });
                        this.selectize['vendor'].addItem(data.vendor.id);
                        this.selectedBundle.attr('bags', bags);
                        this.selectedBundle.attr('str_id', bundle_id);
                        $("#tagging-bundles-modal").modal({
                            backdrop: 'static',
                            keyboard: false,
                            show: true
                        })
                    },
                    error: function(){
                        toastr.danger("Try again later.")
                    }
                })
            },

            closeBundleModal: function(context, element, event){
                this.selectize['bundle'].clearOptions();
                this.selectize['bundle'].clear();
                this.selectize['vendor'].clear();
                this.selectedBundle.attr({}, true);
            },

            saveBundle: function(context, element, event){
                var type = 'post';
                var url = "/api/bundle"
                var name = this.selectedBundle.attr('name');
                if (typeof name == 'number')
                    name = name.toString();
                if (!name) {
                    toastr.error("Please give a name to the bundle.")
                    return false;
                };

                var bags = [];
                if(this.selectedBundle.attr('bags')){
                    bags = this.selectedBundle.attr('bags').attr();
                }
                var str_id = this.selectedBundle.attr('str_id') || null;
                if (str_id){
                    type = 'put';
                    url = "/api/bundle/" + this.selectedBundle.attr('str_id')
                }
                $.ajax({
                    url: url,
                    type: type,
                    context: this,
                    dataType: 'json',
                    data: {
                        name: name,
                        date: this.selectedBundle.attr('date'),
                        vendor: this.selectedBundle.attr('vendor') || null,
                        bags: JSON.stringify(bags)
                    },
                    success: function(data){
                        this.selectedBundle.attr({}, true);
                        if (str_id){
                            this.allBundles.attr(str_id).attr('bags', bags)
                        }
                        $("#tagging-bundles-modal").modal("hide")
                        this.closeBundleModal();
                        $("#tagging-orders .fa-refresh").parent().trigger('click');
                    }
                })
            }

        }),

        helpers: $.extend(BaseHelpers, {
            multiply: function(a, b, options){
                return a() * b();
            },

            timeslotBackColor: function(hour, date, option){
                var today = moment(), date = moment(date());
                if(today.format("YYYY-MM-DD") != date.format("YYYY-MM-DD")) 
                    return "#FFF5A3";
                if (hour < today.hours()) return "#ff6c60";
                else if((hour - today.hours()) < 2 ) return "#FF8134";
                else return "#FFF5A3";
            }
        }),

        events: {
            '{can.route} sidebarmenu': function(route){
                var now = moment();
                if (route.sidebarmenu == "main-content-tagging" && !this.scope.loaded) {
                    var now = moment();
                    this.scope._pollData('order', now);
                    setInterval(this.scope.intervalFunc.bind(this.scope), 5*60*1000)

                    this.scope.loaded = true;
                };
            },

            '#tagging-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },

            'inserted': function(){
                var tagging_self = this;
                var options = {
                    format: "yyyy-mm-dd",
                    startdate: "2014-10-22",
                    autoclose: true,
                    todayBtn: true
                }
                $("tagging-tabs .order-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    var order_id = $("#tagging-order-details-modal").attr("index");
                    var formatted_value = selectedDate.format("YYYY/MM/DD");
                    tagging_self.scope._pollData('order', selectedDate);
                    tagging_self.scope.attr('variableDate', selectedDate.toDate());
                })
                
                $("#tagging-order-details-modal .modal-pickup-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    var order_id = $("#tagging-order-details-modal").attr("index");
                    var formatted_value = selectedDate.format("YYYY/MM/DD");
                    $.ajax({
                        url: "/api/pickup",
                        type: "put",
                        dataType: 'json',
                        context: tagging_self,
                        data: {
                            order_id: order_id,
                            date: formatted_value
                        },
                        success: function(data){
                            toastr.success("Date changed.")
                            tagging_self.scope.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", formatted_value)
                        },
                        error: function(xhr, status, error){
                            toastr.error("Date change error.")
                        }
                    })
                    
                    tagging_self.scope.modalCustomerDetails.attr("data.schedules.pickup.schedule_date", selectedDate.format("YYYY/MM/DD"))
                })

                $("#tagging-order-details-modal .modal-delivery-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    var order_id = $("#tagging-order-details-modal").attr("index");
                    var formatted_value = selectedDate.format("YYYY/MM/DD");
                    $.ajax({
                        url: "/api/delivery",
                        type: "put",
                        dataType: 'json',
                        context: self,
                        data: {
                            order_id: order_id,
                            date: formatted_value
                        },
                        success: function(data){
                            toastr.success("Date changed.")
                            self.scope.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", formatted_value)
                        },
                        error: function(xhr, status, error){
                            toastr.error("Date change error.")
                        }
                    })
                })

                // Add datepicker to bundle modal
                $("#tagging-bundles-modal .add-bundle-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    tagging_self.scope.selectedBundle.attr('order_date', selectedDate);
                })

                // Add selectize to bundle modal
                var addBagSelectize = $("#tagging-bundles-modal .add-bags-input").selectize({
                    plugins : ['remove_button'],
                    valueField: 'bag',
                    labelField: 'name',
                    searchField: 'bag',
                    create: false,

                    render: {
                        item : function(item, escape){
                            return '<div style="color:#fff">' + 
                                        '<span>' + escape(item.name) + '</span>&nbsp;' +
                                        '(<span class="bold">' + escape(item.bag) + '</span>)' +
                                    '</div>';
                        },
                        option: function(item, escape) {
                            return '<div>' + 
                                        '<span>' + escape(item.name) + '</span>&nbsp;' +
                                        '(<span class="bold">' + escape(item.bag) + '</span>)' +
                                    '</div>';
                        }
                    },
                    
                    load: function(query, callback){
                        if(!query.length) return callback();
                        query = query.toUpperCase();
                        $.ajax({
                            url : "/api/tagbags/" + moment(tagging_self.scope.orderDate()).format("YYYY-MM-DD") + "/" + query,
                            type : 'get',
                            dataType : 'json',
                            success: function(data){
                                callback(data.data);
                            },
                            error: function(xhr, status, error){
                                callback();
                            }
                        });
                    },

                    onItemAdd: function(value, item){
                        if(!tagging_self.scope.selectedBundle.attr('bags'))
                            tagging_self.scope.selectedBundle.attr('bags', [])
                        if (tagging_self.scope.selectedBundle.attr('bags').indexOf(value) == -1)
                            tagging_self.scope.selectedBundle.attr('bags').push(value)

                    },

                    onItemRemove: function(value){
                        var index = tagging_self.scope.selectedBundle.attr('bags').indexOf(value);
                        tagging_self.scope.selectedBundle.attr('bags').removeAttr(index)
                        // tagging_self.scope.selectedBundle.attr('bags').removeAttr(4)
                        //console.log(tagging_self.scope.selectedBundle.attr(), index)
                    }
                })
                
                var selectize_laundry = $('#tagging-modal-edit .bag-laundry').selectize({
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
                        var item = tagging_self.scope.modalCustomerDetails.attr('data');
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
                        var item = tagging_self.scope.modalCustomerDetails.attr('data.bag').attr("laundry");
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
                            url: "/api/order/" + tagging_self.scope.modalCustomerDetails.attr('data._id'),
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
                                var index = tagging_self.scope.modalCustomerDetails.attr('data._id');
                                var arr_id = tagging_self.scope.getOrderDataKey(index);
                                var order = tagging_self.scope.orderData.attr(arr_id).attr(index)
                                
                                if (action == 'add') {
                                    if (!order.attr('bag.laundry')) {
                                        order.attr('bag.laundry', []);
                                    };
                                    order.attr('bag.laundry').push(alter_bags[0]);
                                } else {
                                    order.attr('bag.laundry').removeAttr(
                                        order.attr('bag.laundry').indexOf(alter_bags[0])
                                    );
                                }
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })

                        this.addEvent = false;
                        this.removeEvent = false;
                    }

                });

                var selectize_dryclean = $('#tagging-modal-edit .bag-dryclean').selectize({
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
                        var item = tagging_self.scope.modalCustomerDetails.attr('data');
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
                        var item = tagging_self.scope.modalCustomerDetails.attr('data.bag').attr("dryclean");
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
                            url: "/api/order/" + tagging_self.scope.modalCustomerDetails.attr('data._id'),
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
                                var index = tagging_self.scope.modalCustomerDetails.attr('data._id');
                                var arr_id = tagging_self.scope.getOrderDataKey(index);
                                var order = tagging_self.scope.orderData.attr(arr_id).attr(index)
                                
                                if (action == 'add') {
                                    if (!order.attr('bag.dryclean')) {
                                        order.attr('bag.dryclean', []);
                                    };
                                    order.attr('bag.dryclean').push(alter_bags[0]);
                                } else {
                                    order.attr('bag.dryclean').removeAttr(
                                        order.attr('bag.dryclean').indexOf(alter_bags[0])
                                    );
                                }
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })

                        this.addEvent = false;
                        this.removeEvent = false;
                    }

                });
                
                var selectize_iron = $('#tagging-modal-edit .bag-iron').selectize({
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
                        var item = tagging_self.scope.modalCustomerDetails.attr('data');
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
                        var item = tagging_self.scope.modalCustomerDetails.attr('data.bag').attr("iron");
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
                            url: "/api/order/" + tagging_self.scope.modalCustomerDetails.attr('data._id'),
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
                                var index = tagging_self.scope.modalCustomerDetails.attr('data._id');
                                var arr_id = tagging_self.scope.getOrderDataKey(index);
                                var order = tagging_self.scope.orderData.attr(arr_id).attr(index)
                                
                                if (action == 'add') {
                                    if (!order.attr('bag.iron')) {
                                        order.attr('bag.iron', []);
                                    };
                                    order.attr('bag.iron').push(alter_bags[0]);
                                } else {
                                    order.attr('bag.iron').removeAttr(
                                        order.attr('bag.iron').indexOf(alter_bags[0])
                                    );
                                }
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })

                        this.addEvent = false;
                        this.removeEvent = false;
                    }
                });

                // Add selectize to bundle modal
                var selectize_vendor = $("#tagging-bundles-modal .add-vendor-input").selectize({
                    plugins : ['remove_button'],
                    valueField: 'id',
                    labelField: 'name',
                    searchField: 'name',
                    create: false,
                    preload: true,

                    render: {
                        item : function(item, escape){
                            return '<div>' + 
                                        '<span>' + escape(item.name) + '</span>&nbsp;' +
                                    '</div>';
                        },
                        option: function(item, escape) {
                            return '<div>' + 
                                        '<span>' + escape(item.name) + '</span>&nbsp;' +
                                    '</div>';
                        }
                    },
                    
                    load: function(query, callback){
                        $.ajax({
                            url : "/api/vendor/search",
                            type : 'get',
                            dataType : 'json',
                            success: function(data){
                                callback(data);
                            },
                            error: function(xhr, status, error){
                                callback();
                            }
                        });
                    },

                    onItemAdd: function(value, item){
                        tagging_self.scope.selectedBundle.attr('vendor', value);
                    },

                    onItemRemove: function(value){
                        tagging_self.scope.selectedBundle.removeAttr('vendor', value);
                    }
                })
                

                tagging_self.scope.selectize = {
                    'laundry': selectize_laundry[0].selectize,
                    'dryclean': selectize_dryclean[0].selectize,
                    'iron': selectize_iron[0].selectize,
                    'vendor': selectize_vendor[0].selectize,
                    'bundle': addBagSelectize[0].selectize
                }
            }
        }
    })
})