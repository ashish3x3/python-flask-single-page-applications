define([
	'jquery',
	'can',
	'../../lib/mywash/constructs/map.helpers',
	'../../lib/mywash/components/tabs',
	'toastr',
	'nanobar',
	'momentjs',
	'summernote',
],function($, can, BaseHelpers, TabsComponents, toastr, Nanobar){
	'use strict';

	var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

	return TabsComponent.extend({
		tag: 'all-orders-tabs',
		template: '',
		scope: TabsComponentScope.extend({
			init: function(){
				var all_orders_self = this;
				var now = moment();
				this.order_status = new can.Map({});
				this.timeslots = new can.Map({})
				this.poll_skip = 0;
				this.poll_limit = 20;
				this.last_action = null;
				this.total_quantity = can.compute(0);
				this.row_count = can.compute(0);

				this.search_skip = 0;
				this.search_limit = 20;

				this.nanobar = new Nanobar({
					id: 'mybar',
					bg: "#FF6600"
				})
				
				var statuses = JSON.parse(localStorage.getItem("statuses"));
				$.each(statuses, function(index, value){
					all_orders_self.order_status.attr(index, value);
				})
				
				var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
				$.each(timeslots_temp, function(index, value){
					all_orders_self.timeslots.attr(index, value);
				})
			},

			orderData: new can.Map({}),
			loaded: false,
			failureReasons: new can.List([]),

			cleaningItems: new can.List([]),
			modalCustomerDetails: new can.Map({}),
			allCosts: new can.Map({}),
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

			pickupPrevday: function(context, element, event){
                var date = moment(this.attr('variableDate'));
                date.subtract(1, 'days');
                this.attr('variableDate', date.toDate());
                this._pollData(this.orderDate());
                this._pollDataDeferExec();
            },

            pickupNextday: function(context, element, event){
                var date = moment(this.attr('variableDate'));
                date.add(1, 'days');
                this.attr('variableDate', date.toDate());
                this._pollData(this.orderDate());
                this._pollDataDeferExec();
            },

			pickupTimeSlotChange: function(context, element, event){
				var order_id = $("#all-orders-order-details-modal").attr("index");
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
				var order_id = $("#all-orders-order-details-modal").attr("index");
				var index = $(element).val();
				if (index == 0) {
					index = $(element).attr('value');
				};
				var value = this.timeslots.attr(index);
				
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
						this.modalCustomerDetails.attr("data.schedules.delivery.schedule", value);
						toastr.success("Timeslot changed.")
					},
					error: function(xhr, status, error){
						toastr.error("Timeslot change error.")
					}
				})
			},


			selectSearchOption: function(context, element, event) {
				var input = $(element).parents(".input-group").find(".search-input");
				var type = $(element).attr('data-option');
				if (type == "name") input.val("name:");
				else if (type == "email") input.val("email:");
				else if (type == "phone") input.val("phone:");
				else if (type == "oid") input.val("oid:");
				input.focus();
			},

			captureEnterKey: function(context, element, event) {
				if (event.keyCode == 13) $("all-orders-tabs .btn-search-go").trigger('click');
			},

			searchOrders: function(context, element, event) {
				this._searchOrders(0, this.search_limit);
				this._searchOrdersDeferred();
			},

			_searchOrders: function(skip, limit) {
				var search_term = $.trim($("all-orders-tabs .search-input").val());
				if(search_term == ""){
					$("all-orders-tabs .btn-refresh").trigger('click');
					return;
				}
				skip = typeof skip == 'undefined'? this.search_skip : skip;
				limit = typeof limit == 'undefined'? this.search_limit : limit;
				this.nanobar.go(30);
				this.all_orders_search_defer = $.ajax({
					url: "/api/order/search/" + search_term + "/" + skip + "/" + limit,
					type: 'get',
					dataType: 'json',
					context: this,
				})
			},

			_searchOrdersDeferred: function() {
				this.all_orders_search_defer.done(function(data){
					var all_orders_self = this;
					this.nanobar.go(50);
					var insert_data = {};
					$.each(data.data, function(index, value){
						var status_details = all_orders_self.getStatusDetails(value['status']);
						value['status_formal'] = status_details.formal_name;
						value['status_color'] = status_details.color;
						value['user_info']['name'] = value['user_info']['name'].trim();
						insert_data[value['order_id']] = value;
					})
					this.orderData.attr(insert_data, true);
					
					this.search_skip += data.data.length;
					this.nanobar.go(100);
					this.last_action = "search"
				})

				this.all_orders_search_defer.fail(function(xhr, status, error){
					this.nanobar.go(100);
					toastr.error("Proper search criteria not used.")
				})
			},


			orderRefresh: function(context, element, event) {
				if (this.last_action == 'query') {
					this._pollData(this.orderDate());
					this._pollDataDeferExec(true);
				}else{
					this.searchOrders();
				}
			},

			getTotalQuantity: function(){
				return this.total_quantity();
			},

			loadMoreRows: function(context, element, event) {
				$(element).button('load');
				$(element).find(".fa-repeat").addClass("fa-spin");
				if (this.last_action == "search") {
					this._searchOrders();
					this._searchOrdersDeferred(false);

				}else{
					this._pollData();
					this._pollDataDefer.done(function(data){
						this.nanobar.go(50);
						var all_orders_self = this;
						$.each(data.data, function(index, value){
							var status_details = all_orders_self.getStatusDetails(value['status']);
							value['status'] = status_details.formal_name;
							value['status_color'] = status_details.color;
							all_orders_self.orderData.push(value);
						})
						this.poll_skip += data.data.length;
						$(element).button('reset');
						$(element).find(".fa-repeat").removeClass("fa-spin");
						this.nanobar.go(100);
					})
				}
				
			},

			_pollData: function(date){
				if(date) date = this.getFormattedDate(moment(date));
				this.nanobar.go(30);
				this._pollDataDefer = $.ajax({
					url: "/api/order/pickup/" + date,
					type: 'get',
					context: this,
					dataType: 'json',
				});
			},

			_addData: function(data){
				this.row_count(data.length);
				var all_orders_self = this;
				var input_data = {};
				$.each(data, function(index, value){
					var status_details = all_orders_self.getStatusDetails(value['status']);
					value['status_formal'] = status_details.formal_name;
					value['status_color'] = status_details.color;
					value['pickup_date'] = value['pickup_data']['schedule_date'];
					value['delivery_date'] = value['delivery_data']['schedule_date'];
					value['user_info']['name'] = value['user_info']['name'].trim();
					delete(value['delivery_data']);
					delete(value['pickup_data']);
					input_data[value['order_id']] = value;
				})
				all_orders_self.orderData.attr(input_data, true);
			},

			_updateData: function(data){
				this.row_count(data.length);
                var all_orders_self = this;
                var temp = [];
                $.each(data, function(index, value){
                	temp.push(value['order_id'])
                    if (!all_orders_self.orderData.attr(value['order_id'])) {
                    	var status_details = all_orders_self.getStatusDetails(value['status']);
	                    value['status_formal'] = status_details.formal_name;
	                    value['status_color'] = status_details.color;
	                    value['user_info']['name'] = value['user_info']['name'].trim();
	              		delete(value['delivery_data']);
						delete(value['pickup_data']);
						all_orders_self.orderData.attr(value['order_id'], value);
                    } else {
                    	if (all_orders_self.orderData.attr(value['order_id'] + '.status') != value['status']) {
                    		var status_details = all_orders_self.getStatusDetails(value['status']);
		                    all_orders_self.orderData.attr(value['order_id'] + '.status_formal', status_details.formal_name);
		                    all_orders_self.orderData.attr(value['order_id'] + '.status_color', status_details.color);
		                    all_orders_self.orderData.attr(value['order_id'] + '.status', value['status']);
                    	};
                    }
                    
                })
                
                // Collect obsolete objects
                var delete_map = []
                this.orderData.each(function(value, key){
                	if (temp.indexOf(key) == -1)
                        delete_map.push(key);
                })
                // Delete obsolete objects
                $.each(delete_map, function(key, value){
                    all_orders_self.orderData.removeAttr(value);
                })
			},

			// Success part for _pollData ajax call
			_pollDataDeferExec: function(refresh){
				if (typeof refresh == 'undefined') refresh = false;
				this._pollDataDefer.done(function(data){
					this.nanobar.go(50);

					if (!data.data){
						this.nanobar.go(100);
						return false;
					}

					if(!refresh) this._addData(data.data);
					else this._updateData(data.data);
					
					this.poll_skip = data.data.length;
					this.last_action = "query"
					this.nanobar.go(100);
				})
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

					//if(express) then final*2
					item.attr('final_cost', laundry + dryclean + iron);
				}
				this._update_total_cost();
				this._update_total_quantity();
			},

			changeFailureReason: function(context, element, event){
				var pay_type=this.modalCustomerDetails.attr("data.is_paid");

				this.modalCustomerDetails.attr('is_paid',pay_type);
				
				var reason = $(element).val();
				var fail_reason = "";

				if (!this.modalCustomerDetails.attr("data").attr("reason")) {
					this.modalCustomerDetails.attr("data").attr("reason", {'type': null, 'value': null})

				};

				if(reason !=undefined){
					if (reason != "other") {
						this.modalCustomerDetails.attr("failure_reason",reason);
						this.modalCustomerDetails.attr("data").attr("reason", {'type': null});
					}else{
						this.modalCustomerDetails.attr("failure_reason",reason);
						this.modalCustomerDetails.attr("data").attr("reason", {'type': "others"});
					}
				}
			},

			changeOtherReason: function(context, element, event){
				this.modalCustomerDetails.attr("data").attr("reason.value", element.val())
			},

			saveOtherReason: function(context, element, event){
				$.ajax({
					url: "/api/order/" + this.modalCustomerDetails.attr('data._id'),
					type: 'put',
					dataType: 'json',
					data: {
						failure_reason: JSON.stringify({
							reason: this.modalCustomerDetails.attr("data.reason.value"),
							type: 'delivery',
							type2: 'other'
						})
					},
					success: function(data){
						toastr.success("Successfully changed.");
					},
					error: function(xhr, status, error){
						toastr.error("Failed.");
					}
				})
			},

			changeCashCollected: function(context, element, event){
				var cash_collected = parseInt($(element).val());
				var total_cost= this.modalCustomerDetails.attr('data.cost.total');
				var last_cash_collected=this.modalCustomerDetails.attr('data.cash_collected');

				var is_paid=this.modalCustomerDetails.attr('data.is_paid');

				var diff=0;

				var max_allowed=total_cost-1;
				var max_allowed_excess_paid=total_cost+1;

				if(is_paid != 'excess_paid'){
					if(cash_collected >= total_cost ){
						toastr.error("Please Enter Number in cash Collected..\n Max Allowed = " +max_allowed);
						$('#cashCollected').val(max_allowed);
					}
				}

				var cash_collected = parseInt($(element).val());

				this.modalCustomerDetails.attr('data.cash_collected', cash_collected);
				this.saveCashCollected();
			},

			saveCashCollected: function(context, element, event){
				var order_id = $("#all-orders-order-details-modal").attr('index');
				var cash_collected = this.modalCustomerDetails.attr('data.cash_collected');
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


				var all_orders_self = this;
				$.when(item_defer, failure_reason_defer).done(function(item_data, reason_data){

					item_data = item_data[0];
					reason_data = reason_data[0];
					all_orders_self.failureReasons.attr(reason_data.data);
					all_orders_self.nanobar.go(50);
					all_orders_self.cleaningItems.replace(item_data.data);
					item_data.customer_details['status'] = all_orders_self.getStatusDetails(item_data.customer_details['status']).attr('name_id')
					all_orders_self.modalCustomerDetails.attr('data', item_data.customer_details);

					if (!all_orders_self.modalCustomerDetails.attr('data.failure_reason.partial_payment')){
                        all_orders_self.modalCustomerDetails.attr('data.failure_reason.partial_payment', {'type': ''});
                    } else {
                        all_orders_self.modalCustomerDetails.attr('data.failure_reason.partial_payment').attr('type', '');
                    }

                    if(all_orders_self.modalCustomerDetails.attr('data.bag.laundry')){
                        all_orders_self.modalCustomerDetails.attr('data.bag.laundry').each(function(value, index){
                            all_orders_self.selectize['laundry'].addOption({
                                value: value,
                                text: value
                            });
                            all_orders_self.selectize['laundry'].addItem(value, true);
                        })
                    }
                    
                    
                    if (all_orders_self.modalCustomerDetails.attr('data.bag.dryclean')) {
                        var selectize_dryclean = $("#all-orders-modal-others .bag-dryclean")[0].selectize;
                        all_orders_self.modalCustomerDetails.attr('data.bag.dryclean').each(function(value, index){
                            all_orders_self.selectize['dryclean'].addOption({
                                value: value,
                                text: value
                            });
                            all_orders_self.selectize['dryclean'].addItem(value, true);
                        })
                    };
                    
                    if (all_orders_self.modalCustomerDetails.attr('data.bag.iron')) {
                        var selectize_iron = $("#all-orders-modal-others .bag-iron")[0].selectize;
                        all_orders_self.modalCustomerDetails.attr('data.bag.iron').each(function(value, index){
                            all_orders_self.selectize['iron'].addOption({
                                value: value,
                                text: value
                            });
                            all_orders_self.selectize['iron'].addItem(value, true);
                        })
                    };

                    
					var reason_others = true;

					if (all_orders_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason")) {
						all_orders_self.failureReasons.each(function(value, index){
							if (all_orders_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason") == value.attr('str_id')){
								all_orders_self.modalCustomerDetails.attr("data.failure_reason.partial_payment.reason",value.attr('str_id'));
								reason_others = false;
							}
						})
						
						if (reason_others){
							all_orders_self.modalCustomerDetails.attr('data.failure_reason.partial_payment.type', 'others');
						}
					}

					$("#all-orders-order-details-modal").attr('index', index);
					var summernote = $("#all-orders-order-details-modal .summernote");
					summernote.html(all_orders_self.modalCustomerDetails.attr('data.remark'));
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
					    	all_orders_self.modalCustomerDetails.attr('data.remark', $("#all-orders-order-details-modal .summernote").code());
					    }
					});

					$("#all-orders-order-details-modal").modal({
						backdrop: 'static',
						keyboard: false,
						show: true
					});
					all_orders_self.nanobar.go(100);
					$("#all-orders-order-details-modal table").focus();
					all_orders_self._update_total_cost();
					all_orders_self._update_total_quantity();
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
						if(sub_total_cost >= min_order){
							discount = sub_total_cost * discount_amount/100;
						}else{
							discount = 0;
						}
					}else{
						discount = sub_total_cost * discount_amount/100;
					}
					
				}else{
					if (min_order) {
						if(sub_total_cost >= min_order){
							discount = discount_amount;
						}else{
							discount = 0;
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
				var max_discount_amount = $('#all-orders-order-details-modal .modal-discount-max-amount').val() || 0;
				this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
				this._update_total_cost();
			},

			changeDiscount: function(context, element, event){
				var discount_type = $('#all-orders-order-details-modal .modal-discount-type li.active');
				this.applyDiscount(context, discount_type, event);
			},

			changePaymentStatus: function(context, element, event){
				var new_value = $(element).val();

				var order_id = $("#all-orders-order-details-modal").attr('index');
				if (new_value){
					this.modalCustomerDetails.attr("data.is_paid", new_value);
				} else {
					this.modalCustomerDetails.attr("data.is_paid", false);
				}
				
				if (new_value == 'paid') {
					this.modalCustomerDetails.attr('disable_amt',false);
					this.modalCustomerDetails.attr('data.cash_collected',this.allCosts.total_cost);
					this.saveCashCollected();

				}else if(new_value =='not_paid'){
					this.modalCustomerDetails.attr('data.cash_collected',0);
					this.saveCashCollected();
					this.modalCustomerDetails.attr('disable_amt',true);
				}else if(new_value =='partially_paid'){
					this.modalCustomerDetails.attr('data.cash_collected',0);
					this.modalCustomerDetails.attr('disable_amt',false);
				} else if(new_value =='excess_paid'){
					this.modalCustomerDetails.attr('data.cash_collected',0);
				}else{
					this.modalCustomerDetails.attr('data.cash_collected',-1);
					this.modalCustomerDetails.attr('disable_amt',true);
				}

			},

			// saveAllOrderChanges: function(context, element, event){
			// 	var index = $("#all-orders-order-details-modal").attr('index');
			// 	$(element).button('loading');

			// 	var tab=this.modalCustomerDetails.attr("tab_selected");

			// 	var cash_collected = this.modalCustomerDetails.attr('data.cash_collected');

			// 	var reason=this.modalCustomerDetails.attr("failure_reason");

			// 	if(reason == undefined && new_value !='excess_paid'){
			// 		reason=this.modalCustomerDetails.attr("data.failure_reason.delivery.reason");
			// 	}

			// 	var payment_status=this.modalCustomerDetails.attr("data.is_paid");
			// 	if(isNaN(cash_collected)){
			// 		toastr.error("Please Enetr only Number in Cash Collected..");
			// 			$(element).button('reset');
			// 			return;

			// 	}

			// 	var max=this.modalCustomerDetails.attr('data.cost.total');
			// 	var max_allowed_excess_paid=max+1;

			// 	var new_value = this.modalCustomerDetails.attr('data.is_paid');

			// 	if(new_value== "excess_paid"){
			// 		if(cash_collected <= this.modalCustomerDetails.attr('data.cost.total')){
			// 			toastr.error("Please Enter Number in cash Collected..\n Min Allowed = " +max_allowed_excess_paid);
			// 			$('#cashCollected').val(max_allowed_excess_paid);
			// 			$(element).button('reset');
			// 			return;

			// 		}else{
			// 			this.saveCashCollected();
			// 			var total_cost=this.modalCustomerDetails.attr('data.cost.total');
			// 			var cash_collected=this.modalCustomerDetails.attr('data.cash_collected');
			// 		}
			// 	}

			// 	if(payment_status != 'paid' ){
			// 		if(reason=='undefined'  || reason == ""){
			// 			toastr.error("Please select reason..");
			// 			$(element).button('reset');
			// 			return;
			// 		}
			// 	}

			// 	var new_value = this.modalCustomerDetails.attr('data.is_paid');

			// 	if(new_value =='not_paid'){
			// 		this.modalCustomerDetails.attr('disable_amt',true);
			// 	}

			// 	if(reason == 'other'  && new_value !='excess_paid'){
			// 		if(this.modalCustomerDetails.attr("data.reason.value") == "" || this.modalCustomerDetails.attr("data.reason.value") == undefined ){
			// 			toastr.error("Please select reason..");
			// 			$(element).button('reset');
			// 			return;
			// 		}
			// 	}

			// 	if(!this.modalCustomerDetails.attr("data").attr("reason")){
			// 		this.modalCustomerDetails.attr("data").attr("reason", {'type': null, 'value': null});
			// 	}

			// 	var data;
			// 	if(payment_status == 'paid'){
			// 		data={
			// 			is_paid : payment_status,
			// 			cash_collected : cash_collected
			// 		}
			// 	}else if(payment_status=="excess_paid"){
			// 		var total_cost=this.modalCustomerDetails.attr('data.cost.total');
			// 		var cash_collected=this.modalCustomerDetails.attr('data.cash_collected');

			// 		data={
			// 			is_paid:payment_status,
			// 			cash_collected:cash_collected
			// 		}
			// 	}
			// 	else if(reason !="other") {
			// 		data={	
			// 		 	is_paid: payment_status,
			// 			cash_collected : cash_collected,
			// 			failure_reason : JSON.stringify({
			// 				reason: reason,
			// 				type: 'delivery'
			// 			})
			// 		}

			// 	}
			// 	else{
			// 		data={
			// 			is_paid: payment_status,
			// 			cash_collected : cash_collected,
			// 			failure_reason : JSON.stringify({
			// 				reason: this.modalCustomerDetails.attr("data.reason.value"),
			// 				type: 'delivery',
			// 				type2: 'other'

			// 			})
			// 		}
			// 	}


			// 	$.ajax({
			// 		url: "/api/order/" + index,
			// 		type: "put",
			// 		dataType: 'json',
			// 		context: this,
			// 		data:data,
			// 		success: function(data){
			// 			toastr.success("Saved successfully.")
			// 			$(element).button('reset');
			// 		},
			// 		error: function(xhr, status, error){
			// 			toastr.error("Saving unsuccessful. Try again.")
			// 			$(element).button('reset');
			// 		}
			// 	})
			// },

			applyDiscount: function(context, element, event){
				var is_percentage = $(element).hasClass('modal-discount-percentage');
				var discount_amount = $('#all-orders-order-details-modal .modal-discount-amount').val() || 0;

				if (is_percentage) {
					this.modalCustomerDetails.attr("data.discount.percentage", true);
				}else{
					this.modalCustomerDetails.attr("data.discount.percentage", false);
				}
				this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
				this._update_total_cost();
			},

			saveOrderChanges: function(context, element, event){
				var index = $("#all-orders-order-details-modal").attr('index');
				$(element).button('loading');

				var discount_data = this.modalCustomerDetails.attr("data.discount").attr()
				var bags = this.modalCustomerDetails.attr("data.bag").attr() || {}

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
				var order_id = $("#all-orders-order-details-modal").attr('index');
				$.ajax({
					url: "/api/order/" + order_id,
					type: "put",
					dataType: 'json',
					context: this,
					data:{
						status: new_value,
					},
					success: function(data){
						var status_detail = this.getStatusDetails(new_value);
						this.orderData.attr(order_id + ".status", status_detail.formal_name)
						this.orderData.attr(order_id + ".status_color", status_detail.color)
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
				$("#all-orders-order-details-modal .summernote").destroy();
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
			}
		}),

		events: {
			'{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-all-orders" && !this.scope.loaded) {
                    this.scope._pollData(this.scope.orderDate());
                    this.scope._pollDataDeferExec();
                    this.scope.loaded = true;
                };
            },

            '#all-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },

			'inserted': function(){
				var all_orders_self = this;
				var options = {
					format: "yyyy-mm-dd",
					startdate: "2014-10-22",
					autoclose: true,
					todayBtn: true
				}

				$("all-orders-tabs .order-datepicker").datepicker(options)
                .on('changeDate', function(event){
                    var target = event.currentTarget;
                    var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
                    var order_id = $("#all-orders-order-details-modal").attr("index");
                    var formatted_value = selectedDate.format("YYYY/MM/DD");
                    all_orders_self.scope._pollData(selectedDate);
                    all_orders_self.scope._pollDataDeferExec();
                    all_orders_self.scope.attr('variableDate', selectedDate.toDate());
                })
				
				$("#all-orders-order-details-modal .modal-pickup-datepicker").datepicker(options)
				.on('changeDate', function(event){
					var target = event.currentTarget;
					var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
					var order_id = $("#all-orders-order-details-modal").attr("index");
					var formatted_value = selectedDate.format("YYYY/MM/DD");
					$.ajax({
						url: "/api/pickup",
						type: "put",
						dataType: 'json',
						context: all_orders_self,
						data: {
							order_id: order_id,
							date: formatted_value
						},
						success: function(data){
							toastr.success("Date changed.")
							all_orders_self.scope.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", formatted_value)
						},
						error: function(xhr, status, error){
							toastr.error("Date change error.")
						}
					})
					
					all_orders_self.scope.modalCustomerDetails.attr("data.schedules.pickup.schedule_date", selectedDate.format("YYYY/MM/DD"))
				})

				$("#all-orders-order-details-modal .modal-delivery-datepicker").datepicker(options)
				.on('changeDate', function(event){
					var target = event.currentTarget;
					var selectedDate = moment(new Date(Date.parse($(this).datepicker('getDate'))));
					var order_id = $("#all-orders-order-details-modal").attr("index");
					var formatted_value = selectedDate.format("YYYY/MM/DD");
					$.ajax({
						url: "/api/delivery",
						type: "put",
						dataType: 'json',
						context: all_orders_self,
						data: {
							order_id: order_id,
							date: formatted_value
						},
						success: function(data){
							toastr.success("Date changed.")
							all_orders_self.scope.modalCustomerDetails.attr("data.schedules.delivery.schedule_date", formatted_value)
						},
						error: function(xhr, status, error){
							toastr.error("Date change error.")
						}
					})
				})

				var selectize_laundry = $('#all-orders-modal-others .bag-laundry').selectize({
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
                        var item = all_orders_self.scope.modalCustomerDetails.attr('data');
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
                        var item = all_orders_self.scope.modalCustomerDetails.attr('data.bag').attr("laundry");
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
                            url: "/api/order/" + all_orders_self.scope.modalCustomerDetails.attr('data._id'),
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

                var selectize_dryclean = $('#all-orders-modal-others .bag-dryclean').selectize({
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
                        var item = all_orders_self.scope.modalCustomerDetails.attr('data');
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
                        var item = all_orders_self.scope.modalCustomerDetails.attr('data.bag').attr("dryclean");
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
                            url: "/api/order/" + all_orders_self.scope.modalCustomerDetails.attr('data._id'),
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
                
                var selectize_iron = $('#all-orders-modal-others .bag-iron').selectize({
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
                        var item = all_orders_self.scope.modalCustomerDetails.attr('data');
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
                        var item = all_orders_self.scope.modalCustomerDetails.attr('data.bag').attr("iron");
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
                            url: "/api/order/" + all_orders_self.scope.modalCustomerDetails.attr('data._id'),
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

				all_orders_self.scope.selectize = {
                    'laundry': selectize_laundry[0].selectize,
                    'dryclean': selectize_dryclean[0].selectize,
                    'iron': selectize_iron[0].selectize,
                }

			}
		}
	})
})