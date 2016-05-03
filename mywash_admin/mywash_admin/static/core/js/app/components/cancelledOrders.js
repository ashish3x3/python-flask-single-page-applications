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
		tag: 'cancel-tabs',
		template: '',
		scope: TabsComponentScope.extend({
			init: function(){
				var cancelled_self = this;
				var now = moment();
				this.order_status = new can.Map({});
				this.timeslots = new can.Map({})
				this.datepickers_initialised = false;
				this.poll_skip = 0;
				this.poll_limit = 20;
				this.last_action = null;
				this.total_quantity = can.compute(0);

				this.search_skip = 0;
				this.search_limit = 20;

				this.nanobar = new Nanobar({
					id: 'mybar',
					bg: "#FF6600"
				})
				
				var statuses = JSON.parse(localStorage.getItem("statuses"));
				$.each(statuses, function(index, value){
					cancelled_self.order_status.attr(index, value);
				})
				
				var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
				$.each(timeslots_temp, function(index, value){
					cancelled_self.timeslots.attr(index, value);
				})
			},

			orderData: new can.List([]),
			loaded: false,

			cleaningItems: new can.List([]),
			modalCustomerDetails: new can.Map({}),
			allCosts: new can.Map({}),

			variableDate: new Date(),
			orderDate: can.compute(function(){
				return this.attr('variableDate');
			}),

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

			selectSearchOption: function(context, element, event) {
				var input = $(element).parents(".input-group").find(".search-input");
				var type = $(element).attr('data-option');
				if (type == "name") input.val("name:");
				else if (type == "email") input.val("email:");
				else if (type == "phone") input.val("phone:");
				else if (type == "oid") input.val("oid:");
				input.focus();
			},


			getStatusDetails: function(item){
				var credible_status = null, return_status = null;
				if (item == 1) credible_status = 'order_placed';
				else if(item == 2) credible_status = 'pickup_complete';
				else if(item == 3) credible_status = 'delivery_ready';
				else if(item == 4) credible_status = 'clothes_delivered';
				else if(item == 5) credible_status = 'order_cancelled';
				else if(item == 6) credible_status = 'order_rejected';
				else credible_status = item;

				while(true){
					var order_status_length = $.map(this.order_status.attr(), function(n, i) { return i; }).length;
					if (order_status_length) break;
				}

				this.order_status.each(function(group, key){
					group.status.each(function(status, inner_key){
						if (status.name_id == credible_status) {
							status['color'] = group.color;
							return_status = status;
						}
					})
				});
				return return_status;
			},


			captureEnterKey: function(context, element, event) {
				if (event.keyCode == 13) $("cancel-tabs .btn-search-go").trigger('click');
			},

			searchOrders: function(context, element, event) {
				this._searchOrders(0, this.search_limit);
				this._searchOrdersDeferred();
			},

			_searchOrders: function(skip, limit) {
				var search_term = $.trim($("cancel-tabs .search-input").val());
				if(search_term == ""){
					$("cancel-tabs .btn-refresh").trigger('click');
					return;
				}

				skip = typeof skip == 'undefined'? this.search_skip : skip;
				limit = typeof limit == 'undefined'? this.search_limit : limit;
				this.nanobar.go(30);
				this.cancelled_search_defer = $.ajax({
					url: "/api/order/search/cancelled/" + search_term + "/" + skip + "/" + limit,
					type: 'get',
					dataType: 'json',
					context: this,
				})
			},

			_searchOrdersDeferred: function(replace) {
				if (typeof replace == 'undefined') replace = true;

				this.cancelled_search_defer.done(function(data){
					var cancel_self = this;
					this.nanobar.go(50);
					if (replace)
						this.orderData.replace([]);

					var insert_data = [];
					$.each(data.data, function(index, value){
						var status_details = cancel_self.getStatusDetails(value['status']);
						value['status'] = status_details.formal_name;
						value['status_color'] = status_details.color;
						insert_data.push(value);
					})
					this.orderData.replace(insert_data);

					this.search_skip += data.data.length;
					this.nanobar.go(100);
					this.last_action = "search"
					if (!replace)
						$("cancel-tabs .block-load-more").find(".fa-repeat").removeClass("fa-spin");
				})

				this.cancelled_search_defer.fail(function(xhr, status, error){
					this.nanobar.go(100);
					toastr.error("Proper search criteria not used.")
				})
			},

			orderRefresh: function(context, element, event) {
				this._pollData(0, this.poll_skip);
				this._pollDataDeferExec(true);
				$("cancel-tabs .block-load-more").show()
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
						var cancel_self = this;
						$.each(data.data, function(index, value){
							var status_details = cancel_self.getStatusDetails(value['status']);
							value['status'] = status_details.formal_name;
							value['status_color'] = status_details.color;
							cancel_self.orderData.push(value);
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
					url: "/api/cancelled/" + skip + "/" + limit,
					type: 'get',
					context: this,
					dataType: 'json',
				});
			},

			// Success part for _pollData ajax call
			_pollDataDeferExec: function(replace){
				if (typeof replace == 'undefined') replace = false;
				var cancel_self = this;
				can.when(this._pollDataDefer).then(function(data){
					this.nanobar.go(50);
					if (!data.data){
						this.nanobar.go(100);
						return false;
					}

					if (!replace){
						$.each(data.data, function(index, value){
							var status_details = cancel_self.getStatusDetails(value['status']);
							value['status'] = status_details.formal_name;
							value['status_color'] = status_details.color;
							value['user_info']['name'] = value['user_info']['name'].trim();
							cancel_self.orderData.push(value);
						})
						this.poll_skip = this.poll_skip + data.data.length;
					}
					else{
						var insert_data = [];
						$.each(data.data, function(index, value){
							var status_details = cancel_self.getStatusDetails(value['status']);
							value['status'] = status_details.formal_name;
							value['status_color'] = status_details.color;
							value['user_info']['name'] = value['user_info']['name'].trim();
							insert_data.push(value);
						})
						this.orderData.replace(insert_data);
						this.poll_skip = data.data.length;
					}
					cancel_self.nanobar.go(100);
					cancel_self.last_action = "query"
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

					item.attr('final_cost', laundry + dryclean + iron);
				}
				this._update_total_cost();
				this._update_total_quantity();
			},

			openOrderModal: function(context, element, event){
				var cancel_self = this;
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
					var cancel_self = this;
					this.nanobar.go(50);
					this.cleaningItems.replace(data.data);
					data.customer_details['status'] = this.getStatusDetails(data.customer_details['status']).attr('name_id')
					this.modalCustomerDetails.attr('data', data.customer_details);
					$("#cancel-order-details-modal").attr('index', index);
					var summernote = $("#cancel-order-details-modal .summernote");
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
					    	cancel_self.modalCustomerDetails.attr('data.remark', $("#cancel-order-details-modal .summernote").code());
					    }
					});

					$("#cancel-order-details-modal").modal({
						backdrop: 'static',
						keyboard: false,
						show: true
					});
					this.nanobar.go(100);
					$("#cancel-order-details-modal table").focus();
					this._update_total_cost();
					this._update_total_quantity();
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

				this.allCosts.attr('total_cost', Math.round(total_cost));
			},

			changeMaxDiscount: function(context, element, event){
				var max_discount_amount = $('#cancel-order-details-modal .modal-discount-max-amount').val() || 0;
				this.modalCustomerDetails.attr("data.discount.max", max_discount_amount);
				this._update_total_cost();
			},

			changeDiscount: function(context, element, event){
				var discount_type = $('#cancel-order-details-modal .modal-discount-type li.active');
				this.applyDiscount(context, discount_type, event);
			},

			changePaymentStatus: function(context, element, event){
				var new_value = $(element).val();
				var order_id = $("#cancel-order-details-modal").attr('index');
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
				var discount_amount = $('#cancel-order-details-modal .modal-discount-amount').val() || 0;

				if (is_percentage) {
					this.modalCustomerDetails.attr("data.discount.percentage", true);
				}else{
					this.modalCustomerDetails.attr("data.discount.percentage", false);
				}
				this.modalCustomerDetails.attr("data.discount.amount", discount_amount);
				this._update_total_cost();
			},

			saveOrderChanges: function(context, element, event){
				self = this;
				var index = $("#cancel-order-details-modal").attr('index');
				$(element).button('loading');

				var discount_data = self.modalCustomerDetails.attr("data.discount").attr()
				var bags = this.modalCustomerDetails.attr("data.bag").attr() || {}

				$.ajax({
					url: "/api/orderitem/" + index,
					type: "post",
					data: {
						data: JSON.stringify(self.cleaningItems.attr()),
						remark: self.modalCustomerDetails.attr('data.remark'),
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
				var order_id = $("#cancel-order-details-modal").attr('index');
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
				$("#cancel-order-details-modal .summernote").destroy();
				if (this.last_action == 'query')
					$("cancel-tabs .btn-refresh").trigger('click');
				else
					$("cancel-tabs .btn-search-go").trigger('click');
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
                if (route.sidebarmenu == "main-content-cancelled" && !this.scope.loaded) {
                    this.scope._pollData();
					this.scope._pollDataDeferExec();
                    this.scope.loaded = true;
                };
            },

            '#cancelled-orders .openOrderModal click': function(element, event){
                this.scope.openOrderModal(null, element, event);
            },
		}
	})
})