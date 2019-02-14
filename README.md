# speckle-load-collector
izzy lyseggen (izzylys)
14/02/2019

This simple script pulls data from speckle to calculate room gains and push them to a new results stream. User must be authenticated by creating a `speckleProfile.py` with their API token (see `sampleProfile.py`)

Each room is set up as a different stream and the `streamId` is specified in the script. The room gain includes occupancy, lighting, small power, and fabric with a 10% safety factor. The result is rounded based on specified rounding rules and pushed to a Load Calc Results stream. 