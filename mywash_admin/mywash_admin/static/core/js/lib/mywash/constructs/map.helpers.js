define(["jquery", "can", 'momentjs'], function($, can){
	
	var BaseHelpers = {
		getFormattedDate: function(value, options){
			var val = value();
			if (!val) return "";
			var date = moment(val);
			return date.format("YYYY-MM-DD");
		},

		getFormattedDateTime: function(value, options){
			var val = value();
			if (!val) return "";
			var date = moment(val);
			return date.format("YYYY-MM-DD hh:mm A");
		},

		lower: function(valueFunc, options){
			return valueFunc().toLowerCase();
		},

		upper: function(valueFunc, options){
			return valueFunc().toUpperCase();
		},

		capitalize: function(valueFunc, options){
			var value = null;
			if (typeof valueFunc == 'function')
				value = valueFunc();
			else if (typeof valueFunc == 'string')
				value = valueFunc;

			if (value)
				return value.charAt(0).toUpperCase() + value.slice(1);
			else
				return value;
		},

		ifNot: function(valueFunc, options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			if (valueFunc()) return fnFalse();
			else return fnTrue();
		},

		isNum: function(valueFunc, options){
			var value = valueFunc();
			var fnTrue = options.fn, fnFalse = options.inverse;
			return isNaN(value)? fnFalse() : fnTrue();
		},

		isSet: function(valueFunc, options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			var m = typeof valueFunc() != "undefined"? fnTrue() : fnFalse();
			return m
		},

		idFormat: function(valueFunc, options){
			var data = valueFunc().toLowerCase();
			var dataSplit = data.split(' ');
			return dataSplit.join('-')
		},

		isEmpty: function(valueFunc, options){
			var fnTrue = options.fn, fnFalse = options.inverse, map = valueFunc();
			if (typeof map == 'undefined') return;
			var count = 0, data = map.attr();
			map.each(function(index, value){
				count++;
			})
			if (count == 0) return fnTrue();
			return fnFalse();
		},

		isNotEmpty: function(valueFunc, options){
			var map = null;
			if(typeof valueFunc == "object") map = valueFunc;
			else map = valueFunc();
			var fnTrue = options.fn, fnFalse = options.inverse;
			if (typeof map == 'undefined') return 0;
			var count = 0;
			$.each(map.attr(), function(index, value){
				count++;
			})
			if (count == 0) return fnFalse();
			return fnTrue();
		},

		ifEqual: function(a, b ,options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			if (typeof a == "function") {
				a = a();
			}

			if (typeof b == "function") {
				b = b();
			}

			if (a && a.indexOf(" ") >= 0)
				a = a.replace(/ /g, '');
			if (b && b.indexOf(" ") >= 0)
				b = b.replace(/ /g, '');
			return a == b ? fnTrue() : fnFalse();
		},

		ifNotEqual: function(a, b ,options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			if (typeof a == "function") {
				a = a();
			}

			if (typeof b == "function") {
				b = b();
			}
			
			if (a && a.indexOf(" ") >= 0)
				a = a.replace(/ /g, '');
			if (b && b.indexOf(" ") >= 0)
				b = b.replace(/ /g, '');

			return a != b ? fnTrue() : fnFalse();
		},

		lt: function(a, b ,options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			return a() < b ? fnTrue() : fnFalse();
		},

		gt: function(a, b ,options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			return a() > b ? fnTrue() : fnFalse();
		},

		// Length for list and maps
		length: function(obj, options){
			if (typeof obj == 'function')
				obj = obj();
			var count = 0;
			if(obj){
				obj.each(function(index, value){
					count++;
				})
			}
			return count;
		},

		incr: function(obj, options){
			var obj = obj();
			return ++obj;
		},

		decr: function(obj, options){
			var obj = obj();
			return --obj;
		},

		timeRangeFormat: function(valueFunc, options){
			var suffix = null, ceil = null, floor = null, rawCeil = null, rawFloor = null;
			var rawSum = parseInt(valueFunc);
			if (rawSum % 2 == 0) {
				rawCeil = rawSum/2 + 1;
				rawFloor = rawSum/2 - 1;
			}else{
				rawCeil = (rawSum+1)/2;
				rawFloor = rawCeil - 1;
			}

			if(rawCeil > 12)
				ceil = (rawCeil - 12).toString() + "pm";
			else if(rawCeil == 12)
				ceil = rawCeil.toString() + "pm";
			else
				ceil = rawCeil.toString() + "am";

			if(rawFloor > 12)
				floor = (rawFloor - 12).toString() + "pm";
			else if(rawFloor == 12)
				floor = rawFloor.toString() + "pm";
			else
				floor = rawFloor.toString() + "am";
			return floor + " - " + ceil;
		},

		_timeRange: function(valueFunc, options){
			var suffix = null, ceil = null, floor = null, rawCeil = null, rawFloor = null;
			var rawSum = parseInt(valueFunc);
			if (rawSum % 2 == 0) {
				rawCeil = rawSum/2 + 1;
				rawFloor = rawSum/2 - 1;
			}else{
				rawCeil = (rawSum+1)/2;
				rawFloor = rawCeil - 1;
			}
			return {
				'ceil': rawCeil,
				'floor': rawFloor
			}
		},

		timeslotBackColor: function(hour, date, option){
			var today = moment(), date = moment(date());
			if(today.format("YYYY-MM-DD") != date.format("YYYY-MM-DD")) return "#FFF5A3";
			if (this._timeRange(hour)['ceil'] < today.hours()) return "#ff6c60";
			else if((this._timeRange(hour)['ceil'] - today.hours()) < 2 ) return "#FF8134";
			else return "#FFF5A3";
		},

		currentDate: function(options){
			var date = moment();
			return date.format("DD-MM-YYYY hh:mma")
		},

		joinList: function(list, delimiter, options){
			if (typeof list == 'function') list = list();
			if (list) 
				return list.attr().join(delimiter || ',');
		},

		jsonify: function(list, options){
			if (typeof list == 'function') list = list();
			if (list) 
				return JSON.stringify(list.attr());
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

		startsWith: function(a, b, options){
			var fnTrue = options.fn, fnFalse = options.inverse;
			if (typeof a == 'function') a = a();
			if (typeof b == 'function') b = b();
			return a.startsWith(b) ? fnTrue() : fnFalse();
		},

	};

	return BaseHelpers;
})