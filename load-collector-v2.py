# Izzy Lyseggen (izzylys)
# 12/02/2019
# load collector
import requests
import speckle
import uuid
import datetime
import simplejson as json
from pprint import pprint
import collections as c
from speckleProfile import creds, headers
#-----------------------------------------------------------------#
# pull speckle data if each layer has one object
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

# pull speckle data if each layer has several (but the same number) of objects
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

    store = {}
    length = int(len(objects)/len(layer_name))
    for i,layer in enumerate(layer_name):
        store[layer] = list(values[i*length:i*length+length])
    return store

# calculate the room gain
def calcGain(roomArea, designData,sf):
    sens_gain = roomArea/float(designData['Room Occupancy [sqm/pers]'])*float(designData['Occ Sens [W/pers]'])
    lat_gain = roomArea/float(designData['Room Occupancy [sqm/pers]'])*float(designData['Occ Lat [W/pers]'])
    light_gain = roomArea*float(designData['Lighting Allowance [W/m2]'])
    smallp_gain = roomArea*float(designData['Small Power Allowance [W/m2]'])
    fab_gain = roomArea*float(designData['Fabric Allowance [W/m2]'])
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

# apply rounding rules to stabalize results
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

# format the parameters in the appropriate way
def formatParams(data,lists_yes_no):    # 'yes' for lists for each room layer
    params={ 
    'name': 'Load Calc Results v2',
    'description': '',
    'layers': [],
    'objects': [],
    }

    if lists_yes_no == 'yes':
        params['description'] = 'This stream was updated from `load-collector-v2.py` by {} on {} \n\n '.format(creds['name'],datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        for i,name in enumerate(data[0][1].keys()):
            params['layers'].append({
                'name': name,
                'guid': str(uuid.uuid4()),
                'startIndex': i*len(data),
                'objectCount': len(data),
                'topology': '0-{}'.format(len(data)),
                'orderIndex': i
            })
            for room in data:
                params['objects'].append({'name': name, 'type': 'Number', 'value': room[1][name]})
    '''
    broken after transposed output format -- will fix later
    else:
        params['description'] = 'This stream was updated from `load-collector-v2.py` by {} on {}'.format(creds['name'],datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        for i,(room,loads) in enumerate(data.items()):
            for j,(name,value) in enumerate(loads.items()):
                params['layers'].append({
                    'name': room+' '+name,
                    'guid': str(uuid.uuid4()),
                    'startIndex': j+i*len(loads), 
                    'objectCount': len(loads), 
                    'topology': '0-{}'.format(len(loads))
                })
                params['objects'].append({'type': 'Number', 'value': value})
    '''
    return params
#-----------------------------------------------------------------#
# start up PySpeckle and autenticate
speck = speckle.SpeckleApiClient()
speck.set_profile(creds['server'],creds['apitoken'])

# initial inputs (will be able to change later)
sf = 1.1        # safety factor
thresh = [0,100,1000,5000,20000]        # rounding threshold
step = [0,20,100,200,500,1000]          # rounding step size

# stream IDs
if input('Enter your own streams? (Y/N):  ') == 'Y':
    room_stream = input('Room Stream ID:')
    design_brief = input('Design Brief Stream ID:')
    out_stream = input('Output Stream ID:')
else:
    '''
    room_stream = 'y2DlFS1Yt'
    design_brief = '6TE2S1YBk'
    out_stream = 'dP-bQxpez'
    '''
    room_stream = 'Zzby8Jdnc1'
    design_brief = '6TE2S1YBk'
    out_stream = 'Lbjn7PdIKf'

# get room data and calculate the load in each room
room_data = getSpeckleLists(room_stream)
# pprint(room_data)
design_data = getSpeckleObjects(design_brief)
try:
    store_prev = getSpeckleLists(out_stream)['Total']
except:
    pass
load_results = []
for i,area in enumerate(room_data['area']):
    raw_gain = calcGain(area,design_data,sf)
    try:
        prev_gain = int(store_prev[i])
        raw_gain['Total'] = detwitchRounding(raw_gain['Total'],prev_gain)
    except:
        raw_gain['Total'] = detwitchRounding(raw_gain['Total'])
        pass
    load_results.append((room_data['name'][i], raw_gain))

#-----------------------------------------------------------------#
# Format the parameters 
# 'yes' if you would like layers for each room and lists in each layer with results
params = formatParams(load_results,'yes')

# Update the stream
update = requests.put('https://hestia.speckle.works/api/v1/streams/{}'.format(out_stream), json = params, headers = headers)
print(update.json())

