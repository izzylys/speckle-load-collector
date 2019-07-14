# speckle-load-collector

izzy lyseggen (izzylys)
14/02/2019

This simple script pulls data from speckle to calculate room gains and push them to a new results stream. It was written for the Speckle Workflow shown at the MSSN ADC in Madrid.

User must be authenticated by creating a `speckleProfile.py` with their API token (see `sampleProfile.py`)

A single stream is set up with the room data as layers (area, facade length, and height). The data is stored in each layer as a list with the index corresponding to the room number.

The room gain is calculated by pulling parameters from a design brief stream and includes occupancy, lighting, small power, and fabric with a 10% safety factor. The result is rounded based on specified rounding rules and pushed to a Load Calc Results v2 stream.

As is, the output writes layers for each load type with a list of results for the all the rooms in each layer. Passing anything other than `'yes'` to the function `formatParameters()` will give you an output with each piece of data as its own layer.
