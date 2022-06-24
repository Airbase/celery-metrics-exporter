# celery-metrics-exporter

## Components

### CeleryEventReceiver

- this is components listening the celery events
- this is where the any filter for events would live
- receiver maintains a list of the exporters
- on receiving a event it calls all the exporters to process the event

### Exporter

- this is components picks up events, processes it
- the plan is to support
    - Datadog stores → will start this for initial version
    - Postgres stores
- exporter must  impl `process_event` which is called by the receiver
- ideally exporter processing code would be started in different threads, to unblock celery event receiver.

### DataDogExporter Impl

- we will need to store all the events (atleast `pending`,  `received` , `success` , `failed` event) to compute  `wait_time` and `run_time`
- the `process_event` function add the event to the **Store** object, if the event is in its final, its added to the `processing_queue`
    - the **Store** has all events with `task-id` as key
    - there is a `processing_queue` where task-id succeeded / failed task are tracked
- once a `task-id` is present pushed to `processing_queue` , it picked by to be pushed to Datadog.

### Cli

- initialize the **CeleryEventReceiver**, **Exporters**
- attach **Exporters** to **CeleryEventReceiver**
- starts the application
