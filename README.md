# speckle-load-collector
izzy lyseggen (izzylys)
14/02/2019

This simple script pulls data from speckle to calculate room gains and push them to a new results stream. User must be authenticated by creating a `speckleProfile.py` with their API token (see `sampleProfile.py`)

## for v2
A single stream is set up with the rooms as layers and the data as objects in each room layer. The room data includes area, facade length, and height. The stream can include as many rooms as you want.

The room gain is calculated by pulling parameters from a design brief stream and includes occupancy, lighting, small power, and fabric with a 10% safety factor. The result is rounded based on specified rounding rules and pushed to a Load Calc Results v2 stream.

As is, the output writes layers for each room with a list of results for each layer. Passing anything other than `'yes'` to the function `formatParameters()` will give you an output with each piece of data as its own layer.

## for v1
Each room is set up as a different stream and the `streamId` is specified in the script.