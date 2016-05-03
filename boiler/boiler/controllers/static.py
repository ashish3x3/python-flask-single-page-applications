from flask import render_template,session, make_response, request, jsonify, json
from boiler.models.dao import itemsDAO
from boiler.renderer import commonrender
from boiler import app
import copy
from flask import Flask, make_response
import sms
from boiler.models.database import db
import pymongo
import csv
from datetime import datetime, date
import Constants
import pytz
import requests

# def test():
#     return jsonify({})


def celery_test():
    print "celery"
    sms.sms_alert_agent_pickup.delay({"phone":"7411721439","name":"raghu","order_id":"544ba81c425b9667c1d8980f"})


@commonrender('profile/basicinfo/form.jinja')
def basicinfo():
    result = {



        'deals': {
            0: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },

             1: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             2: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             3: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },



             4: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             5: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": 5,
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },
            
        }


    }

    
    # print result
    return result











@commonrender('order/order_history/history.jinja')
def order_history():
    result = {



        'deals': {
            0: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },

             1: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             2: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             3: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },



             4: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             5: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": 5,
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },
            
        }


    }

    
    # print result
    return jsonify(result)










@commonrender('order/order_history/reciept.jinja')
def order_reciept():
    result = {



        'deals': {
            0: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },

             1: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             2: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             3: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },



             4: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             5: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": 5,
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },
            
        }


    }

    
    # print result
    return result









@commonrender('order/status.jinja')
def order_status():
    result = {



        'deals': {
            0: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },

             1: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             2: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             3: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },



             4: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             5: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": 5,
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },
            
        }


    }

    
    # print result
    return result








@commonrender('login/form.jinja')
def login():
    result = {



        'deals': {
            0: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },

             1: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             2: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             3: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },



             4: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             5: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": 5,
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },
            
        }


    }

    
    # print result
    return result
 
    
@commonrender('pricing/pricing.jinja')
def pricing():
    result = {



        'deals': {
            0: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },

             1: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             2: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             3: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },



             4: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": {
                    "count":5,
                    "all_comments": {
                        0: "",
                        1: "",
                        2: ""
                    }
                },
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },


             5: {
                'id': 1535282599,
                'title': 'Footwear Sale on',
                'description': 'Footwear Sale on',
                'url': '/profile/1535282599',
                'discount': '10%',
                "price_original": "240Rs", 
                "price_current": "220Rs", 
                "upvotes": 0.0,
                "views": 10,
                "comments": 5,
                "posted_by": {
                    "auth_key": "53dceeecb8139317d267054c",
                    "name": 'Balaji Ashok',
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xfa1/t1.0-1/p160x160/429103_2718081952695_497634066_n.jpg",
                    "email": 'balajiadober@gmail.com'
                },
                'posted_on': '',
                'expires_on': '',
                'imageUrl': '//graph.facebook.com/1535282599/picture?width=50&height=50',
                "categories": [
                    "fashion", 
                    "apparel"
                ]
            },
            
        }


    }

    
    # print result
    return result


def get_current_time():
    kol = pytz.timezone("Asia/Calcutta")
    a = datetime.utcnow()
    a = a.replace(tzinfo=kol)
    return kol.fromutc(a).strftime("%Y-%m-%d %H:%M:%S")


def timeslots():
    return jsonify(requests.get("%s/api/timeslot" % app.config['API_SERVER']['private_dashboard']).json())


def order_item(order_id):
    return jsonify(requests.get("%s/api/orderitem/%s" % (app.config['API_SERVER']['private_dashboard'], order_id)).json())


def paytm_payment(order_id):
    return jsonify(requests.get("%s/api/paytm/payment/%s" % (app.config['API_SERVER']['private_dashboard'], order_id)).json())


def dashboard_address(address_id=None):
    form = copy.deepcopy(request.form)
    print "form........", form
    if request.method not in ['GET', 'DELETE']:
        if not form.get('tag', False):
            return jsonify({'status': 'failure', 'error': 'Tag not provided.'}), 403

        if not form.get('apartment_number', False):
            return jsonify({'status': 'failure', 'error': 'Flat number not provided.'}), 403

        if not form.get('address_2', False):
            return jsonify({'status': 'failure', 'error': 'Landmark not provided.'}), 403

        if not form.get('locality', False):
            return jsonify({'status': 'failure', 'error': 'Locality not provided.'}), 403
        else:
            locality = json.loads(form['locality'])
            print "locality.....", locality
            if locality is None:
                return jsonify({'status': 'failure', 'error': 'Locality not provided.'}), 403
            if locality['lat'] is False:
                return jsonify({'status': 'failure', 'error': 'Locality invalid. Refresh page and try again.'}), 403
            if locality['lng'] is False:
                return jsonify({'status': 'failure', 'error': 'Locality invalid. Refresh page and try again.'}), 403
    
        if not form.get('address_1', False):
            return jsonify({'status': 'failure', 'error': 'Address not provided.'}), 403

    ret = None
    if request.method == 'GET':
        ret = requests.get("%s/api/address/%s" % (app.config['API_SERVER']['private_dashboard'], address_id)).json()
    elif request.method == 'PUT':
        ret = requests.put("%s/api/address/%s" % (app.config['API_SERVER']['private_dashboard'], address_id), data=form).json()
    elif request.method == 'POST':
        ret = requests.post("%s/api/address" % app.config['API_SERVER']['private_dashboard'], data=form).json()
    elif request.method == "DELETE":
        ret = requests.delete("%s/api/address/%s" % (app.config['API_SERVER']['private_dashboard'], address_id), data=form).json()

    return jsonify(ret)
