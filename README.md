# speckle-load-collector
izzy lyseggen (izzylys)
14/02/2019

This simple script pulls data from speckle to calculate room gains and push them to a new results stream. User must be authenticated by creating a `speckleProfile.py` with their API token (see `sampleProfile.py`)

## for v2
A single stream is set up with the rooms as layers and the data as objects in each room layer. The room gain includes occupancy, lighting, small power, and fabric with a 10% safety factor. The number of rooms in the stream does not matter. The result is rounded based on specified rounding rules and pushed to a Load Calc Results v2 stream.

As is, the output writes layers for each room with a list of data for each room. The commented out section will push out layers for each piece of data with each layer only having one object.

## for v1
Each room is set up as a different stream and the `streamId` is specified in the script.