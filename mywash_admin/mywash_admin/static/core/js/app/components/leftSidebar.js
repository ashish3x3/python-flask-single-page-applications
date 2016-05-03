define([
	'jquery',
	'can',
	'../../lib/mywash/constructs/map.helpers',
],function($, can, BaseHelpers){
	'use strict';

	return can.Component.extend({},{
		tag: 'left-sidebar',
		template: '',
		scope: {
			init: function(){
                can.route.bind(this.bindRoute, this.tabchangeevent);
            },

			bindRoute: 'sidebarmenu',

			sidebarMenuItems: [
				{
					iconClass: "fa-dashboard",
					name: "dashboard"
				},
				{
					iconClass: "fa-laptop",
					name: 'orders',
					submenu: [
						{ name: 'all', pane_href: "all-orders"},
						{ name: 'pickup'},
						{ name: 'tagging'},
						{ name: 'packaging/Invoicing', pane_href: "package"},
						{ name: 'delivery'},
						{ name: 'delivery progress (OFD)', pane_href: "ofd"},
						{ name: 'completed'},
						{ name: 'canceled/Rejected', pane_href: "cancelled"},
					]
				},
				{
					iconClass: "fa-cogs",
					name: "configuration",
				},
				{
					iconClass: "fa-user",
					name: "users",
				},
				{
					iconClass: "fa-user",
					name: "vendors",
				},
				{
					iconClass: "fa-plane",
					name: 'logistics',
					submenu: [
						{ name: 'staffs', pane_href: "logistic-staffs"},
					]
				},
			],

			tabchangeevent: function(context, newValue){
                var elements = $('#nav-accordion').find("a");
                elements.each(function(){
                    var href = $(this).attr('href').substr(1);
                    if (href.substr(0, 12) == "main-content") {
                    	if (href === newValue) {
                        	$(this).parent().addClass("active");
	                        $("#" + href).show();
	                    }else{
	                        $("#" + href).hide();
	                        $(this).parent().removeClass("active");
	                    }
                    };
                });
                if (!$("#" + newValue + " .tab-buttons label.active").length){
                	var el = $("#" + newValue + " .tab-buttons label")[0];
                	$(el).trigger('click');
                }
            },

            tabchange: function(context, element, event){
                event.preventDefault();
                can.route.attr(this.bindRoute, $(element).find('a').attr('href').substr(1));
            },
		},

		helpers: $.extend(BaseHelpers, {})
	})
})