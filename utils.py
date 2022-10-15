def is_event_type_task(event_type: str):
    """Return true when event type is of type event

    Returns
    --------
    bool
        returns true when event type is of type event
    """
    return event_type and event_type.startswith("task-")


def serialize_event(event, event_fields):
    return {
        field: getattr(event, field) for field in event_fields if hasattr(event, field)
    }
