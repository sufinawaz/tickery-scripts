import requests
from datetime import datetime
from time import sleep
import json
try:
    from sense_hat import SenseHat
except ImportError:
    # this is done so that the script does not die a horrible death
    # when running on a device other than raspberry pi
    print('No sense hat')

# configurations
hickery_api_host_address = "<ENETER_HOST_ADDRESS_HERE>"
harvest_account_id = '<ENTER_HARVEST_ACCOUNT_ID_HERE>'
harvest_user_id = '<ENTER_HARVEST_USER_ID_HERE>'
harvest_access_token = '<ENTER_HARVEST_PERSONAL_ACCESS_TOKEN_HERE>'


hickery_api_url = "http://{}:8080/mapping".format(hickery_api_host_address)
headers = {'Harvest-Account-ID': harvest_account_id,
           'Authorization': "Bearer {0}".format(harvest_access_token)}
harvest_api_base_url = 'https://api.harvestapp.com/api/v2'
time_entries_url = harvest_api_base_url + '/time_entries'
today = datetime.now().strftime("%Y-%m-%d")

project_mapping = {}


def get_side_mapping():
    global project_mapping
    sideMappingJson = {}
    try:
        sideMappingJson = requests.get(hickery_api_url).json()
    except requests.ConnectionError as e:
        sense = SenseHat()
        sense.low_light = True
        sense.clear([255, 0, 0])
        sleep(.5)
        sense.clear()
        print("An exception has occurred - {}".format(e))
    for sideMappingJson in sideMappingJson['sideMappings']:
        if (sideMappingJson['sideNumber'] == 1):
            project_mapping[0] = sideMappingJson['harvestTask']
        elif (sideMappingJson['sideNumber'] == 2):
            project_mapping[90] = sideMappingJson['harvestTask']
        elif (sideMappingJson['sideNumber'] == 3):
            project_mapping[180] = sideMappingJson['harvestTask']
        elif (sideMappingJson['sideNumber'] == 4):
            project_mapping[270] = sideMappingJson['harvestTask']
    return project_mapping


def get_project_name(angle):
    global project_mapping
    if angle in project_mapping:
        harvest_task = project_mapping[angle]
        return "{0} - {1}".format(harvest_task['projectName'], harvest_task['taskName'])
    else:
        return "X"


def get_project_from_angle(angle):
    global project_mapping
    return project_mapping[angle]


def resume_existing_timer(time_entry_id):
    url = "{0}/time_entries/{1}/restart".format(
        harvest_api_base_url, str(time_entry_id))
    req = requests.patch(url, headers=headers)
    print(req.status_code)


def start_new_timer(task_id, project_id):
    url = "{0}/time_entries".format(harvest_api_base_url)
    req = requests.post(url, headers=headers, data={
                        "user_id": harvest_user_id, "project_id": project_id, "task_id": task_id, "spent_date": today})
    print(req.status_code)


def start_timer(harvestTask):
    task_id = harvestTask['taskId']
    project_id = harvestTask['projectId']
    if not task_id:
        return
    print("starting timer...")
    a = todays_time_entries().json()
    m = {}
    time_entry_id = None
    if 'time_entries' in a:
        for entry in a['time_entries']:
            m[entry['task']['id']] = entry['id']
    if task_id in m:
        print('resuming existing timer')
        time_entry_id = m[task_id]
        resume_existing_timer(time_entry_id)
    else:
        print('starting new timer')
        start_new_timer(task_id, project_id)


def todays_time_entries():
    return requests.get("{0}?from={1}".format(time_entries_url, today), headers=headers)


def get_running_time_entries():
    return requests.get("{0}?is_running=true".format(time_entries_url), headers=headers)


def stop_timers():
    time_entries = get_running_time_entries().json()['time_entries']
    for time_entry in time_entries:
        stop_timer(time_entry['id'])


def stop_timer(time_entry_id):
    url = "{0}/time_entries/{1}/stop".format(
        harvest_api_base_url, str(time_entry_id))
    req = requests.patch(url, headers=headers)
    print(req.status_code)


# # TEST -----------------------------------------------
# print(get_project_name(0))
# print(get_running_time_entries().text)
