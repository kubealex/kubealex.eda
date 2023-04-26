# Event Driven Automation Collection - kubealex.eda

This collection was born with the idea to group some plugins and resources that can be helpful in extending the Event Driven Automation collection.


## Plugins

The following plugins are included in the collection

| Name | Description |
|-|-|
| kubealex.eda.mqtt | Configure MQTT listener for events |

## Usage

A sample rulebook using *kubealex.eda.mqtt* plugin is shown below

    ---
    - name: Hello Events
        hosts: all
        sources:
        - kubealex.eda.mqtt:
            host: localhost
            port: 1883
            topic: anomaly-data-out
        rules:
        - name: Debug connection
        condition: event.sensor_location is defined
        action:
            debug: