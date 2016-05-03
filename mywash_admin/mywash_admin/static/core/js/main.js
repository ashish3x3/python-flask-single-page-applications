
require.config({
    shim: {
        bootstrap: {
            deps: ['jquery']
        },
        dcjqaccordion: {
            deps: ['jquery'],
        },
        scrollTo: {
            deps: ['jquery']
        },
        slidebars: {
            deps: ['jquery']
        },
        nicescroll: {
            deps: ['jquery']
        },
        common_scripts: {
            deps: ['jquery']
        },
        datepicker: {
            deps: ['jquery']
        },
        jqprint: {
            deps: ['jquery']
        },
        ajaxForm: {
            deps: ['jquery']
        },
        toastr: {
            deps: ['jquery']
        },
        selectize: {
            deps: ['jquery']
        },
        d3: {
            exports: 'd3'
        },
        xchart: {
            deps: ['d3'],
            exports: 'xchart'
        },
        respondjs: {
            exports: "respondjs"
        },
        daterangepicker:{
            deps: ['jquery'],
            exports: 'daterangepicker'
        }
    },

    paths: {
        jquery: './lib/misc/jquery-2.1.3.min',
        can: './lib/canjs/can',
        bootstrap: './lib/misc/bootstrap.min',
        dcjqaccordion: './lib/misc/jquery.dcjqaccordion.2.7',
        scrollTo: './lib/misc/jquery.scrollTo.min',
        slidebars: './lib/misc/slidebars.min',
        nicescroll: './lib/misc/jquery.nicescroll',
        respondjs: './lib/misc/respond.min',
        common_scripts: './lib/misc/common-scripts',
        datepicker: './lib/assets/bootstrap-datepicker/js/bootstrap-datepicker.min',
        momentjs: './lib/assets/bootstrap-daterangepicker/moment.min',
        summernote: './lib/assets/summernote/dist/summernote.min',
        toastr: './lib/assets/toastr-master/build/toastr.min',
        selectize: './lib/assets/selectize/js/standalone/selectize',
        nanobar: './lib/assets/nanobar/nanobar.min',
        d3: "./lib/assets/xchart/d3.v3.min",
        xchart: "./lib/assets/xchart/xcharts.min",
        jqprint: './lib/misc/jquery.print.min',
        ajaxForm: './lib/misc/jquery.ajaxform.min',
        async: './lib/requirejs/async',
        daterangepicker: './lib/assets/bootstrap-daterangepicker/daterangepicker'
    },

    waitSeconds: 0,

})

define('gmaps', 
    ['async!https://maps.googleapis.com/maps/api/js?libraries=geometry,places&sensor=false'],
    function(){
        return window.google.maps;
    })

require([
    "jquery",
    'can',
    "common_scripts",
    'can/route/pushstate',
    'bootstrap',
    'dcjqaccordion',
    'scrollTo',
    'slidebars',
    'nicescroll',
    'respondjs',
    './app/components/leftSidebar',
    './app/components/pickupOrders',
    './app/components/deliveryOrders',
    './app/components/cleaningItemsConf',
    './app/components/cancelledOrders',
    './app/components/completedOrders',
    './app/components/allOrders',
    './app/components/taggingOrders',
    './app/components/packageOrders',
    './app/components/usersList',
    './app/components/vendorsList',
    './app/components/logisticStaffs',
    './app/components/failureReasonsConf',
    './app/components/deliveryProgress',
    './app/components/timeslotsBlockConf',
    './app/components/dashboard',
    ], function($, can, base_init){
        'use strict';

        $(function(){
            can.route.ready();
            can.route("/:sidebarmenu", {tabname: "frameworks"});

            var status_defer = $.ajax({
                url: "/api/statuslist",
                type: "get",
                dataType: 'json',
            })

            var timeslot_status = $.ajax({
                url: "/api/timeslot",
                type: "get",
                dataType: 'json',
            })

            var servicetype_defer = $.ajax({
                url : "/api/servicetype",
                type : 'get',
                dataType : 'json',
            })

            $.when(status_defer, timeslot_status, servicetype_defer).done(
                function(status_data, timeslot_data, servicetype_data){
                    status_data = status_data[0];
                    timeslot_data = timeslot_data[0];
                    servicetype_data = servicetype_data[0];
                    
                    localStorage.setItem("statuses", JSON.stringify(status_data.data));
                    localStorage.setItem("timeslots", JSON.stringify(timeslot_data.data));
                    localStorage.setItem('servicetype', JSON.stringify(servicetype_data));
                    
                    $("#container").html(can.view("core-template", {}));
                    base_init();
                    $("#loading-screen").remove();
                    can.route.attr('sidebarmenu', "main-content-dashboard");

                    $('#logout-btn').click(function(){
                        $.ajax({
                            url: '/logout',
                            type: 'get',
                            dataType: 'json',
                            success: function(){
                                location.reload()
                            }
                        })

                    })
                    
                }
            )

        })

})