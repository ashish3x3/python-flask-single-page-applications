define([
    'jquery',
	'can', 
], function($, can){
	'use strict';

	var TabsComponent =  can.Component.extend({},{
		tag: "",
		template: "<content></content>",
        scope: TabsScope
	});

   var TabsScope = can.Map({
            tabchangeevent: function(context, newValue){
                
            },

            tabchange: function(context, element, event){
                event.preventDefault();
                var newValue = $(element).find('input').attr('href').substr(1);
                var elements = $('input[href="#' + newValue + '"]').parents('.btn-group').find('input');
                elements.each(function(){
                    var href = $(this).attr('href').substr(1);
                    if (href === newValue) {
                        $(this).parent().addClass("active");
                        $("#" + href).show();
                    }else{
                        $("#" + href).hide();
                        $(this).parent().removeClass("active");
                    }
                });
            },

            _validateEmail: function(data){
                var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
                return re.test(data)
            },

            _validatePhone: function(data){
                var re = /^((\+?91)|(0))?\d{8,12}$/;
                return re.test(data)
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

                var override_color = null;
                if (credible_status == 'pickup_failed' || credible_status == 'delivery_failed'){
                    override_color = 'danger';
                }

                this.order_status.each(function(group, key){
                    group.status.each(function(status, inner_key){
                        if (status.name_id == credible_status) {
                            status['color'] = override_color || group.color;
                            return_status = status;
                        }
                    })
                });
                return return_status;
            },


        })

    return [TabsComponent, TabsScope];

});
