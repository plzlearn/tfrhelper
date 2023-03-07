import json
import os
from datetime import datetime

def load_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_json_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_thread_choices():
    threads_file = os.path.join(os.path.dirname(__file__), '../threads.json')
    thread_choices = load_json_file(threads_file)
    now = datetime.now()
    valid_threads = []
    for thread_name, thread_date_str in thread_choices.items():
        thread_date = datetime.strptime(thread_date_str, '%Y-%m-%d')
        if (now - thread_date).days <= 7:
            valid_threads.append(thread_name)
    return valid_threads

def add_thread_choice(thread_name):
    threads_file = os.path.join(os.path.dirname(__file__), '../threads.json')
    thread_choices = load_json_file(threads_file)
    thread_choices[thread_name] = datetime.now().strftime('%Y-%m-%d')
    save_json_file(threads_file, thread_choices)

def add_event(event):
    events_file = os.path.join(os.path.dirname(__file__), '../events.json')
    events = load_json_file(events_file)
    if isinstance(events, dict):
        events = [events]
    events.append(event)
    save_json_file(events_file, events)

def remove_event(event_text):
    events_file = os.path.join(os.path.dirname(__file__), '../events.json')
    events = load_json_file(events_file)
    for i in range(len(events)):
        if events[i]['event_text'][:100] == event_text[:100]:
            del events[i]
            break
    save_json_file(events_file, events)

def get_events():
    events_file = os.path.join(os.path.dirname(__file__), '../events.json')
    events = load_json_file(events_file)
    now = datetime.now().strftime('%m/%d')
    valid_events = []
    for event in events:
        event_date_str = event['event_date']
        if event_date_str >= now:
            valid_events.append(event)
    return valid_events