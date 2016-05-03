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
		tag: 'failure-reason-app',
		template: "",
		scope: TabsComponentScope.extend({
			init: function(){
				this.nanobar = new Nanobar({
					id: 'mybar',
					bg: "#FF6600"
				})
				this.activeEditId = can.compute(0);
			},

			allItems: new can.List([]),
			loaded: false,
			editingItem: new can.Map({}),
			selectize: {},

			getAllItems: function(){
				var itemsDefer = $.ajax({
					url: "/api/failurereason",
					type: 'get',
					dataType: 'json',
					context: this,
					success: function(data){
						this.allItems.replace(data.data);
					}
				});
			},

			editItem: function(context, element, event){
				var reasonSelf = this;
				var index = element.attr('index');
				var defer = $.ajax({
					url: "/api/failurereason/" + index,
					type: "get",
					context: this,
				})

				defer.done(function(data){
					this.activeEditId(index);
					$.each(data.data, function(index, value){
						reasonSelf.editingItem.attr(index, value);
					});
					$.each(data.data[0]['type'], function(index, value){
						reasonSelf.selectize['reason'].addItem(value['name']);
					});
					$("#failure-reason-modal").modal('show');
				})

			},

			addItem: function(context, element, event){
				this.activeEditId(-1);
				$("#failure-reason-modal").modal('show');
			},

			closeModal: function(context, element, event){
				var reasonSelf = this;
				this.editingItem.each(function(value, key){
					reasonSelf.editingItem.attr(key, null);
				})
				this.selectize['reason'].clear();
				$("#failure-reason-modal").modal('hide');
			},

			saveItem: function(context, element, event){
				self = this;
				var type = null, url = "/api/failurereason";
				if (this.activeEditId() < 0){
					type = 'post';
				} else {
					type = "put";
					url = "/api/failurereason/" + this.activeEditId();
				}
				var reason_types = $('#failure-reason-modal .reason-type').val();
				$.ajax({
					url: url,
					type: type, 
					dataType: 'json',
					context: this,
					data: {
						reason: $('#failure-reason-modal input[name="reason"]').val(),
						type: JSON.stringify(reason_types),
					},
					success: function(data){
						this.getAllItems();
						this.closeModal(context, element, event);
					}
				})
			}

		}),

		events: {
			'{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-configuration" && !this.scope.loaded) {
                    this.scope.getAllItems();
                    this.scope.loaded = true;
                };
            },

            'inserted': function(){
            	var selectize_reason_type = $('#failure-reason-modal .reason-type').selectize({
                    plugins : ['remove_button'],
                    delimiter: '|',
                    persist: false,
                    create: false,
                });

                this.scope.selectize = {
                	'reason': selectize_reason_type[0].selectize
                }

            }
		}

	})

})