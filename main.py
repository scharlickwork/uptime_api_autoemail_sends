from base64 import b64encode
import requests
import json
import re
import smtplib
import email.message
import logging
import os
import datetime

#set logging variable
script_name = os.path.basename(__file__)
current_directory = os.getcwd()
datetime = datetime.datetime.now()
log_dir = f'{current_directory}/log'
# log_dir = log_dir.replace(" ", "_")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
#logging configs
logging.basicConfig(
    filename=f'{log_dir}/{script_name}.log',  # Specify the log file name (optional)
    level=logging.INFO,     # Set the logging level (e.g., INFO, DEBUG, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Define the log message format (optional)
)
#global setting for email send
sender_email_id = 'AKIAJPBAKXYZETF2JOOA'
sender_email_id_password = 'AsQSbkseKx9aPoSrL2tSA30bZOEuPS6hhYliIneaaw/V'

##global variable
api_data_sorted = {}
userAndPass = b64encode(b"api:jamfapi").decode("ascii")

#makes specific API with url and token passed through
def api_call_and_return(url, token):
    #actual api call being made
    response = requests.get(url, headers={"Authorization": "Bearer %s" % token})
    #check for proper http reponse return response at .text file
    if response.status_code == 200:
        return response.text
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error("Response content:", response.text)
        return None

#jamf Api call to get brearer token to be able to make specific API calls
def jamf_api_token_call():
    #set variables
    url = 'https://casper.cgps.org:8443/api/v1/auth/token'
    headers = {'Authorization': 'Basic %s' % userAndPass}
#make the call
    try:
        token_call = requests.post(url, headers=headers)
        token_call.raise_for_status()
#check for correct http reponse and set token are variable
        if token_call.status_code == 200:
            api_json = token_call.json()
            token = api_json.get('token')

            if token:
                return token
            else:
                logging.error("Error: Token not found in the API response")
        else:
            logging.error(f"Error: API request failed with status code {token_call.status_code}")
            logging.error(token_call.text)  # Print the content of the response for further inspection

    except requests.RequestException as e:
        logging.error(f"Error making API request: {e}")

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error: {e}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return None

#sets the url for each api call, calls the api_call_return_function and returns .jscon data
def jamf_apicalls(token):
    full_computer_inventory_data = api_call_and_return(
        'https://casper.cgps.org:8443/api/v1/computers-inventory?section=GENERAL&page=0&page-size=3000&sort=id%3Aasc',
        token
    )

    ext_attribute_inventory_data = api_call_and_return(
        'https://casper.cgps.org:8443/api/v1/computers-inventory?section=EXTENSION_ATTRIBUTES&page=0&page-size=3000&sort=id%3Aasc',
        token
    )

    return full_computer_inventory_data, ext_attribute_inventory_data

#lints the returned API data seperating out into and returning an array of dictionaries for email sending
def api_info_sorting(full_computer_inventory_data, ext_attribute_inventory_data):
    try:
        #loads the .json text file to an active state for infomration retreaval
        full_inventory_data = json.loads(full_computer_inventory_data)
        extension_attribute_data = json.loads(ext_attribute_inventory_data)
        #checks that both have reults dict in file
        if 'results' in full_inventory_data and 'results' in extension_attribute_data:
            #set variable for array
            computer_records_array = []
            #sets list to start in the result dict of .json file
            computer_records = full_inventory_data['results']
            extension_attribute = extension_attribute_data['results']
            #loops computer record list and sets variable to be used
            for record in computer_records:
                computer_id = record.get('id')
                computer_name = record['general']['name']
                #within one computer record loop, after getting the computer ID as a comparison point it loops over extention attributes to assosiate the correct computer to the correct extention attribute value
                for ext_record in extension_attribute:
                    #compairs the unique value of computer ID record to make sure the correct entry is pulled
                    if isinstance(ext_record, dict) and ext_record['id'] == computer_id:
                        #sets the definition of the extention attribute as jamf numbers it
                        target_definition_id = "24"
                        #uses the .get search exention attribute and if the tag exists it grabs the value
                        extension_attributes = ext_record.get("extensionAttributes", [])
                        #after finding the extentionAttribute location it finds the next dict entry that matches the target definistion id.  None value is defualt if not found
                        target_entry = next(
                            (entry for entry in extension_attributes if entry["definitionId"] == target_definition_id),
                            None)
                        #checks for trutthy value in variable return
                        if target_entry:
                            #sets value of uptime extention atrribute
                            up_time = target_entry.get("values")
                            #create the dictionary format
                            computer_record_dict = {
                                'ID': computer_id,
                                'Name': computer_name,
                                'Up Time': up_time
                            }
                            #append dictionary with new values
                            computer_records_array.append(computer_record_dict)
                        else:
                            logging.error(f"DefinitionId {target_definition_id} not found in extensionAttributes for this record.")
                    else:
                        continue

            return computer_records_array
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def email_send(computer_records_array):
    #sets regex pattern for variable ending in -m2
    pattern = re.compile(r".*-m2$")
    try:
        #uses array of dictionary created in prvious function
        for record in computer_records_array:
            #sets variables to be used in loop and email send
            computer_name = record['Name']
            #converts list to str type
            up_time = str(record['Up Time'])
            #removes trailing [] from list value
            up_time = up_time[2:-2]

            try:
                #excludes any computer with value less than a day or no value
                if up_time != 'Less then a day' or '':
                    # logging.info(f' computer name: {computer_name} uptime: {up_time} ')
                    #matches for regex
                    match = re.search(pattern, computer_name)
                    #converts varable to int for comaprison
                    up_time = int(up_time)
                    if match and up_time > 30:
                        #linting for computer name to email changes stest-m2 to stest
                        computer_name_email_edit = computer_name[:-3]
                        #adds @cgps for email send
                        email_based_on_computer_name = computer_name_email_edit + "@cgps.org"
                        s = smtplib.SMTP('email-smtp.us-east-1.amazonaws.com', 587)
                        s.starttls()
                        s.login(sender_email_id, sender_email_id_password)
                        m = email.message.Message()
                        m['From'] = "noreply@cgps.org"
                        m['To'] = email_based_on_computer_name
                        m['Subject'] = "Your computer may need a restart"
                        body = f"Hello,\n\nThis is an automated email from the CGPS Tech Team. Our records indicate that your computer " \
                               f"has been on for at least {up_time} days.  Computers start to have issues when they are left " \
                               f"on for prolonged periods of time.  To ensure your computer is running well, we strongly recommend that you restart your computer as soon as you can. If you have any questions please email us at support@cgps.org\n\n- CGPS Tech Team"
                        m.set_payload(body)
                        s.sendmail("noreply@cgps.org", email_based_on_computer_name, m.as_string().encode('utf-8'))
                        s.quit()
                        logging.info(f'email sent to {email_based_on_computer_name} for having it on for {up_time}')
            except (IndexError, ValueError) as e:
                logging.error(f"Error: {e}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")




def main():
    # API call to get Bearer Token
    token = jamf_api_token_call()

    if token:
        # API calls to get data
        full_computer_inventory_data, ext_attribute_inventory_data = jamf_apicalls(token)

        # Sorting and processing data
        computer_records_array = api_info_sorting(full_computer_inventory_data, ext_attribute_inventory_data)

        # Sending emails
        email_send(computer_records_array)


if __name__ == "__main__":
    main()