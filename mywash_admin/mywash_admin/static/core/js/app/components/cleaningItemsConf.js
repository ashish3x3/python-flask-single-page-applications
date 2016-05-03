define([
	'jquery',
	'can',
	'../../lib/mywash/constructs/map.helpers',
	'../../lib/mywash/components/tabs',
	'nanobar',
	'toastr',
	'datepicker',
	'momentjs',
	'ajaxForm',
],function($, can, BaseHelpers, TabsComponents, Nanobar, toastr){
	'use strict';

	var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

	return TabsComponent.extend({
		tag: 'cleaning-items-app',
		template: "",
		scope: TabsComponentScope.extend({
			init: function(){
				this.nanobar = new Nanobar({
					id: 'mybar',
					bg: "#FF6600"
				})
				this.activeEditId = can.compute(0);
				var image = new Image();
				image.src = "/static/core/img/items/default.png";
				this.defaultItemImage = can.compute(image);
			},

			allItems: new can.List([]),
			loaded: false,
			editingItem: new can.Map({}),

			getAllItems: function(){
				var itemsDefer = $.ajax({
					url: "/api/items",
					type: 'get',
					dataType: 'json',
					context: this,
				});

				itemsDefer.done(function(data){
					this.allItems.replace(data.items);
				})
			},

			getItemImage: function(){
				return this.defaultItemImage();
			},

			editItem: function(context, element, event){
				var cleaningItemSelf = this;
				var index = element.attr('index');
				var defer = $.ajax({
					url: "/api/items/" + index,
					type: "get",
					context: this,
				})

				defer.done(function(data){
					this.activeEditId(index);
					$.each(data.item, function(index, value){
						cleaningItemSelf.editingItem.attr(index, value);
					})
					var input = $("#item-image-input");
					input.replaceWith(input.val("").clone(true));
					
					var image = new Image();
					image.src = this.editingItem.attr('imageUrl');
					this.defaultItemImage(image);
					$("#cleaning-items-modal").modal('show');
				})

			},

			addItem:  function(context, element, event){
				this.activeEditId(-1);
				var image = new Image();
				image.src = "/static/core/img/items/default.png";
				this.defaultItemImage(image);
				$("#cleaning-items-modal").modal('show');
			},

			closeModal: function(context, element, event){
				var cleaningItemSelf = this;
				this.editingItem.each(function(value, key){
					cleaningItemSelf.editingItem.attr(key, null);
				})
				$("#cleaning-items-modal").modal('hide');
			},

			previewImage: function(context, element, event){
				//console.log(element[0]);
				var oFReader = new FileReader();
				oFReader.readAsDataURL(element[0].files[0]);
				self = this;
				oFReader.onload = function (oFREvent) {
					var image = new Image();
					image.src = oFREvent.target.result;
					self.defaultItemImage(image);
				};
			},

			saveItem: function(context, element, event){
				var cleaningItemSelf = this;
				var type = null, url = "/api/items";
				if (this.activeEditId() < 0){
					type = 'post';
				}else{
					type = "put";
					url += "/" + this.activeEditId()
				}
				//console.log(this.activeEditId(), ".......")

				$("#cleaning-items-modal form").ajaxSubmit({
					url: url,
					type: type,
					dataType: 'json',
					beforeSubmit: function(formData, jqForm, options){
						if (cleaningItemSelf.activeEditId() >= 0)
							formData.push({
								name: "item_id",
								type: "hidden",
								value: cleaningItemSelf.activeEditId(),
							})
					},
					success: function(data){
						cleaningItemSelf.getAllItems();
						toastr.success("Success.")
						cleaningItemSelf.closeModal();
					},
					error: function(){
						toastr.error("Failed.")
					}
				});
			}

		}),

		events: {
			'{can.route} sidebarmenu': function(route){
                if (route.sidebarmenu == "main-content-configuration" && !this.scope.loaded) {
                    this.scope.getAllItems();
                    this.scope.loaded = true;
                };
            },
		}

	})

})