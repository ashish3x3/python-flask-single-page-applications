import json
import logging

PAGE_SIZE=5

GRAPH_URL="//graph.facebook.com/"
FB_PICTURE_URL="/picture?type=square"
GOOGLE_USER=1
FACEBOOK_USER=2
TWITTER_USER=3
#PICTURE URL
GRAPH_URL="//graph.facebook.com/"
FB_PICTURE_URL="/picture?type=square"

ORDER_PLACED=1
ORDER_PICKED=2
ORDER_CLEANED=3
ORDER_COMPLETE=4
ORDER_CANCELLED=5
ORDER_REJECTED=6

ORDER_DICT={"1":"Order Placed","2":"Order Picked","3":"Order Cleaned","4":"Order Completed","5":"Order Cancelled","6":"Order Rejected"}

TYPE_DICT={
    "WASH & IRON": "Wash & Iron",
    "DRY_CLEANING": "Dry Cleaning",
    "IRON": "Iron",
    "laundry": "Wash & Iron",
    "dryclean": "Dry Cleaning",
    "iron": "Iron",
}

ADMIN_IDS_FB = [
    "fb_10202977985192041",
    "fb_10152322380847681",
    "fb_10203625451411334",
    "fb_1319053205"
]