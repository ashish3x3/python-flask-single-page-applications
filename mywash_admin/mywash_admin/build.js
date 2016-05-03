({
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
		d3: {
			exports: 'd3'
		},
		xchart: {
			deps: ['d3'],
			exports: 'xchart'
		}
	},

	paths: {
		jquery: 'lib/misc/jquery-2.1.3.min',
		can: 'lib/canjs/can',
		bootstrap: 'lib/misc/bootstrap.min',
		dcjqaccordion: 'lib/misc/jquery.dcjqaccordion.2.7',
		scrollTo: 'lib/misc/jquery.scrollTo.min',
		slidebars: 'lib/misc/slidebars.min',
		nicescroll: 'lib/misc/jquery.nicescroll',
		respondjs: 'lib/misc/respond.min',
		common_scripts: 'lib/misc/common-scripts',
		datepicker: 'lib/assets/bootstrap-datepicker/js/bootstrap-datepicker',
		momentjs: 'lib/assets/bootstrap-daterangepicker/moment.min',
		tasklist: 'lib/misc/tasks.js',
		summernote: 'lib/assets/summernote/dist/summernote.min',
		toastr: 'lib/assets/toastr-master/build/toastr.min',
		nanobar: 'lib/assets/nanobar/nanobar.min',
		d3: "lib/assets/xchart/d3.v3.min",
		xchart: "lib/assets/xchart/xcharts.min",
		jqprint: 'lib/misc/jquery.print.min',
	},

	mainConfigFile : "static/core/js/main.js",
	baseUrl: "static/core/js/",
	name: "main",
	out: "static/dist/main_561a5c4a27e76e15dd556971.js",
	removeCombined: true
})