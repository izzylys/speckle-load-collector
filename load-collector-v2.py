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
def getSpeckleObjects(streamid):
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

def getSpeckleLists(streamid):
    stream = speck.StreamGetAsync(streamid)
    layers = stream['resource']['layers']
    layer_name = []
    for l in layers:
        layer_name.append(l['name'])

    values = []
    objects = stream['resource']['objects']
    for o in objects:
        values.append(speck.ObjectGetAsync(o['_id'])['resource']['value'])

    store = []
    length = int(len(objects)/len(layer_name))
    for i,layer in enumerate(layer_name):
        frame = {
            layer: values[i*length:i*length+length]
        }
        store.append(frame)
    return store


def calcGain(roomArea, designData,sf):
    sens_gain = designData['Room Occupancy [sqm/pers]']*designData['Watts per Occupant (sensible)']
    lat_gain = designData['Room Occupancy [sqm/pers]']*designData['Watts per Occupant (latent)']
    light_gain = roomArea*designData['Lighting Allowance [W/m2]']
    smallp_gain = roomArea*designData['Small Power Allowance [W/m2]']
    fab_gain = roomArea*designData['Fabric Allowance [W/m2]']
    tot = (sens_gain+lat_gain+light_gain+smallp_gain+fab_gain)*sf
    frame = {
        'Sensible': int(sens_gain),
        'Latent': int(lat_gain),
        'Lighting': int(light_gain),
        'Small Power': int(smallp_gain),
        'Fabric': int(fab_gain),
        'Total': int(tot),
    }
    return frame

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

# initial inputs (will be able to change later)
sf = 1.1        # safety factor
thresh = [0,100,1000,5000,20000]        # rounding threshold
step = [0,20,100,200,500,1000]          # rounding step size
out_stream = 'Lbjn7PdIKf'

# stream IDs
roomIDs = {
    'Room1': 'EBw4nQ7gD',
    'Room2': 'a9NLpf663j',
    'Room3': 'EUAxQF85Pn',
}
room_stream = 'Zzby8Jdnc1'
design_brief = '6TE2S1YBk'

# get room data and calculate the load in each room
load_results = {}
room_data = getSpeckleLists(room_stream)
design_data = getSpeckleObjects(design_brief)
for i,room in enumerate(room_data):
    raw_gain = calcGain(list(room.values())[0][0],design_data,sf)
    prev_gain = list(getSpeckleLists(out_stream)[i].values())[0][-1]
    raw_gain['Total'] = detwitchRounding(raw_gain['Total'],prev_gain)
    load_results[list(room.keys())[0]] = raw_gain

pprint(load_results)

#-----------------------------------------------------------------#
# Format the parameters 
params={ 
    'name': 'Load Calc Results',
    'description': 'This stream was updated from `load-collector-v2.py` by {} on {} \n\n The data is in the form \n\n `{}`'.format(creds['name'],datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),list(list(load_results.values())[0].keys())),
    'layers': [],
    'objects': [],
}


for i,(room,loads) in enumerate(load_results.items()):
    params['layers'].append({
        'name': room,
        'guid': str(uuid.uuid4()),
        'startIndex': i*len(loads),
        'objectCount': len(loads),
        'topology': '0-{}'.format(len(loads)),
    })
    for (name,value) in loads.items():
        params['objects'].append({'name': name, 'type': 'Number', 'value': value})

pprint(params)



# Update the stream
update = requests.put('https://hestia.speckle.works/api/v1/streams/{}'.format(out_stream), json = params, headers = headers)
print(update.json())



'''
for i,(room,loads) in enumerate(load_results.items()):
    params['layers'].append({
        'name': room,
        'guid': str(uuid.uuid4()),
        'startIndex': i*len(loads),
        'objectCount': len(loads),
        'topology': '0-{}'.format(len(loads)),
    })
    for val in loads.items():
        params['objects'].append({'type': 'Null', 'value': val})
'''