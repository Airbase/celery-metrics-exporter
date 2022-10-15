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
    - Datadog exporter → will start this for initial version
    - Postgres stores
- exporter must  impl `process_event` which is called by the receiver
- ideally exporter processing code would be started in different threads, to unblock celery event receiver.

### DataDogExporter Impl

- we will need to store all the events (atleast `pending`,  `received` , `success` , `failed` event) to compute  `wait_time` and `run_time`
- the `process_event` function add the event to the **Store** object, if the event is in its final, its added to the `processing_queue`
    - the **Store** has all events with `task-id` as key
    - there is a `processing_queue` where task-id succeeded / failed task are tracked
- once a `task-id` is present pushed to `processing_queue` , it picked by to be pushed to Datadog.

### PostgresExporterExporter Impl
- we will need to store metadata related to a task (like args, kwargs, queue, task_name, status)
- the `process_event` function adds the serialized event to a Queue
- a different runner thread picks up the event and upsert the task in Postgres
- Migration are managed using alembic
  - alembic config file is present inside exporters/postgres folder
  - Autogenerate models using the cmd: ``DATABASE_URL='<db_uri>' alembic --config exporters/postgres/alembic.ini revision --autogenerate -m "Update celery_meta table"``
  - Run migration using the cmd: ``DATABASE_URL='<db_uri>' alembic --config exporters/postgres/alembic.ini upgrade head``

### Cli

- initialize the **CeleryEventReceiver**, **Exporters**
- attach **Exporters** to **CeleryEventReceiver**
- starts the application
