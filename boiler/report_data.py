from datetime import date

from boiler import get_report

get_report.get_report()

"""
Sending dummyrey report
"""
try:
    get_report.sendmail(attach_path='/home/lawrence/mywash/boiler/dummyrey.zip',attach_name='dummyrey_report.zip')
except Exception as e:
    print e

"""
Sending status report
"""
try:
    attach_name = 'report_for_'+str(date.today()).replace('-', '/')+'.zip'
    get_report.sendmail(attach_path='/home/lawrence/mywash/boiler/order_status.zip',attach_name=attach_name)
except Exception as e:
    print e