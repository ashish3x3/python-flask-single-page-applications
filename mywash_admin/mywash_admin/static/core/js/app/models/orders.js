define([
	'jquery',
	'can',
], function($, can){
	'use strict';

	return can.Model.extend({
		findAll: "GET /api/order",
		findOne: "GET /api/order/{id}",
		update: "PUT /api/order/{id}"
	})
})