define([
    'jquery',
    'can',
    '../../lib/mywash/constructs/map.helpers',
    '../../lib/mywash/components/tabs',
    'toastr',
    'nanobar',
    'datepicker',
    'momentjs',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'marketing-coupons-tab',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                var coup_self = this;
                var now = moment();
                this.order_status = new can.Map({});
                this.timeslots = new can.Map({})
                this.poll_skip = 0;
                this.poll_limit = 20;
                this.last_action = null;
                this.user_count = can.compute(0);

                this.search_skip = 0;
                this.search_limit = 20;

                this.nanobar = new Nanobar({
                    id: 'mybar',
                    bg: "#FF6600"
                })
                
                var statuses = JSON.parse(localStorage.getItem("statuses"));
                $.each(statuses, function(index, value){
                    coup_self.order_status.attr(index, value);
                })
                
                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                $.each(timeslots_temp, function(index, value){
                    coup_self.timeslots.attr(index, value);
                })
            },

            couponData: new can.List([]),
            loaded: false,
            selectedCoupon: new can.Map({}),
            selectize: null,

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

            getUserCount: function(){
                return this.user_count();
            },

            selectSearchOption: function(context, element, event) {
                var input = $(element).parents(".input-group").find(".search-input");
                var type = $(element).attr('data-option');
                if (type == "name") input.val("name:");
                input.focus();
            },

            captureEnterKey: function(context, element, event) {
                if (event.keyCode == 13) $("#users .btn-search-go").trigger('click');
            },

            searchUsers: function(context, element, event) {
                this._searchUsers(0, this.search_limit);
                this._searchUsersDeferred();
                
            },

            addCoupon: function(context, element, event) {
                if (!this.selectedCoupon.attr('data'))
                    this.selectedCoupon.attr('data', {});
                this.selectedCoupon.attr('is_active', true);
                this.__openCouponModal()
            },

            __openCouponModal: function(){
                $("#add-marketing-coupon-modal").modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                });
            },

            editCoupon: function(context, element, event) {
                var couponSelf = this;
                var coup_id = $(element).parents('tr').attr('index');
                console.log("coup_id ",coup_id);
                var defer = $.ajax({
                    url: "/api/coupon/" + index,
                    type: "get",
                    context: this,
                })

                defer.done(function(data){
                    this.activeEditId(index);
                    $.each(data.data, function(index, value){
                        couponSelf.editingItem.attr(index, value);
                    });
                    timeslotSelf.selectize['type'].addItem(data.data.type);
                    $.each(data.data.slots, function(index, value){
                        timeslotSelf.selectize['slots'].addItem(value);
                    });
                    $("#timeslot-block-modal").modal('show');
                })
                /*console.log("Welcome ")
                var coup_id = $(element).parents('tr').attr('index');
                console.log("coup_id ",coup_id);
                var arr_index = parseInt($(element).parents('tr').attr('arr-index'));
                $.ajax({
                    url: "/api/coupon/" + coup_id,
                    type: 'get',
                    dataType: 'json',
                    context: this,
                    success: function(data){
                        console.log(data);
                        var market_coupon_self = this;
                        this.selectedCoupon.attr(data.data[0], true);
                        this.selectedCoupon.attr("arr-index", arr_index);
                       $.each(data.data[0].start_date, function(index, value){
                            market_coupon_self.selectize['start-date'].createItem(value);
                        })
                       $.each(data.data[0].expiry_date, function(index, value){
                            market_coupon_self.selectize['expiry-date'].createItem(value);
                        })
                        
                        this.__openCouponModal()
                    }
                })*/
                
            },

            _validateCouponData: function(){
                if (!this.selectedCoupon.attr('data.name')) {
                    toastr.error("Name not provided.")
                    return false;
                };
                
                if (!this.selectedCoupon.attr('data.phone') || !this.selectedCoupon.attr('data.phone').attr().length) {
                    toastr.error("Phone number not provided.")
                    return false;
                }

                if (!this.selectedCoupon.attr('data.shift')) {
                    toastr.error("Shift not selected.")
                    return false;
                };

                if (typeof this.selectedCoupon.attr('is_active') != 'boolean') {
                    toastr.error("Status not selected.")
                    return false;
                };

                if (!this.selectedCoupon.attr('hub')) {
                    toastr.error("Hub not selected.")
                    return false;
                };

                return true;
            },

            saveCoupon: function(context, element, event) {
                var url = "/api/coupon", type = 'post';
                if (!this._validateCouponData()) return false;
                if (this.selectedCoupon.attr('str_id')) {
                    url = "/api/coupon/" + this.selectedCoupon.attr('str_id');
                    type = 'put';
                };
                $.ajax({
                    url: url,
                    type: type,
                    dataType: 'json',
                    context: this,
                    data: {
                        name: this.selectedCoupon.attr('data.name'),
                        data: this.selectedCoupon.attr('data.data'),
                        alias_coupon: this.selectedCoupon.attr('data.alias-coupon'),
                        start_date: this.selectedCoupon.attr('data.start-date'),
                        expiry_data: this.selectedCoupon.attr('data.expiry-date'),
                        is_active: this.selectedCoupon.attr('is_active'),
                    },
                    success: function(data){
                        var coupon_self = this;
                        if (!this.selectedCoupon.attr('str_id')) {
                            this.selectedCoupon.attr('str_id', data.str_id);
                            this.selectedCoupon.attr('coup_id', data.coup_id);
                            this.couponData.unshift(this.selectedCoupon.attr())
                            this.poll_skip += 1;
                        }else{
                            var arr_index = this.selectedCoupon.attr('arr-index');
                            this.selectedCoupon.each(function(value, index){
                                if(coupon_self.couponData.attr(arr_index).attr(index)){
                                    coupon_self.couponData.attr(arr_index).attr(index, value);
                                }
                            })
                            
                        }
                        this.closeCouponModal(context, element, event);
                    },
                    error: function(){
                        toastr.error("Some error occured.")
                    }
                })
            },

            couponDataChange: function(context, element, event) {
                var data = $(element).val().trim()
                if ($(element).attr('name') == 'name') {
                    this.selectedCoupon.attr('data.name', data);
                } else if ($(element).attr('name') == 'phone') {
                    this.selectedCoupon.attr('data.phone', data);
                } else if ($(element).attr('name') == 'shift') {
                    this.selectedCoupon.attr('data.shift', data);
                } else if ($(element).attr('name') == 'is_active') {
                    if (data == 'active')
                        this.selectedCoupon.attr('is_active', true);
                    else
                        this.selectedCoupon.attr('is_active', false);
                }
            },

            closeCouponModal: function(context, element, event) {
                $("#add-marketing-coupon-modal").modal('hide');
                this.selectedCoupon.attr({}, true);
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
                    var coup_self = this;
                    this.nanobar.go(50);
                    if (replace)
                        this.userData.replace([]);
                    $.each(data.data.users, function(index, value){
                        coup_self.userData.push(value);
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

            couponRefresh: function(context, element, event) {
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
                        var coup_self = this;
                        $.each(data.data, function(index, value){
                            coup_self.couponData.push(value);
                        })
                        this.poll_skip += data.data.length;
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
                    url: "/api/coupon/" + skip + "/" + limit,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                });
            },

            // Success part for _pollData ajax call
            _pollDataDeferExec: function(replace){
                if (typeof replace == 'undefined') replace = true;
                this._pollDataDefer.done(function(data){
                    var coup_self = this;
                    this.nanobar.go(50);
                    if (!data.data){
                        coup_self.nanobar.go(100);
                        return false;
                    }
                    if (!replace){
                        $.each(data.data, function(index, value){
                            coup_self.couponData.push(value);
                        })
                        this.poll_skip = this.poll_skip + data.data.length;
                    }
                    else{
                        this.couponData.replace(data.data);
                        this.poll_skip = data.data.length;
                    }

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
                if (route.sidebarmenu == "main-content-marketing-coupons" && !this.scope.loaded) {
                    this.scope._pollData();
                    this.scope._pollDataDeferExec();
                    this.scope.loaded = true;
                };
            },

            'inserted': function(event){
                var coupon_self = this;
                var options = {
                    format: "yyyy-mm-dd",
                    startDate: moment().format("YYYY-MM-DD"),
                    autoclose: true,
                    immediateUpdates: true
                }

                $('#add-marketing-coupon-modal .start-date').datepicker(options)
                .on('changeDate', function(event){
                    var selected_date = moment($(this).datepicker('getDate'));
                })

                $('#add-marketing-coupon-modal .expiry-date').datepicker(options)
                .on('changeDate', function(event){
                    var selected_date = moment($(this).datepicker('getDate'));
                })
            }
        }
    })
})