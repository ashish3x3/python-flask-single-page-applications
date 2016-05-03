define([
    'jquery',
    'can',
    '../../lib/mywash/constructs/map.helpers',
    '../../lib/mywash/components/tabs',
    'toastr',
    'nanobar',
    'momentjs',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'logistic-staffs-tab',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                var emp_self = this;
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
                    emp_self.order_status.attr(index, value);
                })
                
                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                $.each(timeslots_temp, function(index, value){
                    emp_self.timeslots.attr(index, value);
                })
            },

            staffData: new can.List([]),
            loaded: false,
            selectedStaff: new can.Map({}),
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

            addStaff: function(context, element, event) {
                if (!this.selectedStaff.attr('data'))
                    this.selectedStaff.attr('data', {});
                this.selectedStaff.attr('is_active', true);
                this.selectedStaff.attr('data.shift', "1");
                this.__openStaffModal()
            },

            __openStaffModal: function(){
                $("#add-logistic-staff-modal").modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                });
            },

            editStaff: function(context, element, event) {
                var emp_id = $(element).parents('tr').attr('index');
                var arr_index = parseInt($(element).parents('tr').attr('arr-index'));
                $.ajax({
                    url: "/api/employee/" + emp_id,
                    type: 'get',
                    dataType: 'json',
                    context: this,
                    success: function(data){
                        var log_staff_self = this;
                        this.selectedStaff.attr(data.data[0], true);
                        this.selectedStaff.attr("arr-index", arr_index);
                        $.each(data.data[0].data.phone, function(index, value){
                            log_staff_self.selectize['phone'].createItem(value);
                        })
                        if (data.data[0].hub)
                            log_staff_self.selectize['hub'].addItem(data.data[0].hub.str_id);
                        this.__openStaffModal()
                    }
                })
                
            },

            _validateStaffData: function(){
                if (!this.selectedStaff.attr('data.name')) {
                    toastr.error("Name not provided.")
                    return false;
                };
                
                if (!this.selectedStaff.attr('data.phone') || !this.selectedStaff.attr('data.phone').attr().length) {
                    toastr.error("Phone number not provided.")
                    return false;
                }

                if (!this.selectedStaff.attr('data.shift')) {
                    toastr.error("Shift not selected.")
                    return false;
                };

                if (typeof this.selectedStaff.attr('is_active') != 'boolean') {
                    toastr.error("Status not selected.")
                    return false;
                };

                if (!this.selectedStaff.attr('hub')) {
                    toastr.error("Hub not selected.")
                    return false;
                };

                return true;
            },

            saveStaff: function(context, element, event) {
                var url = "/api/employee", type = 'post';
                if (!this._validateStaffData()) return false;
                if (this.selectedStaff.attr('str_id')) {
                    url = "/api/employee/" + this.selectedStaff.attr('str_id');
                    type = 'put';
                };
                $.ajax({
                    url: url,
                    type: type,
                    dataType: 'json',
                    context: this,
                    data: {
                        name: this.selectedStaff.attr('data.name'),
                        phone: JSON.stringify(this.selectedStaff.attr('data.phone').attr()),
                        shift: this.selectedStaff.attr('data.shift'),
                        hub_id: this.selectedStaff.attr('hub').attr('str_id'),
                        is_active: this.selectedStaff.attr('is_active'),
                    },
                    success: function(data){
                        var staff_self = this;
                        if (!this.selectedStaff.attr('str_id')) {
                            this.selectedStaff.attr('str_id', data.str_id);
                            this.selectedStaff.attr('emp_id', data.emp_id);
                            this.staffData.unshift(this.selectedStaff.attr())
                            this.poll_skip += 1;
                        }else{
                            var arr_index = this.selectedStaff.attr('arr-index');
                            this.selectedStaff.each(function(value, index){
                                if(staff_self.staffData.attr(arr_index).attr(index)){
                                    staff_self.staffData.attr(arr_index).attr(index, value);
                                }
                            })
                            
                        }
                        this.closeStaffModal(context, element, event);
                    },
                    error: function(){
                        toastr.error("Some error occured.")
                    }
                })
            },

            staffDataChange: function(context, element, event) {
                var data = $(element).val().trim()
                if ($(element).attr('name') == 'name') {
                    this.selectedStaff.attr('data.name', data);
                } else if ($(element).attr('name') == 'phone') {
                    this.selectedStaff.attr('data.phone', data);
                } else if ($(element).attr('name') == 'shift') {
                    this.selectedStaff.attr('data.shift', data);
                } else if ($(element).attr('name') == 'is_active') {
                    if (data == 'active')
                        this.selectedStaff.attr('is_active', true);
                    else
                        this.selectedStaff.attr('is_active', false);
                }
            },

            closeStaffModal: function(context, element, event) {
                $("#add-logistic-staff-modal").modal('hide');
                this.selectedStaff.attr({}, true);
                this.selectize['phone'].clearOptions();
                this.selectize['phone'].clear();
                this.selectize['hub'].clear();
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
                    var emp_self = this;
                    this.nanobar.go(50);
                    if (replace)
                        this.userData.replace([]);
                    $.each(data.data.users, function(index, value){
                        emp_self.userData.push(value);
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

            staffRefresh: function(context, element, event) {
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
                        var emp_self = this;
                        $.each(data.data, function(index, value){
                            emp_self.staffData.push(value);
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
                    url: "/api/employee/" + skip + "/" + limit,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                });
            },

            // Success part for _pollData ajax call
            _pollDataDeferExec: function(replace){
                if (typeof replace == 'undefined') replace = true;
                this._pollDataDefer.done(function(data){
                    var emp_self = this;
                    this.nanobar.go(50);
                    if (!data.data){
                        emp_self.nanobar.go(100);
                        return false;
                    }
                    if (!replace){
                        $.each(data.data, function(index, value){
                            emp_self.staffData.push(value);
                        })
                        this.poll_skip = this.poll_skip + data.data.length;
                    }
                    else{
                        this.staffData.replace(data.data);
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
                if (route.sidebarmenu == "main-content-logistic-staffs" && !this.scope.loaded) {
                    this.scope._pollData();
                    this.scope._pollDataDeferExec();
                    this.scope.loaded = true;
                };
            },

            'inserted': function(){
                var log_staff_self = this;

                var selectize_phone = $('#add-logistic-staff-modal .add-phone-input').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    maxItems: 1,
                    create: function(input) {
                        return {
                            value: input,
                            text: input
                        }
                    },

                    onItemAdd: function(value, item){
                        var this_selectize = this.$input[0].selectize;
                        var re = /^((\+?91)|(0))?\d{8,12}$/;
                        if (!log_staff_self.scope._validatePhone(value)) {
                            toastr.error("Invalid number", value)
                            this_selectize.removeItem(value);
                            return false;
                        };
                        if(!log_staff_self.scope.selectedStaff.attr('data.phone'))
                            log_staff_self.scope.selectedStaff.attr('data.phone', []);
                        if(log_staff_self.scope.selectedStaff.attr('data.phone').indexOf(value) == -1)
                            log_staff_self.scope.selectedStaff.attr('data.phone').push(value);
                    },

                    onItemRemove: function(value){
                        var index = log_staff_self.scope.selectedStaff.attr('data.phone').indexOf(value);
                        log_staff_self.scope.selectedStaff.attr('data.phone').removeAttr(index);
                    }
                });

                var selectize_hub = $("#add-logistic-staff-modal .select-hub-input").selectize({
                    plugins : ['remove_button'],
                    valueField: 'str_id',
                    labelField: 'name',
                    searchField: ['name', 'short'],
                    preload: true,
                    create: false,

                    render: {
                        item : function(item, escape){
                            return '<div>' + 
                                        '<span>' + escape(item.name) + " " + "<b>(" + item.short.toUpperCase() + ")</b>" + '</span>&nbsp;' +
                                    '</div>';
                        },
                        option: function(item, escape) {
                            return '<div>' + 
                                        '<span>' + escape(item.name) + " " + "<b>(" + item.short.toUpperCase() + ")</b>" + '</span>&nbsp;' +
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
                                callback(data.data);
                            },
                            error: function(xhr, status, error){
                                callback();
                            }
                        });
                    },

                    onItemAdd: function(value, item){
                        var text_list = item.text().split('(');
                        log_staff_self.scope.selectedStaff.attr('hub', {
                            str_id: value,
                            name: text_list[0],
                            'short': text_list[1].replace('(', '').replace(')', '').replace(' ', '')
                        });
                    },
                })

                log_staff_self.scope.selectize = {
                    'phone': selectize_phone[0].selectize,
                    'hub': selectize_hub[0].selectize,
                }
            }
        }
    })
})