define([
    'jquery',
    'can',
    '../../lib/mywash/constructs/map.helpers',
    '../../lib/mywash/components/tabs',
    'toastr',
    'nanobar',
    'gmaps',
    'datepicker',
    'momentjs',
    'selectize',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar, gmaps){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'users-tab',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                var user_self = this;
                var now = moment();
                this.poll_skip = 0;
                this.poll_limit = 20;
                this.last_action = null;
                this.user_count = can.compute(0);
                this.timeslots = new can.Map({});
                this.order_status = new can.Map({});

                this.search_skip = 0;
                this.search_limit = 20;

                this.nanobar = new Nanobar({
                    id: 'mybar',
                    bg: "#FF6600"
                })

                var statuses = JSON.parse(localStorage.getItem("statuses"));
                $.each(statuses, function(index, value){
                    user_self.order_status.attr(index, value);
                })
                

                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                $.each(timeslots_temp, function(index, value){
                    user_self.timeslots.attr(index, value);
                })
            },

            userData: new can.List([]),
            loaded: false,

            cleaningItems: new can.List([]),
            modalCustomerDetails: new can.Map({}),
            allCosts: new can.Map({}),
            selectedUser: new can.Map({}),

            orderHistory: new can.List([]),
            newOrder: new can.Map({}),
            addressList: new can.List([]),
            selectedAddress: new can.Map({}),

            variableDate: new Date(),
            orderDate: can.compute(function(){
                return this.attr('variableDate');
            }),

            selectize: null,

            getFormattedDate: function(date){
                return date.format("YYYY-MM-DD");
            },

            getFormattedTime: function(date){
                return date.format("HH-mm");
            },

            getUserCount: function(){
                return this.user_count();
            },

            getTimeSlots: function(){
                return this.timeslots;
            },

            selectSearchOption: function(context, element, event) {
                var input = $(element).parents(".input-group").find(".search-input");
                var type = $(element).attr('data-option');
                if (type == "name") input.val("name:");
                else if (type == "email") input.val("email:");
                else if (type == "phone") input.val("phone:");
                input.focus();
            },

            captureEnterKey: function(context, element, event) {
                if (event.keyCode == 13) $("#users .btn-search-go").trigger('click');
            },

            searchUsers: function(context, element, event) {
                this._searchUsers(0, this.search_limit);
                this._searchUsersDeferred();
            },

            addUser: function(context, element, event) {
                $("#user-data-modal").modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                });
            },

            closeUserAddModal: function(context, element, event) {
                $("#user-data-modal").modal('hide');
                this.selectedUser.attr({}, true);
            },

            closeUserEditModal: function(context, element, event) {
                $("#user-data-edit-modal").modal('hide');
                this.selectedUser.attr({}, true);
            },

            
            editUser: function(context, element, event) {
                var user_id = $(element).parents("tr").attr("index");
                var array_index = parseInt($(element).parents("tr").attr("array-index"));
                this.selectedUser.attr('user_id', user_id);
                this.selectedUser.attr('array_index', array_index);

                this.nanobar.go(30);
                var user_defer = $.ajax({
                    url: "/api/user/" + user_id,
                    type: 'get',
                    dataType: 'json',
                });

                var address_defer = $.ajax({
                    url: "/api/address/user/" + user_id,
                    type: 'get',
                    dataType: 'json',
                })

                var orderhistory_defer = $.ajax({
                    url: "/api/orderhistory/" + user_id,
                    type: 'get',
                    dataType: 'json',
                })

                var user_self = this;  
                
                $.when(user_defer, address_defer, orderhistory_defer).done(
                function(user_data, address_data, order_data){
                    user_data = user_data[0];
                    address_data = address_data[0];
                    order_data = order_data[0];

                    user_self.nanobar.go(50);
                    user_self.selectedUser.attr('name', user_data.data.users[0].user_data.name);
                    user_self.selectedUser.attr('phone', user_data.data.users[0].user_data.phone);
                    user_self.selectedUser.attr('email', user_data.data.users[0].user_data.email);
                    user_self.selectedUser.attr('credits', parseInt(user_data.data.users[0].user_data.credits) || 0);
                    
                    user_self.selectedUser.attr('backup_credits', parseInt(user_data.data.users[0].user_data.credits) || 0);
                    user_self.selectedUser.attr('backup_credits_add', 0);
                    user_self.selectedUser.attr('backup_credits_deduct', 0);
                    
                    user_self.newOrder.attr('phone', user_data.data.users[0].user_data.phone);
                    user_self.newOrder.attr('user_id', user_self.selectedUser.attr('user_id'));

                    user_self.addressList.replace(address_data.data)
                    $.each(order_data.data, function(key, value){
                        var status_details = user_self.getStatusDetails(value.status);
                        value['status'] = status_details.formal_name;
                        value['status_color'] = status_details.color;
                    })
                    user_self.orderHistory.replace(order_data.data);
                    $("#user-data-edit-modal").modal({
                        backdrop: 'static',
                        keyboard: false,
                        show: true
                    });
                    user_self.nanobar.go(100);
                }).fail(function(){
                    user_self.nanobar.go(100);
                    toastr.error("Some error occured. Try again.")
                })
            },
            
            saveUserDetails: function(context, element, event) {
                if (!this.__validateSelectedUserDetails()) return false;
                var credits = JSON.stringify({
                    'add': parseInt(this.selectedUser.attr('backup_credits_add')),
                    'deduct': parseInt(this.selectedUser.attr('backup_credits_deduct')),
                })
                var edit_user_defer = $.ajax({
                    url: "/api/user/" + this.selectedUser.user_id,
                    type: 'put',
                    dataType: 'json',
                    context: this,
                    data:{
                        name: this.selectedUser.attr('name'),
                        phone: this.selectedUser.attr('phone'),
                        credits: credits,
                        email: this.selectedUser.attr('email')
                    },
                    success: function(data){
                        toastr.success("User details successfully saved.")
                        // Change phone and name
                        var user_data = this.userData.attr(this.selectedUser.attr('array_index'));
                        user_data.attr('user_data.phone', this.selectedUser.attr('phone'))
                        user_data.attr('user_data.name', this.selectedUser.attr('name'))
                        user_data.attr('user_data.credits', this.selectedUser.attr('credits'))
                        user_data.attr('user_data.email', this.selectedUser.attr('email'))
                        this.closeUserEditModal();
                    },
                    error: function(xhr, status, error){
                        toastr.error("Error saving user details. Try again.")
                    }
                })
            },

            saveUser: function(context, element, event) {
                if (!this.__validateSelectedUser()) return false;
                var user_defer = $.ajax({
                    url: "/api/user",
                    type: 'post',
                    dataType: 'json',
                    context: this,
                    data: {
                        email: this.selectedUser.attr('email'),
                        name: this.selectedUser.attr('name'),
                        phone: this.selectedUser.attr('phone'),
                    },
                    success: function(data){
                        toastr.success("User successfully added.")
                        this.closeUserAddModal();
                    },
                    error: function(xhr, status, error){
                        toastr.error("Error adding user. Try again.")
                    }
                })
            },

            __validateSelectedUserDetails: function(){
                if(!this.selectedUser.attr('name')){
                    toastr.error("Name not provided.")
                    return false;
                }
                if(!this.selectedUser.attr('phone')){
                    toastr.error("Phone number not provided.")
                    return false;
                }else{
                    if (!this._validatePhone(this.selectedUser.attr('phone'))){
                        toastr.error("Phone number is incorrect.")
                        return false;
                    }
                }

                if(this.selectedUser.attr('email')){
                    if (!this._validateEmail(this.selectedUser.attr('email'))){
                        toastr.error("Email is incorrect.")
                        return false;
                    }
                }

                return true;
            },

            __validateSelectedUser: function(){
                if(!this.selectedUser.attr('name')){
                    toastr.error("Name not provided.")
                    return false;
                }
                if(!this.selectedUser.attr('phone')){
                    toastr.error("Phone number not provided.")
                    return false;
                }else{
                    if (!this._validatePhone(this.selectedUser.attr('phone'))){
                        toastr.error("Phone number is incorrect.")
                        return false;
                    }
                }
                
                if(!this.selectedUser.attr('email')){
                    toastr.error("Email not provided.")
                    return false;
                }else{
                    if (!this._validateEmail(this.selectedUser.attr('email'))){
                        toastr.error("Email is incorrect.")
                        return false;
                    }
                }

                return true;
            },

            __validateOrder: function(){
                if (!this.newOrder.attr('address_id')) {
                    toastr.error("Address not selected.")
                    return false;
                };
                if (!this.newOrder.attr('service')) {
                    toastr.error("Service not selected.")
                    return false;
                };
                if (!this.newOrder.attr('washtypes')) {
                    toastr.error("Service types not selected.")
                    return false;
                };
                if (!this.newOrder.attr('pickup_date_submit')) {
                    toastr.error("Pickup date not selected.")
                    return false;
                };
                if (!this.newOrder.attr('pickup_time')) {
                    toastr.error("Pickup time not selected.")
                    return false;
                };
                if (!this.newOrder.attr('schedule_date_submit')) {
                    toastr.error("Delivery date not selected.")
                    return false;
                };
                if (!this.newOrder.attr('schedule_time')) {
                    toastr.error("Delivery time not selected.")
                    return false;
                };
                if (!this.newOrder.attr('phone')) {
                    toastr.error("Phone number not provided.")
                    return false;
                };
                if (!this._validatePhone(this.newOrder.attr('phone'))) {
                    toastr.error("Phone number incorrect.")
                    return false;
                };
                return true;
            },

            orderFormChange: function(context, element, event){
                if($(element).attr('name') == "service"){
                    this.newOrder.attr("service", $(element).val());
                    if(this.newOrder.attr("service") == 'express'){
                        var delivery_datepicker = $('#add-order-form input[name="delivery-date"]');
                        var pickup_datepicker = $('#add-order-form input[name="pickup-date"]');
                        var selected_date =moment(pickup_datepicker.datepicker('getDate'));
                        selected_date = selected_date.add(1, "days");
                        delivery_datepicker.datepicker('setDate', selected_date.format("YYYY-MM-DD"));
                    } else {
                        var pickup_datepicker = $('#add-order-form input[name="pickup-date"]');
                        pickup_datepicker.datepicker('setDate', moment(
                            pickup_datepicker.datepicker('getDate')
                        ).format("YYYY-MM-DD"));
                    }
                } else if ($(element).attr('name') == "address") {
                    this.newOrder.attr("address_id", $(element).val());
                } else if ($(element).attr('name') == "pickup-time") {
                    this.newOrder.attr("pickup_time", $(element).val());
                } else if ($(element).attr('name') == "delivery-time") {
                    this.newOrder.attr("schedule_time", $(element).val());
                } else if ($(element).attr('name') == "phone") {
                    this.newOrder.attr("phone", $(element).val());
                } else if ($(element).attr('name') == "coupon") {
                    this.newOrder.attr("coupon", $(element).val());
                };
            },

            saveOrder: function(context, element, event) {
                if(!this.__validateOrder()) return false;
                $(element).button('loading');
                $.ajax({
                    url: "/api/order",
                    type: 'post',
                    dataType: 'json',
                    context: this,
                    data: this.newOrder.attr(),
                    success: function(data){
                        var user_self = this;
                        $(element).button('reset');
                        this.newOrder.attr('_id', data._id)
                        this.newOrder.attr('status', "order_placed")
                        this.newOrder.attr('pickup_data', {
                            'schedule_date': user_self.newOrder.attr('pickup_date_submit'),
                            'schedule_time': user_self.timeslots.attr(user_self.newOrder.attr('pickup_time')),
                        })

                        this.newOrder.attr('delivery_data', {
                            'schedule_date': user_self.newOrder.attr('schedule_date_submit'),
                            'schedule_time': user_self.timeslots.attr(user_self.newOrder.attr('schedule_time')),
                        })
                        this.orderHistory.unshift(this.newOrder.attr());
                        this.cancelOrder(context, element, event);
                        toastr.success("Order placed.")
                    },
                    error: function(xhr, error, status){
                        $(element).button('reset');
                        toastr.error(xhr.responseJSON['error'])
                    }
                })

            },

            cancelOrder: function(context, element, event){
                this.newOrder.attr({}, true);
                this.newOrder.attr('phone', this.selectedUser.attr('phone'));
                this.newOrder.attr('user_id', this.selectedUser.attr('user_id'));
                this.selectize['service'].clear();
                $('#add-order-form input[name="pickup-date"]').datepicker('setDate', moment().format("YYYY-MM-DD"));

                $("#add-order-form select").each(function(index, value){
                    $(value).find("option:first").attr('selected', 'selected');
                })
            },


            selectedUserChange: function(context, element, event) {
                var data = $(element).val().trim();
                if ($(element).attr('name') == "name") {
                    this.selectedUser.attr('name', data)
                } else if ($(element).attr('name') == "phone") {
                    this.selectedUser.attr('phone', data)
                } else if ($(element).attr('name') == "email") {
                    this.selectedUser.attr('email', data)
                } else if ($(element).attr('name') == "credits_add") {
                    this.selectedUser.attr('backup_credits_add', parseInt(data)||0);
                    var available_credits = this.selectedUser.attr('backup_credits');
                    var backup_add = this.selectedUser.attr('backup_credits_add');
                    var backup_deduct = this.selectedUser.attr('backup_credits_deduct');
                    var final_credit = available_credits + backup_add - backup_deduct
                    if (final_credit < 0) final_credit = 0;
                    this.selectedUser.attr('credits', final_credit)
                } else if ($(element).attr('name') == "credits_deduct") {
                    this.selectedUser.attr('backup_credits_deduct', parseInt(data)||0);
                    var available_credits = this.selectedUser.attr('backup_credits');
                    var backup_add = this.selectedUser.attr('backup_credits_add');
                    var backup_deduct = this.selectedUser.attr('backup_credits_deduct');
                    var final_credit = available_credits + backup_add - backup_deduct
                    if (final_credit < 0) final_credit = 0;
                    this.selectedUser.attr('credits', final_credit)
                }
            },

            selectedUserAddressChange: function(context, element, event){
                var data = $(element).val().trim();
                if ($(element).attr('name') == "address_1") {
                    this.selectedAddress.attr('address_1', data)
                } else if ($(element).attr('name') == "address_2") {
                    this.selectedAddress.attr('address_2', data)
                } else if ($(element).attr('name') == "apartment_number") {
                    this.selectedAddress.attr('apartment_number', data)
                } else if ($(element).attr('name') == "tag") {
                    this.selectedAddress.attr('tag', data)
                }
            },

            __validateAddress: function(){
                if(!this.selectedAddress.attr('tag')){
                    toastr.error("Tag not provided.")
                    return false;
                }
                if(!this.selectedAddress.attr('address_1')){
                    toastr.error("Address not provided.")
                    return false;
                }
                if(!this.selectedAddress.attr('address_2')){
                    toastr.error("Landmark not provided.")
                    return false;
                }
                if(!this.selectedAddress.attr('apartment_number')){
                    toastr.error("Flat number not provided.")
                    return false;
                }
                if(!this.selectedAddress.attr('locality')){
                    toastr.error("Locality not provided.")
                    return false;
                }
                return true;
            },

            saveAddress: function(context, element, event){
                if (!this.__validateAddress()) return false;
                var url = "/api/address", type = 'post';
                if (this.selectedAddress.attr('_id')) {
                    url += "/" + this.selectedAddress.attr('_id');
                    type = 'put';
                };
                $(element).button('loading');
                $.ajax({
                    url: url,
                    type: type,
                    dataType: 'json',
                    context: this,
                    data:{
                        tag: this.selectedAddress.attr('tag'),
                        address_1: this.selectedAddress.attr('address_1'),
                        address_2: this.selectedAddress.attr('address_2'),
                        apartment_number: this.selectedAddress.attr('apartment_number'),
                        user_id: this.selectedUser.attr('user_id') || null,
                        locality: JSON.stringify(this.selectedAddress.attr('locality').attr())
                    },
                    success: function(address_data){
                        $(element).button('reset');
                        this.selectedAddress.attr('assigned_hub', address_data.assigned_hub);
                        
                        if (this.selectedAddress.attr('_id')) {
                            var edit_object = this.addressList.attr(this.selectedAddress.attr('array_index'));
                            var data = edit_object.attr();
                            if (data.address_1 != this.selectedAddress.attr('address_1'))
                                edit_object.attr('address_1', this.selectedAddress.attr('address_1'));

                            if (data.apartment_number != this.selectedAddress.attr('apartment_number'))
                                edit_object.attr('apartment_number', this.selectedAddress.attr('apartment_number'));
                            
                            if (data.address_2 != this.selectedAddress.attr('address_2'))
                                edit_object.attr('address_2', this.selectedAddress.attr('address_2'));
                            
                            if (data.tag != this.selectedAddress.attr('tag'))
                                edit_object.attr('tag', this.selectedAddress.attr('tag'));

                            if (data.locality != this.selectedAddress.attr('locality'))
                                edit_object.attr('locality', this.selectedAddress.attr('locality'));

                            if (data.assigned_hub != this.selectedAddress.attr('assigned_hub'))
                                edit_object.attr('assigned_hub', this.selectedAddress.attr('assigned_hub'));
                            
                        }else{
                            this.selectedAddress.attr('_id', address_data.address_id);
                            this.addressList.unshift(this.selectedAddress.attr());
                        }
                        
                        this.selectedAddress.attr({}, true);
                    },
                    error: function(xhr, status, error){
                        // toastr.error(xhr.responseJSON.error)
                        $(element).button('reset');
                    }
                })
            },

            editAddress: function(context, element, event){
                this.nanobar.go(30);
                var array_index = parseInt($(element).attr('array-index'));
                $.ajax({
                    url: '/api/address/' + $(element).attr('index'),
                    type: 'get',
                    dataType: 'json',
                    context: this,
                    success: function(data){
                        data = data.data[0];
                        this.selectedAddress.attr({
                            _id: data['_id'],
                            tag: data['tag'],
                            address_1: data['address_1'],
                            address_2: data['address_2'],
                            apartment_number: data['apartment_number'],
                            locality: data['locality'] || null,
                            assigned_hub: data['assigned_hub'] || null,
                            array_index: array_index
                        }, true);
                        this.nanobar.go(50);
                        this.nanobar.go(100);
                    },
                    error: function(){
                        this.nanobar.go(100);
                    }
                })
            },

            cancelAddress: function(context, element, event){
                this.selectedAddress.attr({}, true);
            },

            _searchUsers: function(skip, limit) {
                var search_term = $.trim($("#users .search-input").val());
                if(search_term == ""){
                    $("#users .btn-refresh").trigger('click');
                    return;
                }
                skip = typeof skip == 'undefined'? this.search_skip : skip;
                limit = typeof limit == 'undefined'? this.search_limit : limit;
                this.nanobar.go(30);
                this.user_search_defer = $.ajax({
                    url: "/api/user/search/" + search_term + "/" + skip + "/" + limit,
                    type: 'get',
                    dataType: 'json',
                    context: this,
                })
            },

            _searchUsersDeferred: function(replace) {
                if (typeof replace == 'undefined') replace = true;

                this.user_search_defer.done(function(data){
                    var user_self = this;
                    this.nanobar.go(50);
                    if (replace)
                        this.userData.replace([]);
                    $.each(data.data.users, function(index, value){
                        user_self.userData.push(value);
                    })
                    this.search_skip += data.data.users.length;
                    this.nanobar.go(100);
                    this.last_action = "search"
                    if (!replace)
                        $("#users .block-load-more").find(".fa-repeat").removeClass("fa-spin");
                })

                this.user_search_defer.fail(function(xhr, status, error){
                    this.nanobar.go(100);
                    toastr.error("Proper search criteria not used.")
                })
            },


            userRefresh: function(context, element, event) {
                this._pollData(0, this.poll_skip);
                this._pollDataDeferExec(true);
            },

            loadMoreRows: function(context, element, event) {
                $(element).button('load');
                $(element).find(".fa-repeat").addClass("fa-spin");
                if (this.last_action == "search") {
                    this._searchUsers();
                    this._searchUsersDeferred(false);

                }else{
                    this._pollData();
                    this._pollDataDefer.done(function(data){
                        this.nanobar.go(50);
                        var user_self = this;
                        $.each(data.data.users, function(index, value){
                            user_self.userData.push(value);
                        })
                        this.poll_skip += data.data.users.length;
                        $(element).button('reset');
                        $(element).find(".fa-repeat").removeClass("fa-spin");
                        this.nanobar.go(100);
                    })
                }
                
            },

            _pollData: function(skip, limit){
                skip = typeof skip == 'undefined'? this.poll_skip : skip;
                limit = typeof limit == 'undefined'? this.poll_limit : limit;
                this.nanobar.go(30);
                this._pollDataDefer = $.ajax({
                    url: "/api/user/" + skip + "/" + limit,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                });
            },

            // Success part for _pollData ajax call
            _pollDataDeferExec: function(replace){
                if (typeof replace == 'undefined') replace = false;
                this._pollDataDefer.done(function(data){
                    var user_self = this;
                    this.nanobar.go(50);
                    if (!data.data){
                        user_self.nanobar.go(100);
                        return false;
                    }
                    if (!replace){
                        $.each(data.data.users, function(index, value){
                            user_self.userData.push(value);
                        })
                        this.poll_skip = this.poll_skip + data.data.users.length;
                    }
                    else{
                        this.userData.replace(data.data.users);
                        this.poll_skip = data.data.users.length;
                    }


                    this.user_count(data.data.total_count);
                    this.nanobar.go(100);
                    this.last_action = "query"
                })
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
            }

        }),

        helpers: $.extend(BaseHelpers, {
            multiply: function(a, b, options){
                return a() * b();
            },

        }),

        events: {
            '{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-users" && !this.scope.loaded) {
                    this.scope._pollData();
                    this.scope._pollDataDeferExec();
                    this.scope.loaded = true;
                };
            },

            'inserted': function(event){
                var user_self = this;
                var options = {
                    format: "yyyy-mm-dd",
                    startDate: moment().format("YYYY-MM-DD"),
                    autoclose: true,
                    immediateUpdates: true
                }

                var delivery_opts = $.extend(options, {
                    startdate: moment().add(3, "days").format("YYYY-MM-DD"),
                })

                $('#add-order-form input[name="pickup-date"]').datepicker(options)
                .on('changeDate', function(event){
                    var selected_date = moment($(this).datepicker('getDate'));
                    user_self.scope.newOrder.attr('pickup_date_submit', selected_date.format("YYYY/MM/DD"))
                    var washtypes = user_self.scope.newOrder.attr('washtypes') || null;
                    var delivery_datepicker = $('#add-order-form input[name="delivery-date"]');
                    var service_type = $('#add-order-form select[name="service"] option:selected').val();

                    if (service_type == 'regular') {
                        if (!washtypes) {
                            selected_date = selected_date.add(3, "days");
                        } else if (washtypes.indexOf('dryclean') > -1) {
                            selected_date = selected_date.add(5, "days");
                        } else if (washtypes.indexOf('laundry') > -1 || washtypes.indexOf('iron') > -1){
                            selected_date = selected_date.add(3, "days");
                        }
                    }else{
                        
                        selected_date = selected_date.add(1, "days");

                    }
                    delivery_datepicker.datepicker('setDate', selected_date.format("YYYY-MM-DD"));
                })

                $('#add-order-form input[name="delivery-date"]').datepicker(delivery_opts)
                .on('changeDate', function(event){
                    user_self.scope.newOrder.attr('schedule_date_submit', moment($(this).datepicker('getDate')).format("YYYY/MM/DD"))
                })

                var service_type = null;
                $('#add-order-form input[name="service"]').change(function(){
                    service_type = user_self.scope.newOrder.attr('service');
                });

                var selectize_service = $('input[name="service-types"]').selectize({
                    plugins : ['remove_button'],
                    valueField: 'name',
                    labelField: 'name',
                    searchField: 'name',
                    preload: true,
                    create: false,
                    render: {
                        item : function(item, escape){
                            return '<div style="color:#fff">' + 
                                        '<span>' + escape(
                                            item.name.replace(
                                                item.name.substr(0, 1),
                                                item.name.substr(0, 1).toUpperCase()
                                                )
                                            ) + '</span>&nbsp;' +
                                    '</div>';
                        },
                        option: function(item, escape) {
                            return '<div>' + 
                                        '<span>' + escape(
                                            item.name.replace(
                                                item.name.substr(0, 1),
                                                item.name.substr(0, 1).toUpperCase()
                                                )
                                            ) + '</span>&nbsp;' +
                                    '</div>';
                        }
                    },

                    load: function(query, callback){
                        if (localStorage.getItem('servicetype')) {
                            callback(JSON.parse(localStorage.getItem('servicetype')))
                        }else{
                            $.ajax({
                                url : "/api/servicetype",
                                type : 'get',
                                dataType : 'json',
                                success: function(data){
                                    callback(data);
                                    localStorage.setItem('servicetype', JSON.stringify(data));
                                },
                                error: function(xhr, status, error){
                                    callback();
                                }
                            });
                        }
                    },

                    onItemAdd: function(value, item){
                        user_self.scope.newOrder.attr('washtypes', this.$input[0].selectize.getValue())
                    },

                    onItemRemove: function(value){
                        user_self.scope.newOrder.attr('washtypes', this.$input[0].selectize.getValue())
                    }
                });

                user_self.scope.selectize = {
                    'service': selectize_service[0].selectize
                }

                $('#add-order-form input[name="pickup-date"]').datepicker('setDate', moment().format("YYYY-MM-DD"));

                

                var northEast = new gmaps.LatLng(13.094677, 77.794881);
                var southWest = new gmaps.LatLng(12.788851, 77.405553);
                var bounds = new gmaps.LatLngBounds(southWest, northEast);
                var options = {
                    bounds: bounds,
                    regions: ['sublocality'],
                    // types: ['(cities)'],
                    componentRestrictions: {country: 'in'}
                }
                var places = new gmaps.places.Autocomplete($('#users-locality')[0], options);
                gmaps.event.addListener(places, 'place_changed', function() {
                    var place = places.getPlace();
                    user_self.scope.selectedAddress.attr('locality', {
                        'map_string': place.formatted_address, 
                        'lat': place.geometry.location.lat(),
                        'lng': place.geometry.location.lng(),
                    })
                });

            }
        }
    })
})