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
		tag: 'package-tabs',
		template: '',
		scope: TabsComponentScope.extend({
			init: function(){
				var package_self = this;
				var now = moment();
				this.order_status = new can.Map({});
				this.timeslots = new can.Map({})
				this.datepickers_initialised = false;
				this.poll_skip = 0;
				this.poll_limit = 20;
				this.last_action = null;
				this.total_quantity = can.compute(0);
				this.row_count = can.compute(0);
				
				this.invoice_now = can.compute(moment());
				this.currentInvoiceIndex = can.compute(0),

				this.search_skip = 0;
				this.search_limit = 20;

				this.nanobar = new Nanobar({
					id: 'mybar',
					bg: "#FF6600"
				})

				var statuses = JSON.parse(localStorage.getItem("statuses"));
				$.each(statuses, function(index, value){
					package_self.order_status.attr(index, value);
				})
				
				var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
				$.each(timeslots_temp, function(index, value){
					package_self.timeslots.attr(index, value);
				})
				
			},

			orderData: new can.Map({}),
			selectize: {},
			loaded: false,

			cleaningItems: new can.List([]),
			modalCustomerDetails: new can.Map({}),
			allCosts: new can.Map({}),

			invoiceStore: new can.List([]),

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

			getCurrentDate: function(){
				return this.getFormattedDate(this.invoice_now());
			},

			getCurrentInvoiceIndex: function(){
				return this.currentInvoiceIndex();
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

			_editOrderData: function(match, update){
				var order = this.orderData.attr(match['value']);
				if (order) {
					if (order.attr(match['key']) == match['value']) {
						order.attr(update['key'], update['value']);
					};
				};
			},

			captureEnterKey: function(context, element, event) {
				if (event.keyCode == 13) $("package-tabs .btn-search-go").trigger('click');
			},

			searchOrders: function(context, element, event) {
				this._searchOrders(0, this.search_limit);
				this._searchOrdersDeferred();
			},

			_searchOrders: function(skip, limit) {
				var search_term = $.trim($("package-tabs .search-input").val());
				if(search_term == ""){
					$("package-tabs .btn-refresh").trigger('click');
					return;
				}
				skip = typeof skip == 'undefined'? this.search_skip : skip;
				limit = typeof limit == 'undefined'? this.search_limit : limit;
				this.nanobar.go(30);
				this.package_search_defer = $.ajax({
					url: "/api/order/search/package/" + search_term + "/" + skip + "/" + limit,
					type: 'get',
					dataType: 'json',
					context: this,
				})
			},

			_searchOrdersDeferred: function(update) {
				if (typeof update == 'undefined') update = true;
				can.when(this.package_search_defer).then(function(data){
					var package_self = this;
					this.nanobar.go(50);
					if (update)
						this.orderData.attr({}, true);

					var insert_data = {};
					$.each(data.data, function(index, value){
						var status_details = package_self.getStatusDetails(value['status']);
						value['status'] = status_details.formal_name;
						value['status_color'] = status_details.color;
						value['delivery_date'] = value['delivery_data']['schedule_date'];
						value['user_info']['name'] = value['user_info']['name'].trim();
						delete(value['delivery_data']);
						delete(value['pickup_data']);
						insert_data[value.order_id] = value;
					})
					this.orderData.attr(insert_data, true);
					this.search_skip += data.data.length;
					this.nanobar.go(100);
					this.last_action = "search"
					// if (!udpate)
					// 	$("package-tabs .block-load-more").find(".fa-repeat").removeClass("fa-spin");
				})

				this.package_search_defer.fail(function(xhr, status, error){
					this.nanobar.go(100);
					toastr.error("Proper search criteria not used.")
				})
			},


			orderRefresh: function(context, element, event) {
				this._pollData(0, this.poll_skip);
				this._pollDataDeferExec(true);
				// $("package-tabs .block-load-more").show()
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
						var package_self = this;
						var insert_map = {}
						$.each(data.data, function(index, value){
							var status_details = package_self.getStatusDetails(value['status']);
							value['status'] = status_details.formal_name;
							value['status_color'] = status_details.color;
							value['delivery_date'] = value['delivery_data']['schedule_date'];
							value['user_info']['name'] = value['user_info']['name'].trim();
							delete(value['delivery_data']);
							delete(value['pickup_data']);
							insert_map[value.order_id] = value
							
						})
						this.orderData.attr(insert_map)
						// $.each(data.data, function(index, value){
						// 	package_self.orderData.push(value);
						// })
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
					url: "/api/package/" + skip + "/" + limit,
					type: 'get',
					context: this,
					dataType: 'json',
				});
			},

			_updateData: function(data){
				//console.log("update data = "+data.data);  // we are getting 88 here
				this.row_count(data.length);
				var package_self = this, remove_list = [];
				var received_data = {}, delete_keys = [];
				$.each(data, function(index, value){
					received_data[value.order_id] = value;
				})

				$.each(received_data, function(key, value){
					var order = package_self.orderData.attr(key);
					var status_details = package_self.getStatusDetails(value['status']);
					value['status'] = status_details.formal_name;
					value['status_color'] = status_details.color;
					value['user_info']['name'] = value['user_info']['name'].trim();
					value['delivery_date'] = value['delivery_data']['schedule_date'];
					value['user_info']['name'] = value['user_info']['name'].trim();
					delete(value['delivery_data']);
					delete(value['pickup_data']);
					if (order) {
						if (order.attr('status') != value.status)
							order.attr('status', value.status);
						if (order.attr('total_price') != value.total_price)
							order.attr('total_price', value.total_price);
						if (order.attr('invoice_printed') != value.invoice_printed)
							order.attr('invoice_printed', value.invoice_printed);
						if (order.attr('racks').attr().length != value.racks.length) {
							order.attr('racks', value.racks);
						} else {
							var rack_changed = false;
							$.each(value.racks, function(index, value){
								if(order.attr('racks.laundry')){
									if(order.attr('racks.laundry').indexOf(value) == -1)
										rack_changed = true;
								}
								if(order.attr('racks.dryclean')){
									if(order.attr('racks.dryclean').indexOf(value) == -1)
										rack_changed = true;
								}
								if(order.attr('racks.iron')){
									if(order.attr('racks.iron').indexOf(value) == -1)
										rack_changed = true;
								}
								
							})
							if (rack_changed)
								order.attr('racks', value.racks);
						}
						
					}else{
						package_self.orderData.attr(value.order_id, value);
					}
				})

				// Collect obsolete
				this.orderData.each(function(value, key){
					if (!received_data[key])
						delete_keys.push(key);
				});

				// Delete keys
				$.each(delete_keys, function(index, value){
					package_self.orderData.removeAttr(value);
				})
			},

			// Success part for _pollData ajax call
			_pollDataDeferExec: function(update){
				if (typeof update == 'undefined') update = false;
				var package_self = this;
				this._pollDataDefer.done(function(data){
					this.nanobar.go(50);
					if (!data.data){
						this.nanobar.go(100);
						return false;
					}
					var insert_map = {};
					if (!update){
						this.row_count(data.item_count);
						$.each(data.data, function(index, value){
							var status_details = package_self.getStatusDetails(value['status']);
							value['status'] = status_details.formal_name;
							value['status_color'] = status_details.color;
							value['delivery_date'] = value['delivery_data']['schedule_date'];
							value['user_info']['name'] = value['user_info']['name'].trim();
							delete(value['delivery_data']);
							delete(value['pickup_data']);
							insert_map[value.order_id] = value
						})
						this.orderData.attr(insert_map, true);
						this.poll_skip = this.poll_skip + data.data.length;
					}
					else{
						this._updateData(data.data)
						this.poll_skip = data.data.length;
					}
					this.nanobar.go(100);
					this.last_action = "query"
				})
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
					}else if(!item.attr('quantity.iron')){
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

				item_defer.done(function(data){
					var package_self = this;
					this.nanobar.go(50);

					data.customer_details['status'] = this.getStatusDetails(data.customer_details['status']).attr('name_id');
					this.modalCustomerDetails.attr('data', data.customer_details);

					var disable_discount_edit = false;
					if (!this.modalCustomerDetails.attr('data.coupon.name')){
						disable_discount_edit = moment(this.modalCustomerDetails.attr('data.created_date')).format("YYYY-MM-DD") >= "2015-11-30";
					}else{
						disable_discount_edit = true;
					}
					this.modalCustomerDetails.attr('data').attr('disable_discount_edit', disable_discount_edit);
					
					var service_type = this.modalCustomerDetails.attr('data.service_type');
					this.cleaningItems.replace(data.data);
					
					if (this.modalCustomerDetails.attr('data.racks.laundry')) {
                        this.modalCustomerDetails.attr('data.racks.laundry').each(function(value, index){
                            package_self.selectize['rack_laundry'].addOption({
                            	value: value,
                            	text: value
                            });
                            package_self.selectize['rack_laundry'].addItem(value, true);
                        })
                    };

                    if (this.modalCustomerDetails.attr('data.racks.dryclean')) {
                        this.modalCustomerDetails.attr('data.racks.dryclean').each(function(value, index){
                            package_self.selectize['rack_dryclean'].addOption({
                            	value: value,
                            	text: value
                            });
                            package_self.selectize['rack_dryclean'].addItem(value, true);
                        })
                    };

                    if (this.modalCustomerDetails.attr('data.racks.iron')) {
                        this.modalCustomerDetails.attr('data.racks.iron').each(function(value, index){
                            package_self.selectize['rack_iron'].addOption({
                            	value: value,
                            	text: value
                            });
                            package_self.selectize['rack_iron'].addItem(value, true);
                        })
                    };

					$("#package-order-details-modal").attr('index', index);
					var summernote = $("#package-order-details-modal .summernote");
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
					    	package_self.modalCustomerDetails.attr('data.remark', $("#package-order-details-modal .summernote").code());
					    }
					});

					$("#package-order-details-modal").modal({
						backdrop: 'static',
						keyboard: false,
						show: true
					});
					this.nanobar.go(100);
					$("#package-order-details-modal table").focus();
					this._update_total_cost();
					this._update_total_quantity();
				})

			},

			_get_sub_total_cost: function(invoice){
				if (typeof invoice == 'undefined') invoice = false;
				var total_cost = 0;
				var service_type = this.modalCustomerDetails.attr('data.service_type');
				this.cleaningItems.each(function(element, index){
					var item = element, laundry, dryclean, iron;
					laundry = (item.attr('quantity.laundry') * item.attr('price.laundry')) || 0;
					dryclean = (item.attr('quantity.dryclean') * item.attr('price.dry_cleaning')) || 0;
					iron = (item.attr('quantity.iron') * item.attr('price.iron')) || 0;
					total_cost += laundry + dryclean + iron;
				});
				if (service_type == 'express' && !invoice) return total_cost * 2;
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
			
			_update_total_cost: function(invoice){
				var sub_total_cost = this._get_sub_total_cost(invoice), discount = null;
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
				var max_discount_amount = $('#package-order-details-modal .modal-discount-max-amount').val() || 0;
				this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
				this._update_total_cost();
			},

			changeDiscount: function(context, element, event){
				var discount_type = $('#package-order-details-modal .modal-discount-type li.active');
				this.applyDiscount(context, discount_type, event);
			},

			applyDiscount: function(context, element, event){
				var sub_total_cost = this._get_sub_total_cost()
				var is_percentage = $(element).hasClass('modal-discount-percentage');
				var discount_amount = $('#package-order-details-modal .modal-discount-amount').val() || 0;

				if (is_percentage) {
					this.modalCustomerDetails.attr("data.discount.percentage", true);
					if (discount_amount > 100)
						discount_amount = 0;
				}else{
					this.modalCustomerDetails.attr("data.discount.percentage", false);
					if (discount_amount > sub_total_cost)
						discount_amount = 0;
				}
				this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
				this._update_total_cost();
			},

			saveOrderChanges: function(context, element, event){
				self = this;
				var index = $("#package-order-details-modal").attr('index');
				$(element).button('loading');

				var discount_data = self.modalCustomerDetails.attr("data.discount").attr()

				$.ajax({
					url: "/api/orderitem/" + index,
					type: "post",
					data: {
						data: JSON.stringify(self.cleaningItems.attr()),
						remark: self.modalCustomerDetails.attr('data.remark'),
						discount: JSON.stringify(discount_data),
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
				var order_id = $("#package-order-details-modal").attr('index');
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
					},
					error: function(xhr, status, error){
						toastr.error("Status change failed.")
					}
				})
			},

			closeModal: function(context, element, event){
				$("#package-order-details-modal .summernote").destroy();
				if (this.last_action == 'query')
					$("package-tabs .btn-refresh").trigger('click');
				else
					$("package-tabs .btn-search-go").trigger('click');
				this.selectize['rack_laundry'].clear(true)
				this.selectize['rack_laundry'].clearOptions()
				this.selectize['rack_dryclean'].clear(true)
				this.selectize['rack_dryclean'].clearOptions()
				this.selectize['rack_iron'].clear(true)
				this.selectize['rack_iron'].clearOptions()
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

			__invoiceDirectionShowHide: function(){
				if (this.invoiceStore[this.currentInvoiceIndex() - 1]) {
					$("#package-invoice-modal .direction-left").prop({'disabled':false});
				}else{
					$("#package-invoice-modal .direction-left").prop({'disabled':true});
				}

				if (this.invoiceStore[this.currentInvoiceIndex() + 1]) {
					$("#package-invoice-modal .direction-right").prop({'disabled':false});
				}else{
					$("#package-invoice-modal .direction-right").prop({'disabled':true});
				}
			},

			showInvoice: function(context, element, event){
				var datepicker_options = {
					format: "yyyy-mm-dd",
					startdate: "2014-10-22",
					autoclose: true,
					todayBtn: true
				}

				// Reset to today's date
				this.invoice_now(moment());

				// Initialize the datepickers in the invoice
				var invoice_date = $("#package-invoice-modal .invoice-date");
				if (!invoice_date.hasClass("datepicker-initialized")) {
					$(invoice_date).addClass("datepicker-initialized")
					$(invoice_date).datepicker(datepicker_options).on('changeDate', function(event){
						var selectedDate = moment(new Date(Date.parse($(invoice_date).datepicker('getDate'))));
						package_self.now(selectedDate);
					});
				};

				var due_date = $("#package-invoice-modal .invoice-due-date");
				if (!due_date.hasClass("datepicker-initialized")) {
					$(due_date).addClass("datepicker-initialized")
					$(due_date).datepicker(datepicker_options).on('changeDate', function(event){
						var selectedDate = moment(new Date(Date.parse($(due_date).datepicker('getDate'))));
						package_self.modalCustomerDetails.attr('data.schedules.delivery.schedule_date', selectedDate.format("YYYY/MM/DD"));
					});
				};

				
				var data = [];
				var rows = $(".package-checkbox.btn-success").parents("tr");
				$.each(rows, function(index, value){
					data.push($(value).attr('index'));
				})

				this.invoiceStore.replace(data)
				if (rows.length) {
					this._update_print_data(this.invoiceStore[0]);
					this.currentInvoiceIndex(0);
					$("#package-invoice-modal").modal({
						backdrop: 'static',
						keyboard: false,
						show: true
					})
					this.__invoiceDirectionShowHide();
				}else{
					toastr.warning("Select an order first.")
				}

			},

			nextInvoice: function(context, element, event){
				var index = this.currentInvoiceIndex();
				this.currentInvoiceIndex(++index)
				this._update_print_data(this.invoiceStore[this.currentInvoiceIndex()]);
				this.__invoiceDirectionShowHide();
			},

			prevInvoice: function(context, element, event){
				var index = this.currentInvoiceIndex();
				this.currentInvoiceIndex(--index)
				this._update_print_data(this.invoiceStore[this.currentInvoiceIndex()]);
				this.__invoiceDirectionShowHide();
			},

			sendInvoice: function(context, element, event){
				var order_id = this.invoiceStore[this.currentInvoiceIndex()];
				$.ajax({
					url: "/api/invoice/send",
					type: 'post',
					context: this,
					data: {
						order_id: order_id
					},
					success: function(data){
						toastr.success("Sent successfully.")
					},
					error: function(xhr, status, error){
						toastr.error(xhr.responseJSON['error'])
					}
				})
			},
			
			saveInvoice: function(context, element, event){
				var order_id = this.invoiceStore[this.currentInvoiceIndex()];

				$(element).button("load");
				$.ajax({
					url: "/api/saveinvoice/" + order_id,
					type: 'post',
					success: function(data){
						toastr.success("Invoice saved.")
						$(element).button("reset");
					},
					error: function(xhr, status, error){
						toastr.error("Invoice not saved.")
						$(element).button("reset");
					}
				})
			},

			printInvoice: function(context, element, event){
				window.print();
				$.ajax({
					url: "/api/order/" + this.invoiceStore[this.currentInvoiceIndex()],
					type: 'put',
					dataType: 'json',
					context: this,
					data: {
						invoice_printed: true
					},
					success: function(data){
						this._editOrderData(
							{
								'key': 'order_id',
								'value': this.invoiceStore[this.currentInvoiceIndex()]
							},
							{
								'key': 'invoice_printed',
								'value': true
							}
						)
						this.saveInvoice()
					}
				})
			},


			addInvoiceRow: function(context, element, event){
				var a = $("#package-invoice-modal tbody tr:first").clone()[0];
				$(a).removeAttr('style').addClass("addedRow");
				var temp_row = $("<div>").append(a);
				var template = can.mustache(temp_row.html());
				var frag = template({
					removeInvoiceRow: this.removeInvoiceRow
				})
				$("#package-invoice-modal tbody").append(frag);
			},

			removeInvoiceRow: function(context, element, event){
				$(element).parents('tr').remove();
			},

			_update_print_data: function(index){
				var defer = $.ajax({
					url: "/api/orderitem/" + index,
					type: 'get',
					context: this,
					dataType: 'json',
				})

				defer.done(function(data){
					this.modalCustomerDetails.attr('data', data.customer_details);
					var service_type = this.modalCustomerDetails.attr('data.service_type');

					if (service_type == 'express') {
						$.each(data.data, function (key, value) {
							if (!isNaN(value['price']['laundry']))
								value['price']['laundry'] *= 2;
							if (!isNaN(value['price']['dryclean']))
								value['price']['dryclean'] *= 2;
							if (!isNaN(value['price']['iron']))
								value['price']['iron'] *= 2;
						})
					};
					this.cleaningItems.replace(data.data);
					this._update_total_cost();
				})
			},

			closeInvoice: function(context, element, event){
				$("#package-invoice-modal .items-list .addedRow").remove();
			},

		}),

		helpers: $.extend(BaseHelpers, {
			multiply: function(a, b, options){
				return a() * b();
			},
		}),

		events: {
			'{can.route} sidebarmenu': function(route){
				if (route.sidebarmenu == "main-content-package" && !this.scope.loaded) {
					this.scope._pollData();
					this.scope._pollDataDeferExec();
					this.scope.loaded = true;
				};
			},

			'#package-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },

			'inserted': function(){
				var package_self = this;
				
				//------------------------- SELECTIZE RACK LAUNDRY ------------------------------
                var selectize_rack_laundry = $('#package-modal-others .rack-laundry').selectize({
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
                    	if (isNaN(parseInt(value))){
                    		var selectize = this.$input[0].selectize;
                    		selectize.removeItem(value, true);
                    	}
                        var item = package_self.scope.modalCustomerDetails.attr('data');
                        if(typeof item.attr("racks") == 'undefined'){
                            item.attr("racks", {});
                        }

                        if(typeof item.attr("racks.laundry") == 'undefined'){
                            item.attr("racks.laundry", []);
                        }

                        if(item.attr('racks.laundry').indexOf(value) == -1)
                            item.attr('racks.laundry').push(value);
                    },

                    onItemRemove: function(value){
                        var item = package_self.scope.modalCustomerDetails.attr('data.racks.laundry');
                        var index = item.indexOf(value);
                        item.removeAttr(index);
                    },

                    onChange: function(value){
                    	value = value.trim()
                    	var racks = []
                    	if (value.length) {
                    		racks = value.split('|');
                    	}
                        var rackIsNaN = false;
                        $.each(racks, function(index, value2){
                        	var trim_val = value2.trim();
                        	if (trim_val.length){
                        		if (isNaN(parseInt(value2))) rackIsNaN = true;
                        	}
                        })

                        if (rackIsNaN){
                        	toastr.error("Rack must be a number.");
                        	return false;
                        }
                        $.ajax({
                            url: "/api/order/" + package_self.scope.modalCustomerDetails.attr('data._id'),
                            type: 'put',
                            dataType: 'json',
                            data: {
                                racks: JSON.stringify({
                                	type: 'laundry',
                                	racks: racks
                                })
                            },
                            success: function(data){
                                
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })
                    }

                });

				//------------------------- SELECTIZE RACK LAUNDRY ------------------------------
                var selectize_rack_dryclean = $('#package-modal-others .rack-dryclean').selectize({
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
                    	if (isNaN(parseInt(value))){
                    		var selectize = this.$input[0].selectize;
                    		selectize.removeItem(value, true);
                    	}
                        var item = package_self.scope.modalCustomerDetails.attr('data');
                        if(typeof item.attr("racks") == 'undefined'){
                            item.attr("racks", {});
                        }

                        if(typeof item.attr("racks.dryclean") == 'undefined'){
                            item.attr("racks.dryclean", []);
                        }

                        if(item.attr('racks.dryclean').indexOf(value) == -1)
                            item.attr('racks.dryclean').push(value);
                    },

                    onItemRemove: function(value){
                        var item = package_self.scope.modalCustomerDetails.attr('data.racks.dryclean');
                        var index = item.indexOf(value);
                        item.removeAttr(index);
                    },

                    onChange: function(value){
                        value = value.trim()
                    	var racks = []
                    	if (value.length) {
                    		racks = value.split('|');
                    	}
                        var rackIsNaN = false;
                        
                        $.each(racks, function(index, value2){
                        	var trim_val = value2.trim();
                        	if (trim_val.length){
                        		if (isNaN(parseInt(value2))) rackIsNaN = true;
                        	}
                        })

                        if (rackIsNaN){
                        	toastr.error("Rack must be a number.");
                        	return false;
                        }
                        $.ajax({
                            url: "/api/order/" + package_self.scope.modalCustomerDetails.attr('data._id'),
                            type: 'put',
                            dataType: 'json',
                            data: {
                            	racks: JSON.stringify({
                                	type: 'dryclean',
                                	racks: racks
                                })
                            },
                            success: function(data){
                                
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })
                    }

                });

				//------------------------- SELECTIZE RACK LAUNDRY ------------------------------
                var selectize_rack_iron = $('#package-modal-others .rack-iron').selectize({
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
                    	if (isNaN(parseInt(value))){
                    		var selectize = this.$input[0].selectize;
                    		selectize.removeItem(value, true);
                    	}
                        var item = package_self.scope.modalCustomerDetails.attr('data');
                        if(typeof item.attr("racks") == 'undefined'){
                            item.attr("racks", {});
                        }

                        if(typeof item.attr("racks.iron") == 'undefined'){
                            item.attr("racks.iron", []);
                        }

                        if(item.attr('racks.iron').indexOf(value) == -1)
                            item.attr('racks.iron').push(value);
                    },

                    onItemRemove: function(value){
                        var item = package_self.scope.modalCustomerDetails.attr('data.racks.iron');
                        var index = item.indexOf(value);
                        item.removeAttr(index);
                    },

                    onChange: function(value){
                    	value = value.trim()
                    	var racks = []
                    	if (value.length) {
                    		racks = value.split('|');
                    	}
                        var rackIsNaN = false;
                        
                        $.each(racks, function(index, value2){
                        	var trim_val = value2.trim();
                        	if (trim_val.length){
                        		if (isNaN(parseInt(value2))) rackIsNaN = true;
                        	}
                        })

                        if (rackIsNaN){
                        	toastr.error("Rack must be a number.");
                        	return false;
                        }
                        $.ajax({
                            url: "/api/order/" + package_self.scope.modalCustomerDetails.attr('data._id'),
                            type: 'put',
                            dataType: 'json',
                            data: {
                            	racks: JSON.stringify({
                                	type: 'iron',
                                	racks: racks
                                })
                            },
                            success: function(data){
                                
                            },
                            error: function(xhr){
                                toastr.error(xhr.responseJSON.error);
                            }
                        })
                    }

                });
				
				package_self.scope.selectize = {
                    'rack_laundry': selectize_rack_laundry[0].selectize,
                    'rack_dryclean': selectize_rack_dryclean[0].selectize,
                    'rack_iron': selectize_rack_iron[0].selectize,
                }

			}
		}
	})
})