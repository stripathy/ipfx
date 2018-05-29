import json
import os
import allensdk.internal.core.lims_utilities as lu
import sys

import allensdk.ipfx.ephys_data_set as eds
import allensdk.ipfx.qc_features as qcf
import allensdk.core.json_utilities as ju
import os.path

specimen_id = int(sys.argv[1])
cell_dir = sys.argv[2]

res = lu.query("""
select err.storage_directory||'EPHYS_FEATURE_EXTRACTION_V2_QUEUE_'||err.id||'_input.json' as input_v2_json,
       err.storage_directory||'EPHYS_FEATURE_EXTRACTION_QUEUE_'||err.id||'_input.json' as input_v1_json,
       err.storage_directory||err.id||'.nwb' as nwb_file
from specimens sp
join ephys_roi_results err on err.id = sp.ephys_roi_result_id
where sp.id = %d
""" % specimen_id)[0]

res = { k.decode('UTF-8'):v for k,v in res.items() }

# query for the h5 file
res2 = lu.query("""
select err.*, wkf.*,sp.name as specimen_name 
from ephys_roi_results err 
join specimens sp on sp.ephys_roi_result_id = err.id 
join well_known_files wkf on wkf.attachable_id = err.id 
where sp.id = %d 
and wkf.well_known_file_type_id = 306905526
""" % specimen_id)[0]

h5_file_name = os.path.join(res2['storage_directory'], res2['filename'])

res["h5_file"] = h5_file_name

# if the input_v2_json does not exist, then use input_v1_json instead:
if os.path.isfile(res["input_v2_json"]):
    res["input_json"] = res["input_v2_json"]
else:
    res["input_json"] = res["input_v1_json"]


with open(res['input_json'], 'r') as f:
    d = json.load(f)

stimulus_ontology_file = eds.DEFAULT_STIMULUS_ONTOLOGY_FILE

if not os.path.exists(cell_dir):
    os.makedirs(cell_dir)

d = {}

if os.path.exists(res['h5_file']):
    d['input_h5_file'] = res['h5_file']

d['input_nwb_file'] = res['nwb_file']
d['output_nwb_file'] = os.path.join(cell_dir, "output.nwb")
d['qc_fig_dir'] = os.path.join(cell_dir,"qc_figs")
d['stimulus_ontology_file'] = stimulus_ontology_file
d['qc_criteria'] = ju.read(qcf.DEFAULT_QC_CRITERIA_FILE)
d['specimen_id'] = specimen_id


with open(os.path.join(cell_dir, 'pipeline_input.json'), 'w') as f:
    f.write(json.dumps(d, indent=2))