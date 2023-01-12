
from base64 import b64encode
import requests
import json
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


#global setting for email send
smtp_server = 'smtp.gmail.com'
gmail = 'noreply@cgps.org'
password = 'PwAzE8mK'
smtp_port = 587



def catch_them_all():
    ## PI request with basic auth to get Bearer Token
    ## tuyrns on basic auth or Requests module
    userAndPass = b64encode(b"api:jamfapi").decode("ascii")
    Token_call = requests.post('https://casper.cgps.org:8443/api/v1/auth/token', headers = { 'Authorization' : 'Basic %s' %  userAndPass })
    api_data = Token_call.text
    api_json = json.loads(api_data)
    token = (api_json['token'])
    # # ## API call to get full computer inverntory records
    full_computer_inventory = requests.get('https://casper.cgps.org:8443/api/v1/computers-inventory?section=GENERAL&page=0&page-size=3000&sort=id%3Aasc', headers = { "Authorization": "Bearer %s" %token})
    api_data = full_computer_inventory.text
    full_computer_inventory = json.loads(api_data)


        ## API call to get all computer inverntory records based on Extention Attribvute
    # EAinventory = "EAinventory.json"
    computer_EAinventory = requests.get('https://casper.cgps.org:8443/api/v1/computers-inventory?section=EXTENSION_ATTRIBUTES&page=0&page-size=3000&sort=id%3Aasc', headers = { "Authorization": "Bearer %s" %token})
    api_data = computer_EAinventory.text
    EAinventory = json.loads(api_data)
    ## Creates a dictionary linking computer ID to Uptime EA
    computerUptimeByID = {}
    total_number = (EAinventory['totalCount'])
    number_EA = (len(EAinventory['results'][1]['extensionAttributes']))
    for i in range(0, total_number, 1):
        computerID = str(EAinventory['results'][i]['id'])
        computerUptimeByID[computerID] = 0
        computer_name = (full_computer_inventory['results'][i]['general']['name'])
        for ii in range(0, number_EA, 1):
            if ((EAinventory['results'][i]['extensionAttributes'][ii]['name']) == 'Computer Uptime'):
                days_up_edit = str(EAinventory['results'][i]['extensionAttributes'][ii]['values'])
                days_up_edit = days_up_edit.replace("'", '')
                days_up_edit = days_up_edit.replace("[]", '')
                days_up_edit = days_up_edit.replace("[", '')
                days_up_edit = days_up_edit.replace("]", '')
                days_up = days_up_edit.replace("u", '')
                computerUptimeByID[computerID] = {'days up' :days_up, 'computer name' : computer_name}
        else:
            continue
    ##take the dictionary, searches for computers ID more than 7 days up, puts the time up and computer name in a list
    keys = computerUptimeByID.keys()
    t = 0
    hasnotrestartedrecent = {t: 0}
    value = []
    up_time = []
    name = []
    for i in keys:
        if (computerUptimeByID[i]['days up'] == ('Less then a day')):
            pass
        elif bool(computerUptimeByID[i]['days up']):
            value.append(i)
    # print(value)
    for i in value:
        if ((int(computerUptimeByID[i]['days up'])) > 10):
            days_up = (computerUptimeByID[i]['days up'])
            computer_name = (computerUptimeByID[i]['computer name'])
            hasnotrestartedrecent[t] = {'days up' :days_up, 'computer name' : computer_name}
            t = t +1
    ## sperates dictionary of hasn't restarted into two lists to be inputted into email function
    # for i in hasnotrestartedrecent:
    #     name.append((hasnotrestartedrecent[i]['computer name']).split('-')[0])
    #     up_time.append(hasnotrestartedrecent[i]['days up'])
    email_send(hasnotrestartedrecent)

def email_send(hasnotrestartedrecent):
    print(hasnotrestartedrecent)










catch_them_all()













#
# #Replace with your own gmail account
# cc = []
# message = MIMEMultipart('mixed')
# message['From'] = 'Contact <{sender}>'.format(sender = gmail)
# message['To'] = student_email
# message['Subject'] = 'Hello'
# msg_content = '<h4>Hi There,<br> This is a testing message.</h4>\n'
# body = MIMEText(msg_content, 'html')
# message.attach(body)
# with smtplib.SMTP(smtp_server, smtp_port) as server:
#     server.ehlo()
#     server.starttls(context=context)
#     server.ehlo()
#     server.login(gmail, password)
#     server.sendmail(gmail, student_email.split(";") + (cc.split(";") if cc else []),
#                 msg_full)
#     server.quit()
# print("email sent out successfully")
#




# #take the array and send emails
# def inform_them_all(name, up_time):
#    # Sets variables
#    port = 465  # For SSL
#    password = 'PwAzE8mK'
#    username = 'noreply@cgps.org'
#    gmail_user = 'noreply@cgps.org'
#    # name = name
#    # up_time = up_time
#    sent_from = gmail_user
#    trange = len(name)
#    for i in range(trange):
#       ##comma sperates multi addresses
#       to = [name[i] + "@cgps.org"]
#       subject = 'Your computer may need a restart'
#       body = "Hello,\n\nThis is an automated email from the CGPS Tech Team. Our records indicate that your computer has been on for at least " + str(up_time[i]) + " days. " \
#              "Computers start to have issues when they are left on for prolonged periods of time. " \
#              "To ensure your computer is running well, we strongly recommend that you restart your computer as soon as you can. If you have any questions please email us at support@cgps.org\n\n- CGPS Tech Team"
#
#       email_text = 'Subject: {}\n\n{}'.format(subject, body)
#
#       server = smtplib.SMTP_SSL('smtp.gmail.com', port)
#       server.ehlo()  # optional
#       server.login(username, password)
#       server.sendmail(sent_from, to, email_text)
#       server.close()
