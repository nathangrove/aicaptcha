
# JSON schema for request validation
store_schema = {
    'type': 'object',
    'properties': {
        'data': {'type': 'string'},
        'session_id': {'type': 'string'}
    },
    'required': ['data']
}

update_schema = {
    'type': 'object',
    'properties': {
        'interaction_id': {'type': 'string'},
        'label': {'type': 'number'}
    },
    'required': ['interaction_id', 'label']
}

# JSON schema for interaction payload validation
interaction_payload_schema = {
    'type': 'object',
    'properties': {
        'interactions': {
            'type': 'object',
            'properties': {
                'mouseMovements': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'type': {
                                'type': 'string'
                            },
                            'x': {
                                'type': 'number'
                            }, 
                            'y': {
                                'type': 'number'
                            }, 
                            'time': {
                                'type': 'number'
                            }
                        }
                    }
                },
                'keyPresses': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'key': {
                                'type': 'string'
                            }, 
                            'time': {
                                'type': 'number'
                            }
                        }
                    }
                },
                'scrollEvents': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'deltaX': {
                                'type': 'number'
                            }, 
                            'deltaY': {
                                'type': 'number'
                            }, 
                            'time': {
                                'type': 'number'
                            }
                        }
                    }
                },
                'formInteractions': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'field': {
                                'type': 'string'
                            },
                            'time' :{
                                'type':'number'
                            }
                        }
                    }
                }
            }
        },
        'duration': {'type': 'number'},
        'loadTimestamp': {'type': 'number'},
        'userAgent': {'type': 'string'},
        'viewPort': {'type': 'object', 'properties': {'width': {'type': 'number'}, 'height': {'type': 'number'}}},
    },
    'required': ['interactions', 'duration', 'viewport', 'loadTimestamp']
}