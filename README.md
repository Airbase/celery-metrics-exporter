# celery-metrics-exporter

## Components

### CeleryEventReceiver
- this is component listening the celery events
    - runs as a separate thread
- any filters worker related events
- stores the events in the **Store** with task-id as key

### Exporter
- this is components picks up events, summary as events as requirement by the data source and push it to datastore
- the plan is to support
    - Datadog stores → will start this for initial version
    - Postgres stores
- the exporters will be started as different threads as well.

### Store
- this acts as the buffer components between CeleryEventReceiver and Exporters
- this has a `event_store` with `task-id` as key and different events as value
- a `processing_queue` where task-id succeeded / failed task are pushed to be picked by the exporters

### Cli
- initialize the **Store**, **CeleryEventReceiver**, **Exporters** and starts the application
