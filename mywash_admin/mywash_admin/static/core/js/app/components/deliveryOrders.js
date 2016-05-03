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
		tag: 'delivery-tabs',
		template: '',
		scope: TabsComponentScope.extend({
			init: function(){
				var delivery_self = this;
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
					delivery_self.order_status.attr(index, value);
				})
				
				var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
				$.each(timeslots_temp, function(index, value){
					delivery_self.timeslots.attr(index, value);
				})

			},

			orderData: new can.Map({}),
			loaded: false,
			failureReasons: new can.List([]),

			cleaningItems: new can.List([]),
			modalCustomerDetails: new can.Map({
				is_paid:false
			}),
			allCosts: new can.Map({}),
			deliveryRescheduleOldValue: new can.Map({}),

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
			
			orderRefresh: function(context, element, event) {
				var current_date = moment(this.orderDate());
				this._pollData('order', current_date, false, true);
			},

			getTotalQuantity: function(){
				return this.total_quantity();
			},

			getOrderDataKey: function(order_id){
                var arr_id;
                this.orderData.each(function(order, key){
                    if(order.attr(order_id)) arr_id = key;
                })
                return arr_id;
            },

			deliveryPrevday: function(context, element, event){
				var date = moment(this.attr('variableDate'));
				date.subtract(1, 'days');
				this.attr('variableDate', date.toDate());
				this._pollData('order', this.orderDate());
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
				var order_id = $("#delivery-order-details-modal").attr("index");
                var date = this.modalCustomerDetails.attr("data.schedules.delivery.schedule_date");
                var timeslot = this.modalCustomerDetails.attr("data.schedules.delivery.schedule_time");
				$.ajax({
					url: "/api/delivery",
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
                        toastr.success("Reschedule unsuccessful.")
                        this.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", this.deliveryRescheduleOldValue.attr('date'));
                        this.modalCustomerDetails.attr("data.schedules.delivery.schedule", this.deliveryRescheduleOldValue.attr('timeslot'));
                    }
				})
			},

			changeFailureReason: function(context, element, event){
				var pay_type=this.modalCustomerDetails.attr("data.is_paid");
				this.modalCustomerDetails.attr('is_paid',pay_type);


				var reason = $(element).val();
				var fail_reason = "";

				if (!this.modalCustomerDetails.attr("data").attr("reason")) {
					this.modalCustomerDetails.attr("data").attr("reason", {'type': null, 'value': null})
				};

				if(reason !=undefined && reason != 'none'){
					if (reason != "other") {
						this.modalCustomerDetails.attr("failure_reason",reason);
						this.modalCustomerDetails.attr("data").attr("reason", {'type': null});
					}else{
						if(this.modalCustomerDetails.attr('data.reason.value')!=undefined){
							this.modalCustomerDetails.attr('data.reason.value',undefined);
						}
						if(this.modalCustomerDetails.attr('data.failure_reason.partial_payment.full_reason')!=undefined){
							this.modalCustomerDetails.attr('data.failure_reason.partial_payment.full_reason',undefined);
						}
						this.modalCustomerDetails.attr("failure_reason",reason);
						this.modalCustomerDetails.attr("data").attr("reason", {'type': "others"});
					}
				}
			},


			deliveryNextday: function(context, element, event){
				var date = moment(this.attr('variableDate'));
				date.add(1, 'days');
				this.attr('variableDate', date.toDate());
				this._pollData('order', this.orderDate());
			},

			_addData: function(list){
				this.row_count(list.length);
				var map_keys = can.Map.keys(this.orderData);
				var delivery_self = this;
				var data = {}

				// Put the new values into the map.
				$.each(list, function(index, value){
					var status_details = delivery_self.getStatusDetails(value['status']);
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
				var delivery_self = this;
				var temp = {};
				$.each(list, function(index, value){
					temp[value['order_id']] = value['schedule_time'];
					var status_details = delivery_self.getStatusDetails(value['status']);
					value['status'] = status_details.formal_name;
					value['status_color'] = status_details.color;
					value['user_info']['name'] = value['user_info']['name'].trim();
					if (!delivery_self.orderData.attr(value['schedule_time']))
						delivery_self.orderData.attr(value['schedule_time'], {});
					if(!delivery_self.orderData.attr(value['schedule_time']).attr(value['order_id'])){
						delivery_self.orderData.attr(value['schedule_time']).attr(value['order_id'], value);
					}else{
						if(!delivery_self.orderData.attr(value['schedule_time']).attr(value['order_id']).attr('status') != value['status']){
							delivery_self.orderData.attr(value['schedule_time']).attr(value['order_id']).attr('status', value['status']);
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
					delivery_self.orderData.attr(key).removeAttr(value);
				})
			},

			_pollData: function(delivery_type, date, time, refresh){
				if(date) date = this.getFormattedDate(moment(date));
				if (time) time = this.getFormattedTime(moment(time));
				if(!refresh) refresh = false;
				var pollUrl = "";
				if(time){
					pollUrl = "/api/delivery/" + date + "/" + time;
				}else{
					pollUrl = "/api/delivery/" + date;
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

				var failure_reason_defer = $.ajax({
					url: "/api/failurereason/partial_payment",
					type: 'get',
					dataType: 'json',
				})

				var delivery_self = this;
				$.when(item_defer, failure_reason_defer).done(function(item_data, reason_data){
					item_data = item_data[0];
					reason_data = reason_data[0];
					delivery_self.failureReasons.attr(reason_data.data);
					delivery_self.nanobar.go(50);
					delivery_self.cleaningItems.replace(item_data.data);
					item_data.customer_details['status'] = delivery_self.getStatusDetails(item_data.customer_details['status']).attr('name_id')

					delivery_self.modalCustomerDetails.attr('data', item_data.customer_details);

					if(delivery_self.modalCustomerDetails.attr('data.failure_reason.partial_payment.reason') != undefined){
						delivery_self.modalCustomerDetails.attr('failure_reason',delivery_self.modalCustomerDetails.attr('data.failure_reason.partial_payment.reason'));
					}

					if(delivery_self.modalCustomerDetails.attr('data.failure_reason.partial_payment.full_reason') == 'other' ){
						delivery_self.modalCustomerDetails.attr('failure_reason','other');
					}
						
					if (!delivery_self.modalCustomerDetails.attr("data").attr("reason")) {
						delivery_self.modalCustomerDetails.attr("data").attr("reason", {'type': null, 'value': null})
					};

					var new_value = delivery_self.modalCustomerDetails.attr('data.is_paid');

					if(new_value =='not_paid'){
							delivery_self.modalCustomerDetails.attr('disable_amt',true);
					}else{
						delivery_self.modalCustomerDetails.attr('disable_amt',false);

					}

					var reason_others = true;

					if (delivery_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason")) {
						delivery_self.failureReasons.each(function(value, index){
							if (delivery_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason") == value.attr('str_id')){
								delivery_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason",value.attr('str_id'));
								reason_others = false;
							}
						})
						
						if (reason_others){
							delivery_self.modalCustomerDetails.attr('data.reason.type', 'others');
						}
					}else{
						delivery_self.modalCustomerDetails.attr('data.reason.type', 'none');
					}

					$("#delivery-order-details-modal").attr('index', index);
					var summernote = $("#delivery-order-details-modal .summernote");
					summernote.html(delivery_self.modalCustomerDetails.attr('data.remark'));
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
					    	delivery_self.modalCustomerDetails.attr('data.remark', $("#delivery-order-details-modal .summernote").code());
					    }
					});

					$("#delivery-order-details-modal").modal({
						backdrop: 'static',
						keyboard: false,
						show: true
					});
					delivery_self.nanobar.go(100);
					$("#delivery-order-details-modal table").focus();
					delivery_self._update_total_cost();
					delivery_self._update_total_quantity();
					//delivery_self.changePaymentStatus();
					
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

			_update_credits: function(context, element, event){
				var available_credits = this.modalCustomerDetails.attr("data.credits.available");

				var total_cost=this.modalCustomerDetails.attr('data.cost.total');
				var cash_collected=this.modalCustomerDetails.attr('data.cash_collected');
				if(cash_collected > total_cost){

					var credits_to_add=cash_collected-total_cost;
					if (!available_credits){
						available_credits = this.modalCustomerDetails.attr("data.user.credits");
						available_credits+=credits_to_add;

						this.modalCustomerDetails.attr("data.user.credits", Math.round(available_credits));
						}else{
							available_credits = this.modalCustomerDetails.attr("data.user.credits");
						available_credits+=credits_to_add;

						this.modalCustomerDetails.attr("data.user.credits", Math.round(available_credits));
					}

				}
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

				if (this.modalCustomerDetails.attr("data.service_tax.type") == 'inclusive') {
					this.allCosts.attr('service_tax', this.modalCustomerDetails.attr("data.service_tax.amount"))
				} else if(this.modalCustomerDetails.attr("data.service_tax.type") == 'exclusive') {
					total_cost += this.modalCustomerDetails.attr("data.service_tax.amount")
					this.allCosts.attr('service_tax', this.modalCustomerDetails.attr("data.service_tax.amount"))
				}

				this.allCosts.attr('total_cost', Math.round(total_cost));
			},

			changeMaxDiscount: function(context, element, event){
				var max_discount_amount = $('#delivery-order-details-modal .modal-discount-max-amount').val() || 0;
				this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
				this._update_total_cost();
			},

			changeDiscount: function(context, element, event){
				var discount_type = $('#delivery-order-details-modal .modal-discount-type li.active');
				this.applyDiscount(context, discount_type, event);
			},

			
			applyDiscount: function(context, element, event){
				var is_percentage = $(element).hasClass('modal-discount-percentage');
				var discount_amount = $('#delivery-order-details-modal .modal-discount-amount').val() || 0;

				if (is_percentage) {
					// discount = total_cost * discount_amount/100;
					this.modalCustomerDetails.attr("data.discount.percentage", true);
				}else{
					this.modalCustomerDetails.attr("data.discount.percentage", false);
				}
				this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
				this._update_total_cost();
			},

			
			saveOrderChanges: function(context, element, event){
				var index = $("#delivery-order-details-modal").attr('index');

				$(element).button('loading');

				$.ajax({
					url: "/api/orderitem/" + index,
					type: "post",
					context: this,
					data: {
						remark: this.modalCustomerDetails.attr('data.remark'),
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
				var order_id = $("#delivery-order-details-modal").attr('index');
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
						toastr.success("Status changed successfully!")
					}
				})
			},

			closeModal: function(context, element, event){
				$("#delivery-order-details-modal .summernote").destroy();
				$("delivery-tabs .btn-refresh").trigger('click');
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
                if (route.sidebarmenu == "main-content-delivery" && !this.scope.loaded) {
                    this.scope._pollData('order', now);
                    this.scope.loaded = true;
                };
            },

            '#delivery-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },

			'inserted': function(){
				var delivery_self = this;
				var options = {
					format: "yyyy-mm-dd",
					startdate: "2014-10-22",
					autoclose: true,
					todayBtn: true
				}
				// Order date datepicker
				$("delivery-tabs .datepicker-here").datepicker(options).on('changeDate', function(event){
					var target = event.currentTarget;
					var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
					var order_id = $("#delivery-order-details-modal").attr("index");
					var formatted_value = selectedDate.format("YYYY/MM/DD");

					if ($(target).hasClass("order-datepicker")) {
						delivery_self.scope._pollData('order', selectedDate);
						delivery_self.scope.attr('variableDate', selectedDate.toDate());
					}else if ($(target).hasClass("modal-delivery-datepicker")) {
						var oldValue = delivery_self.scope.modalCustomerDetails.attr("data.schedules.delivery.schedule_date")
	                    delivery_self.scope.deliveryRescheduleOldValue.attr('date', oldValue);
	                    delivery_self.scope.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", selectedDate.format("YYYY/MM/DD"))
					};
					
				});
			},

			".click-to-assign click": function(element, event){
                var delivery_self = this;
                var order_id = element.parents('tr').attr('index');
                var arr_id = null;
                delivery_self.scope.orderData.each(function(order, key){
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
                                var assigned_to = delivery_self.scope.orderData.attr(arr_id).attr(order_id + ".assigned_to");
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
                            var order = delivery_self.scope.orderData.attr(arr_id).attr(order_id);
                            if(!order.attr("assigned_to"))
                                order.attr("assigned_to", {})
                            order.attr("assigned_to").attr("name", value['name']);
                            order.attr("assigned_to").attr("str_id", value['str_id']);
                            order.attr("status", delivery_self.scope.getStatusDetails('delivery_progress').formal_name);
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