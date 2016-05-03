define([
    'jquery',
    'can',
    '../../lib/mywash/constructs/map.helpers',
    '../../lib/mywash/components/tabs',
    'toastr',
    'nanobar',
    'momentjs',
    'selectize',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return TabsComponent.extend({
        tag: 'vendor-tab',
        template: '',
        scope: TabsComponentScope.extend({
            init: function(){
                this.skip = 0;
                this.limit = 20;
            },

            vendorList: new can.Map({}),
            loaded: false,
            selectedVendor: new can.Map({}),
            selectize: null,

            selectedVendorChange: function(context, element, event){
                if ($(element).attr("name") == "name") {
                    this.selectedVendor.attr('name', $(element).val())
                } else if ($(element).attr("name") == "address") {
                    this.selectedVendor.attr('address', $(element).val().trim())
                } else if ($(element).attr("name") == "status") {
                    var value = $(element).val();
                    if(value == "active")
                        this.selectedVendor.attr('is_active', true);
                    else if(value == "inactive")
                        this.selectedVendor.attr('is_active', false);
                }
            },

            addVendor: function(context, element, event){
                this.selectedVendor.attr('is_active', true);
                $("#vendor-data-modal").modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                })
            },

            vendorRefresh: function(refresh, skip, limit){
                this._pollData(false, 0, this.skip);
            },

            _pollData: function(refresh, skip, limit){
                if (typeof refresh == 'undefined')
                    refresh = false;

                if(typeof skip == 'undefined')
                    skip = this.skip;

                if(typeof limit == 'undefined')
                    limit = this.limit;

                $.ajax({
                    url: "/api/vendor/" + skip + "/" + limit,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                    success: function(data){
                        var vendor_self = this;
                        if (refresh) {
                            // Check to add
                            $.each(data, function(key, value){
                                if (!vendor_self.vendorList.attr(key))
                                    vendor_self.vendorList.attr(key, value);
                                else{
                                    if (vendor_self.vendorList.attr(key + ".data.name") != value['data']['name'])
                                        vendor_self.vendorList.attr(key + ".data.name", value['data']['name'])
                                    if (vendor_self.vendorList.attr(key + ".data.address") != value['data']['address'])
                                        vendor_self.vendorList.attr(key + ".data.address", value['data']['address'])
                                    if (vendor_self.vendorList.attr(key + ".is_active") != value['is_active'])
                                        vendor_self.vendorList.attr(key + ".is_active", value['is_active'])
                                    vendor_self.vendorList.attr(key + ".services", value['services'])
                                    vendor_self.vendorList.attr(key + ".data.phone", value['data']['phone'])
                                    vendor_self.vendorList.attr(key + ".data.email", value['data']['email'])
                                    
                                }
                            })
                            var delete_list = [];
                            this.vendorList.each(function(value, key){
                                if (!data[key])
                                    delete_list.push(key);
                            })
                            $.each(delete_list, function(key, value){
                                vendor_self.vendorList.removeAttr(value);
                            })
                        }else{
                            this.vendorList.attr(data, true);
                            this.skip = can.Map.keys(this.vendorList).length;
                        }
                    }
                })
            },
            
            editVendor: function(context, element, event){
                var vendor_id = $(element).parents("tr").attr("index");
                $.ajax({
                    url: "/api/vendor/" + vendor_id,
                    type: "get",
                    context: this,
                    dataType: 'json',
                    success: function(data){
                        var vendor_self = this;
                        data['address'] = data['address'].trim();
                        this.selectedVendor.attr(data, true);
                        this.selectedVendor.attr('str_id', vendor_id);
                        $.each(data['phone'], function(key, value){
                            vendor_self.selectize['phone'].createItem(value);
                        })

                        $.each(data['email'], function(key, value){
                            vendor_self.selectize['email'].createItem(value);
                        })
                        var service_ids = []
                        $.each(data['services'], function(key, value){
                            vendor_self.selectize['service'].addItem(value['id']);
                            service_ids.push(value['id']);
                        })

                        this.selectedVendor.attr('services', service_ids);

                        $("#vendor-data-modal").modal({
                            backdrop: 'static',
                            keyboard: false,
                            show: true
                        })
                    }
                })
                
                
            },

            _validateVendorForm: function(){
                if (!this.selectedVendor.attr('name')) {
                    toastr.error("Name not provided.")
                    return false;
                };
                
                if (!this.selectedVendor.attr('phone') || !this.selectedVendor.attr('phone').attr().length) {
                    toastr.error("Phone number not provided.")
                    return false;
                }

                if (!this.selectedVendor.attr('email')) {
                    toastr.error("Email not provided.")
                    return false;
                };

                if (!this.selectedVendor.attr('services')) {
                    toastr.error("Services not selected.")
                    return false;
                };

                if (typeof this.selectedVendor.attr('is_active') != 'boolean') {
                    toastr.error("Status not selected.")
                    return false;
                };

                return true;
            },

            saveVendor: function(context, element, event){
                if (!this._validateVendorForm()) return false;
                var vendor_id = null;
                if(this.selectedVendor.attr('str_id'))
                    vendor_id = this.selectedVendor.attr('str_id');
                var type = "post", url = "/api/vendor";
                if (vendor_id) {
                    type = 'put';
                    url = "/api/vendor/" + vendor_id;
                };
                $.ajax({
                    url: url,
                    type: type,
                    dataType: 'json',
                    context: this,
                    data: {
                        name: this.selectedVendor.attr('name'),
                        email: JSON.stringify(this.selectedVendor.attr('email').attr()),
                        phone: JSON.stringify(this.selectedVendor.attr('phone').attr()),
                        address: this.selectedVendor.attr('address'),
                        services: JSON.stringify(this.selectedVendor.attr('services').attr()),
                        is_active: this.selectedVendor.attr('is_active')
                    },
                    success: function(data){
                        var data = {
                            data: {
                                name: this.selectedVendor.attr('name'),
                                email: JSON.stringify(this.selectedVendor.attr('email').attr()),
                                phone: JSON.stringify(this.selectedVendor.attr('phone').attr()),
                                address: this.selectedVendor.attr('address'),
                            },
                            is_active: this.selectedVendor.attr('is_active'),
                            services: this.selectedVendor.attr('services').attr(),
                        }

                        if(this.selectedVendor.attr('str_id')){
                            data['str_id'] = this.selectedVendor.attr('str_id');
                            this.vendorList.attr(data['str_id'], data);
                        }else{
                            data['str_id'] = data.str_id;
                            this.vendorList.attr(data.str_id, data);
                            this.limit += 1;
                            console.log(this.limit)
                        }

                        this.closeVendorModal(context, element, event);
                    }
                })
            },

            loadMoreRows: function(context, element, event){
                this._pollData(true)
            },

            closeVendorModal: function(context, element, event){
                $("#vendor-data-modal").modal('hide');
                this.selectedVendor.attr({},true);
                $.each(this.selectize, function(index, value){
                    value.clear();
                    if (index != 'service')
                        value.clearOptions();
                })
            }

        }),

        helpers: $.extend(BaseHelpers, {
            
        }),


        events: {
            '{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-vendors" && !this.scope.loaded) {
                    this.scope._pollData(false);
                    this.scope.loaded = true;
                };
            },

            'inserted': function(){
                var vendor_self = this;

                var selectize_phone = $('#vendor-data-modal .add-phone-input').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: function(input) {
                        return {
                            value: input,
                            text: input
                        }
                    },

                    onItemAdd: function(value, item){
                        var this_selectize = this.$input[0].selectize;
                        var re = /^((\+?91)|(0))?\d{8,12}$/;
                        if (!re.test(value)) {
                            toastr.error("Invalid number", value)
                            this_selectize.removeItem(value);
                            return false;
                        };
                        if(!vendor_self.scope.selectedVendor.attr('phone'))
                            vendor_self.scope.selectedVendor.attr('phone', []);
                        if(vendor_self.scope.selectedVendor.attr('phone').indexOf(value) == -1)
                            vendor_self.scope.selectedVendor.attr('phone').push(value);
                    },

                    onItemRemove: function(value){
                        console.log(vendor_self.scope.selectedVendor.attr());
                        var index = vendor_self.scope.selectedVendor.attr('phone').indexOf(value);
                        vendor_self.scope.selectedVendor.attr('phone').removeAttr(index);
                    }
                });

                var selectize_email = $('#vendor-data-modal .add-email-input').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: function(input) {
                        return {
                            value: input,
                            text: input
                        }
                    },

                    onItemAdd: function(value, item){
                        var this_selectize = this.$input[0].selectize;
                        var email_re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                        if(!email_re.test(value)){
                            toastr.error("Invalid email", value)
                            this_selectize.removeItem(value);
                            return false;
                        }
                        if(!vendor_self.scope.selectedVendor.attr('email'))
                            vendor_self.scope.selectedVendor.attr('email', []);
                        if(vendor_self.scope.selectedVendor.attr('email').indexOf(value) == -1)
                            vendor_self.scope.selectedVendor.attr('email').push(value);
                    },

                    onItemRemove: function(value){
                        var index = vendor_self.scope.selectedVendor.attr('email').indexOf(value);
                        vendor_self.scope.selectedVendor.attr('email').removeAttr(index);
                    }
                });

                var selectize_service = $('#vendor-data-modal .add-service-input').selectize({
                    plugins : ['remove_button'],
                    valueField: 'id',
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
                        if(!vendor_self.scope.selectedVendor.attr('services'))
                            vendor_self.scope.selectedVendor.attr('services', []);
                        if (vendor_self.scope.selectedVendor.attr('services').indexOf(value) == -1)
                            vendor_self.scope.selectedVendor.attr('services').push(value);
                    },

                    onItemRemove: function(value){
                        var index = vendor_self.scope.selectedVendor.attr('services').indexOf(value);
                        vendor_self.scope.selectedVendor.attr('services').removeAttr(index);
                    }
                });


                vendor_self.scope.selectize = {
                    'phone': selectize_phone[0].selectize,
                    'email': selectize_email[0].selectize,
                    'service': selectize_service[0].selectize,
                }
            }
        }
    })
})