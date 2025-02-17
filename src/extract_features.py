from typing import List, Dict
import math

class UserInteractionData:
    def __init__(self, 
        mouse_movements: List[Dict[str, float]], 
        key_presses: List[Dict[str, float]], 
        scroll_events: List[Dict[str, float]], 
        form_interactions: List[Dict[str, float]], 
        touch_events: List[Dict[str, float]], 
        mouse_clicks: List[Dict[str, float]], 
        duration: float
    ):
        self.mouse_movements = mouse_movements
        self.key_presses = key_presses
        self.scroll_events = scroll_events
        self.form_interactions = form_interactions
        self.touch_events = touch_events
        self.mouse_clicks = mouse_clicks
        self.duration = duration

class ExtractedFeatures:
    def __init__(self, 
        avg_mouse_speed: float, 
        avg_key_press_interval: float, 
        avg_scroll_speed: float, 
        form_completion_time: float, 
        interaction_count: int, 
        mouse_linearity: float, 
        avg_touch_pressure: float, 
        avg_touch_movement: float, 
        avg_click_duration: float, 
        avg_touch_duration: float, 
        duration: float
    ):
        self.avg_mouse_speed = avg_mouse_speed
        self.avg_key_press_interval = avg_key_press_interval
        self.avg_scroll_speed = avg_scroll_speed
        self.form_completion_time = form_completion_time
        self.interaction_count = interaction_count
        self.mouse_linearity = mouse_linearity
        self.avg_touch_pressure = avg_touch_pressure
        self.avg_touch_movement = avg_touch_movement
        self.avg_click_duration = avg_click_duration
        self.avg_touch_duration = avg_touch_duration
        self.duration = duration


def extract_features(data: UserInteractionData) -> ExtractedFeatures:
    avg_mouse_speed = calculate_avg_mouse_speed(data.mouse_movements)
    avg_key_press_interval = calculate_avg_key_press_interval(data.key_presses)
    avg_scroll_speed = calculate_avg_scroll_speed(data.scroll_events)
    form_completion_time = calculate_form_completion_time(data.form_interactions)
    interaction_count = len(data.mouse_movements) + len(data.key_presses) + len(data.scroll_events) + len(data.form_interactions) + len(data.touch_events) + len(data.mouse_clicks)
    mouse_linearity = calculate_mouse_linearity(data.mouse_movements)
    avg_touch_pressure = calculate_avg_touch_pressure(data.touch_events)
    avg_touch_movement = calculate_avg_touch_movement(data.touch_events)
    avg_click_duration = calculate_avg_click_duration(data.mouse_clicks)
    avg_touch_duration = calculate_avg_touch_duration(data.touch_events)

    return ExtractedFeatures(
        avg_mouse_speed,
        avg_key_press_interval,
        avg_scroll_speed,
        form_completion_time,
        interaction_count,
        mouse_linearity,
        avg_touch_pressure,
        avg_touch_movement,
        avg_click_duration,
        avg_touch_duration,
        data.duration
    )


def calculate_avg_mouse_speed(mouse_movements: List[Dict[str, float]]) -> float:
    if len(mouse_movements) < 2:
        return 0
    total_distance = 0
    total_time = 0
    for i in range(1, len(mouse_movements)):
        dx = mouse_movements[i]['x'] - mouse_movements[i - 1]['x']
        dy = mouse_movements[i]['y'] - mouse_movements[i - 1]['y']
        dt = mouse_movements[i]['time'] - mouse_movements[i - 1]['time']
        total_distance += math.sqrt(dx * dx + dy * dy)
        total_time += dt
    return total_distance / total_time


def calculate_avg_key_press_interval(key_presses: List[Dict[str, float]]) -> float:
    if len(key_presses) < 2:
        return 0
    total_interval = 0
    for i in range(1, len(key_presses)):
        total_interval += key_presses[i]['time'] - key_presses[i - 1]['time']
    return total_interval / (len(key_presses) - 1)


def calculate_avg_scroll_speed(scroll_events: List[Dict[str, float]]) -> float:
    if len(scroll_events) < 2:
        return 0
    total_scroll = 0
    total_time = 0
    for i in range(1, len(scroll_events)):
        ds = scroll_events[i]['scrollTop'] - scroll_events[i - 1]['scrollTop']
        dt = scroll_events[i]['time'] - scroll_events[i - 1]['time']
        total_scroll += abs(ds)
        total_time += dt
    return total_scroll / total_time


def calculate_form_completion_time(form_interactions: List[Dict[str, float]]) -> float:
    if len(form_interactions) < 2:
        return 0
    return form_interactions[-1]['time'] - form_interactions[0]['time']


def calculate_mouse_linearity(mouse_movements: List[Dict[str, float]]) -> float:
    if len(mouse_movements) < 2:
        return 0
    start_x = mouse_movements[0]['x']
    start_y = mouse_movements[0]['y']
    end_x = mouse_movements[-1]['x']
    end_y = mouse_movements[-1]['y']
    total_distance = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

    actual_distance = 0
    for i in range(1, len(mouse_movements)):
        dx = mouse_movements[i]['x'] - mouse_movements[i - 1]['x']
        dy = mouse_movements[i]['y'] - mouse_movements[i - 1]['y']
        actual_distance += math.sqrt(dx * dx + dy * dy)

    return total_distance / actual_distance


def calculate_avg_touch_pressure(touch_events: List[Dict[str, float]]) -> float:
    if len(touch_events) == 0:
        return 0
    total_pressure = sum(event['force'] for event in touch_events)
    return total_pressure / len(touch_events)


def calculate_avg_touch_movement(touch_events: List[Dict[str, float]]) -> float:
    if len(touch_events) < 2:
        return 0
    total_movement = 0
    for i in range(1, len(touch_events)):
        dx = touch_events[i]['x'] - touch_events[i - 1]['x']
        dy = touch_events[i]['y'] - touch_events[i - 1]['y']
        total_movement += math.sqrt(dx * dx + dy * dy)
    return total_movement / (len(touch_events) - 1)


def calculate_avg_click_duration(mouse_clicks: List[Dict[str, float]]) -> float:
    if len(mouse_clicks) < 2:
        return 0
    total_duration = 0
    click_count = 0
    for i in range(1, len(mouse_clicks)):
        if 'type' in mouse_clicks[i] and 'type' in mouse_clicks[i - 1]:
            if mouse_clicks[i]['type'] == 'up' and mouse_clicks[i - 1]['type'] == 'down':
                total_duration += mouse_clicks[i]['time'] - mouse_clicks[i - 1]['time']
                click_count += 1
    return total_duration / click_count if click_count > 0 else 0


def calculate_avg_touch_duration(touch_events: List[Dict[str, float]]) -> float:
    if len(touch_events) < 2:
        return 0
    total_duration = 0
    touch_count = 0
    for i in range(1, len(touch_events)):
        if touch_events[i]['type'] == 'end' and touch_events[i - 1]['type'] == 'start':
            total_duration += touch_events[i]['time'] - touch_events[i - 1]['time']
            touch_count += 1
    return total_duration / touch_count if touch_count > 0 else 0
