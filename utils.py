def is_event_type_task(event_type: str):
    return event_type and event_type.startswith("task-")
