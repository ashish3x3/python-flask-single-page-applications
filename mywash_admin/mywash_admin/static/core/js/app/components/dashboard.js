define([
    'jquery',
    'can',
    'd3',
    'xchart',  
    '../../lib/mywash/constructs/map.helpers',
    '../../lib/mywash/components/tabs',
    'toastr',
    'nanobar',
    'datepicker',
    'momentjs',
],function($, can, d3, xChart, BaseHelpers, TabsComponents, toastr, Nanobar){
    'use strict';

    var TabsComponent = TabsComponents[0];
    var TabsComponentScope = TabsComponents[1];

    return can.Component.extend({
        tag: 'order-freq-tag',
        template: "",
        scope: TabsComponentScope.extend({
            init: function(){

                this.total_users = can.compute(0);

              

            },
            getTotalUsers: function(){

            }
                
        }),

         _pollData: function(pickup_type, date, time, refresh){
                if(date) date = this.getFormattedDate(moment(date));
                if(time) time = this.getFormattedTime(moment(time));
                if(!refresh) refresh = false;
                var pollUrl = "";
                if(time){
                    pollUrl = "/api/pickup/" + date + "/" + time;
                }else{
                    pollUrl = "/api/pickup/" + date;
                }
                this.nanobar.go(30);
                
                $.ajax({
                    url: pollUrl,
                    type: 'get',
                    context: this,
                    dataType: 'json',
                    success: function(data){
                        //console.log(data)
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


        events: {
            'inserted': function(){

             
   
        }
        
    },

     //events






}); //can-component
}) //define




