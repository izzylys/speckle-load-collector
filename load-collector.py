# Izzy Lyseggen (izzylys)
# 12/02/2019
# load collector
import requests
import speckle
import uuid
import datetime
import simplejson as json
from pprint import pprint
from speckleProfile import creds, headers
#-----------------------------------------------------------------#
def getSpeckleRoomData(streamid):
    stream = speck.StreamGetAsync(streamid)
    layers = stream['resource']['layers']
    layer_name = []
    for l in layers:
        layer_name.append(l['name'])

    objects = stream['resource']['objects']
    values = []
    for o in objects:
        values.append(speck.ObjectGetAsync(o['_id'])['resource']['value'])
    
    results = dict(zip(layer_name, values))
    return results

def calcGain(roomData,sf):
    occ_gain = roomData['Room Occupancy']*roomData['Watts per Occupant (sensible)']
    light_gain = roomData['Room Area']*roomData['Lighting Allowance (W/m2)']
    smallp_gain = roomData['Room Area']*roomData['Small Power Allowance (W/m2)']
    fab_gain = roomData['Room Area']*roomData['Fabric Allowance (W/m2)']
    tot = (occ_gain+light_gain+smallp_gain+fab_gain)*sf
    return int(tot)

def detwitchRounding(gain, prevgain = ''):
    for i,j in enumerate(thresh):
        if gain <= j:
            base = step[i]
            val = int(base*round(gain/base))
            break
    if gain > thresh[-1]:
        val = int(step[-1]*round(gain/step[-1]))
    if prevgain != '':
        if abs(prevgain-gain) < base:
            val = int(base*round(prevgain/base))
    return val
#-----------------------------------------------------------------#
# start up PySpeckle and autenticate
speck = speckle.SpeckleApiClient()
speck.set_profile(creds['server'],creds['apitoken'])

# stream IDs for the room data
roomIDs = {
    'Room1': 'EBw4nQ7gD',
    'Room2': 'a9NLpf663j',
    'Room3': 'EUAxQF85Pn',
}

# initial inputs (will be able to change later)
sf = 1.1        # safety factor
thresh = [0,100,1000,5000,20000]        # rounding threshold
step = [0,20,100,200,500,1000]          # rounding step size
out_stream = 'ZLw_1GkWS2'

# get room data and calculate the load in each room
load_results = {}
for room, id in roomIDs.items():
    raw_gain = calcGain(getSpeckleRoomData(id),sf)
    gain = detwitchRounding(raw_gain)
    load_results[room] = gain

pprint(load_results)

#-----------------------------------------------------------------#
# Format the parameters 
params={
    'name': 'Load Calc Results',
    'description': 'This stream is updated from a python script `load-collector.py` on {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
),
    'layers': [],
    'objects': [],
}

for i, (room,load) in enumerate(load_results.items()):
    params['layers'].append({'name': room, 'guid': str(uuid.uuid4()), 'startIndex': i, 'objectCount': 1, 'topology': '0-1'})
    params['objects'].append({'type': 'Number', 'value': load})

# Update the stream
update = requests.put('https://hestia.speckle.works/api/v1/streams/{}'.format(out_stream), json = params, headers = headers)
print(update.json())
