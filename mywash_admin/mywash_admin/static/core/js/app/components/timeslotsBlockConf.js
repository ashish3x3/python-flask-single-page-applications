define([
	'jquery',
	'can',
	'../../lib/mywash/constructs/map.helpers',
	'../../lib/mywash/components/tabs',
	'nanobar',
	'toastr',
	'datepicker',
	'momentjs',
],function($, can, BaseHelpers, TabsComponents, Nanobar, toastr){
	'use strict';

	var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

	return TabsComponent.extend({
		tag: 'timeslot-block-app',
		template: "",
		scope: TabsComponentScope.extend({
			init: function(){
				var timeslot_self = this;
				this.nanobar = new Nanobar({
					id: 'mybar',
					bg: "#FF6600"
				})
				this.activeEditId = can.compute(0);
				this.order_status = new can.Map({});
                this.timeslots = new can.Map({});
                var timeslots_temp = JSON.parse(localStorage.getItem("timeslots"));
                $.each(timeslots_temp, function(index, value){
                    timeslot_self.timeslots.attr(index, value);
                })
                
			},

			allItems: new can.Map({}),
			loaded: false,
			editingItem: new can.Map({}),
			selectize: {},

            getTimeSlots: function(){
                return this.timeslots;
            },

			getAllItems: function(id) {
				var url = "/api/timeslot";
				if (id)
					url = url + "/" + id;
				var itemsDefer = $.ajax({
					url: url,
					type: 'get',
					dataType: 'json',
					context: this,
					success: function(data){
						this.allItems.attr({}, true)
						this.allItems.attr(data, true);
					}
				});
			},


			addItem: function(context, element, event){
				this.activeEditId(-1);
				$("#timeslot-block-modal").modal('show');
			},

            timeslotRefresh: function(context, element, event) {
				this.getAllItems();
            },

			closeModal: function(context, element, event){
				var timeslotSelf = this;
				this.editingItem.each(function(value, key){
					timeslotSelf.editingItem.attr(key, null);
				})
				this.selectize['type'].clear();
				this.selectize['slots'].clear();
				$("#timeslot-block-modal").modal('hide');
			},

			editItem: function(context, element, event){
				var timeslotSelf = this;
				var index = element.attr('index');
				var defer = $.ajax({
					url: "/api/timeslot/" + index,
					type: "get",
					context: this,
				})

				defer.done(function(data){
					this.activeEditId(index);
					$.each(data.data, function(index, value){
						timeslotSelf.editingItem.attr(index, value);
					});
					timeslotSelf.selectize['type'].addItem(data.data.type);
					$.each(data.data.slots, function(index, value){
						timeslotSelf.selectize['slots'].addItem(value);
					});
					$("#timeslot-block-modal").modal('show');
				})
			},

			saveItem: function(context, element, event){
				self = this;
				var action = element[0]['id'];
				
				var type = null, url = "/api/timeslot";

				if (this.activeEditId() < 0){
					type = 'post';
				} 
				else {
					type = "put";
					url = "/api/timeslot/" + this.activeEditId();
				}
				var blocked_slots = $('#timeslot-block-modal .block-slots').val() || {};
				if (blocked_slots == null) blocked_slots = {}
				$.ajax({
					url: url,
					type: type, 
					dataType: 'json',
					context: this,
					data: {
						date: $('#timeslot-block-modal .block-date').val(),
						type: $('#timeslot-block-modal .block-type').val(),
						slots: JSON.stringify(blocked_slots),
						action: action
					},
					success: function(data){
						toastr.success("Saved successfully.");
						this.getAllItems();							
						this.closeModal(context, element, event);
					}
				})
			},

			

		}),

		events: {
			'{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-configuration" && !this.scope.loaded) {
                    this.scope.getAllItems();
                    this.scope.loaded = true;
                };
            },

            'inserted': function(){
            	var selectize_slots = $('#timeslot-block-modal .block-slots').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: false,
                });

                var selectize_type = $('#timeslot-block-modal .block-type').selectize({
                    persist: false,
                    create: false,
                });

                this.scope.selectize = {
                	'type': selectize_type[0].selectize,
                	'slots': selectize_slots[0].selectize
                }

                var timeslot_self = this;
                var options = {
                    format: "yyyy-mm-dd",
                    startDate: moment().format("YYYY-MM-DD"),
                    autoclose: true,
                    immediateUpdates: true
                }

                $('#timeslot-block-modal .block-date').datepicker(options)
                .on('changeDate', function(event){
                    var selected_date = moment($(this).datepicker('getDate'));
                })
            }
		}

	})

})
