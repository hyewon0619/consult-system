topic_model_registry = {}

def register_topic(topic_code: str):
    def wrapper(cls):
        topic_model_registry[topic_code] = cls
        return cls
    return wrapper

