# Tests
For defining tests to be written and tracking progress

# Worker
## AlfalfaConnections
1. What happens if init fails? i.e. environment variables not available?
    - These become exceptions to catch when instantiating?

## Worker
1. Best practice to put entire .run() method in a try/except block

### process_message
1. json.loads(message.body) doesn't work - how to handle?
2. In general, where are the valid values defined for (this validation should be made server side, correct?):
    - realtime, external_clock: 'true', 'undefined', no key, others...?
    - timescale: 'undefined', integer value wrapped as str, no key, others...?
    - start_datetime, end_datetime: 'undefined', datetime string format, no key, others...?

### check_message_body
1. Check that False is returned in following situations:
    - add_site: no osm_name or no upload_id
    - step_sim: no site_id
    - run_sim: no upload_filename or no upload_id

### check_subprocess_call
1. Message logged for:
    - success
    - unsuccessful

### add_site
1. Need to have defined OSW upload structure.  Structure validation occur in Worker or in add_osw.py?
1. Message logged when unsupported file type uploaded.

### step_sim
1. What happens if id can't be found in records?
1. atleast one of realtime, timescale, external_clock must be specified - else, doesn't run
1. no more than one of realtime, timescale, external_clock specified - else, doesn't run

#### check_step_sim_config
1. Berate with a whole bunch of configuration types of a message body.
- no expected parameters found?
- see process_message: what are expected values???
- start_datetime is changed if real_time specified
- start_datetime and end_datetime are default values when none specified
```
{
  'realtime': 'undefined',
  'endDatetime': '2019-11-23 23:59:00',
  'id': '5fa2f208-37d5-11ea-9461-644bf0128e04',
  'timescale': 'undefined',
  'op': 'InvokeAction',
  'action': 'runSite',
  'externalClock': 'true',
  'startDatetime': '2019-11-17 00:00:00'
}
```

### run_sim
1. Message logged when unsupported file type uploaded.

## General
1. For add_site, step_sim, run_sim, want a test to kill subprocess & make sure gets logged when incorrect return codes?
2. In the underlying add_site, step_sim, run_sim, will they all have the same environment variables avaialble to them, i.e. so they can use that AlfalfaConnections class?

# add_site

# step_sim
