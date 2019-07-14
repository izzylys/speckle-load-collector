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


def getSpeckleObjects(streamid: str) -> dict:
    '''pull speckle data if each layer has one object'''
    stream = speck.StreamGetAsync(streamid)
    layers = stream['resource']['layers']
    layer_name = [l['name'] for l in layers]

    objects = stream['resource']['objects']
    values = [
        speck.ObjectGetAsync(o['_id'])['resource']['value'] for o in objects
    ]

    results = dict(zip(layer_name, values))
    return results


def getSpeckleLists(streamid: str) -> dict:
    '''pull speckle data if each layer has several (but the same number) of objects'''
    stream = speck.StreamGetAsync(streamid)
    layers = stream['resource']['layers']
    layer_name = [l['name'] for l in layers]

    objects = stream['resource']['objects']
    values = [
        speck.ObjectGetAsync(o['_id'])['resource']['value'] for o in objects
    ]

    store = {}
    length = int(len(objects) / len(layer_name))
    for i, layer in enumerate(layer_name):
        store[layer] = list(values[i * length:i * length + length])
    return store


def calcGain(roomArea: float, designData: dict, sf: float) -> dict:
    '''calculate the room gains'''
    sens_gain = roomArea / float(
        designData['Room Occupancy [sqm/pers]']) * float(
            designData['Occ Sens [W/pers]'])
    lat_gain = roomArea / float(
        designData['Room Occupancy [sqm/pers]']) * float(
            designData['Occ Lat [W/pers]'])
    light_gain = roomArea * float(designData['Lighting Allowance [W/m2]'])
    smallp_gain = roomArea * float(designData['Small Power Allowance [W/m2]'])
    fab_gain = roomArea * float(designData['Fabric Allowance [W/m2]'])
    tot = (sens_gain + lat_gain + light_gain + smallp_gain + fab_gain) * sf
    frame = {
        'Sensible': int(sens_gain),
        'Latent': int(lat_gain),
        'Lighting': int(light_gain),
        'Small Power': int(smallp_gain),
        'Fabric': int(fab_gain),
        'Total': int(tot),
    }
    return frame


def stableRounding(th: list = [0, 100, 1000, 5000, 20000],
                   step: list = [0, 20, 100, 200, 500, 1000],
                   gain: int,
                   prevgain: int = None) -> int:
    '''apply rounding rules to stabalize results
    `th` is a list of the rounding thresholds
    `step` is the max step before the value will change
    '''
    for i, j in enumerate(th):
        if gain <= j:
            base = step[i]
            val = int(base * round(gain / base))
            break
    if gain > th[-1]:
        val = int(step[-1] * round(gain / step[-1]))
    if prevgain:
        if abs(prevgain - gain) < base:
            val = int(base * round(prevgain / base))
    return val


def formatParams(data: dict, lists_yes_no: str = 'yes') -> dict:
    '''format the parameters to be accepted into speckle stream
    "yes" for lists for each room layer
    '''
    params = {
        'name': 'Load Calc Results v2',
        'description': '',
        'layers': [],
        'objects': [],
    }

    if lists_yes_no == 'yes':
        params[
            'description'] = 'This stream was updated from `load-collector.py` by {} on {} \n\n '.format(
                creds['name'],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        for i, name in enumerate(data[0][1].keys()):
            params['layers'].append({
                'name': name,
                'guid': str(uuid.uuid4()),
                'startIndex': i * len(data),
                'objectCount': len(data),
                'topology': '0-{}'.format(len(data)),
                'orderIndex': i
            })
            for room in data:
                params['objects'].append({
                    'name': name,
                    'type': 'Number',
                    'value': room[1][name]
                })

    else:
        params[
            'description'] = 'This stream was updated from `load-collector.py` by {} on {}'.format(
                creds['name'],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        for i, room in enumerate(data):
            for j, (name, value) in enumerate(room[1].items()):
                params['layers'].append({
                    'name': room[0] + ' ' + name,
                    'guid': str(uuid.uuid4()),
                    'startIndex': j + i,
                    'objectCount': 1,
                    'topology': '0-1'
                })
                params['objects'].append({'type': 'Number', 'value': value})

    return params


#-----------------------------------------------------------------#
# start up PySpeckle and autenticate
speck = speckle.SpeckleApiClient()
speck.set_profile(creds['server'], creds['apitoken'])

# initial inputs (will be able to change later)
sf = 1.1  # safety factor

# stream IDs
if input('Enter your own streams? (Y/N):  ') == 'Y':
    room_stream = input('Room Stream ID:')
    design_brief = input('Design Brief Stream ID:')
    out_stream = input('Output Stream ID:')
else:

    room_stream = 'y2DlFS1Yt'
    design_brief = '6TE2S1YBk'
    out_stream = 'dP-bQxpez'

room_data = getSpeckleLists(room_stream)
design_data = getSpeckleObjects(design_brief)
try:
    store_prev = getSpeckleLists(out_stream)['Total']
except:
    pass
load_results = []

for i, area in enumerate(room_data['area']):
    raw_gain = calcGain(area, design_data, sf)
    try:
        prev_gain = int(store_prev[i])
        raw_gain['Total'] = stableRounding(raw_gain['Total'], prev_gain)
    except:
        raw_gain['Total'] = stableRounding(raw_gain['Total'])
        pass
    load_results.append((room_data['name'][i], raw_gain))

#-----------------------------------------------------------------#
# Format the parameters
# 'yes' if you would like layers for each room and lists in each layer with results
params = formatParams(load_results)

update = requests.put(
    f'https://hestia.speckle.works/api/v1/streams/{out_stream}',
    json=params,
    headers=headers)
print(update.json())
