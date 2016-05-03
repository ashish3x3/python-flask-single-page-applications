import sendgrid,jinja2
from jinja2 import Template, PackageLoader, FileSystemLoader, Environment
import os
import logging
import urllib,config

user_name = "mywash"
api_key = "dummy123"
env = Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def sendmailWithTemplate(paramDict = {}):

    recepients = paramDict.get('recepients','')
    if(recepients=="" or recepients==None):
        print "No recepients email defined"
        return
        

    template =  env.get_template(paramDict.get('templateName',''))
    html = template.render(paramDict)
    

    attach_path = ''
    attach_name = ''
    if(not paramDict.get('attach_name','')==''):
        attach_name = paramDict['attach_name']
        attach_path = paramDict['attach_path']
    categories = paramDict.get('categories',[])
    if(not isinstance(categories,list)):
        categories = []

    senderMail=paramDict.get("senderMail","team@mywash.in")
    
    sendmail(recepients = paramDict.get('recepients',''),recepientName = paramDict.get('recepientName',''),senderMail = senderMail,subject = paramDict.get('subject','New Message from MyWash'),body = paramDict.get('body',''),html = html,attach_path=attach_path,attach_name=attach_name,categories=categories)



def sendmail(recepients,recepientName,senderMail = 'noreply@MyWash.in', senderName = 'MyWash',subject = 'MyWash', body='',html='',attach_path='',attach_name='',categories=[]):
    s = sendgrid.Sendgrid(user_name, api_key, secure=True)
    message = sendgrid.Message((senderMail,senderName), subject, body, html)
    message.add_header("Content-Type","text/html; charset=utf-8")
    message.add_to(recepients,recepientName)
    message.add_category(categories)
    if(attach_path!=''):
        print "Sending attachment and path",attach_name," ",attach_path
        message.add_attachment(attach_name,attach_path)
    s.smtp.send(message)
    if(attach_path!=''):
        _del_file(attach_path)
