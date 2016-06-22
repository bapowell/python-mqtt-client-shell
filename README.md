# Python-based MQTT Client Shell

Written in Python *(works with Python 2 and 3)*, and using the [Eclipse Paho](http://eclipse.org/paho/) MQTT Python client library, this is an interactive MQTT client command shell.

## Purpose

The purpose of this utility is to provide a text console-based, interactive shell for exercising various tasks associated with MQTT client communications, including connecting to an MQTT server, subscribing to topics, and publishing messages.

Other MQTT client tools exist, such as [mqtt-spy](https://github.com/kamilfb/mqtt-spy), but they tend to be GUI-based. This project arose from the need for a quick and easy way to test MQTT communications from the command line, e.g. SSH session.

## Installation

### Dependencies

Other than Python itself, the only other dependency is the [Paho Python](http://www.eclipse.org/paho/clients/python/) client library.

### Install

* Copy the `mqtt_client_shell.py` file to your desired folder location.

* Install the Paho Python client, via PyPI.
  * Alternatively, if security restrictions prohibit installing Python packages in your environment, then the source (src/paho) can simply be copied into a `paho` subfolder in the same folder where the `mqtt_client_shell.py` file resides.

### Running

```
python  mqtt_client_shell.py  [optional playback file]
```

## Usage

(to-do)

## Built With

* Python [Cmd](https://docs.python.org/3/library/cmd.html) module
* [Eclipse Paho Python Client for MQTT](http://www.eclipse.org/paho/clients/python/)

## Tested Environments

* Ubuntu 14.04 - Python 2.7 and 3.4 (verify versions)
* ?? Ubuntu 16.04 - Python 2.7 and 3.4
* Red Hat Enterprise Linux 7 - Python 2.7
* Raspberry Pi - Raspbian - Python 2.7 and 3.4 (verify versions)
* Windows - Python 2.7 and 3.4

## Requests/Issues/Bugs

This project uses [GitHub Issues](https://github.com/bapowell/python-mqtt-client-shell/issues)
to track feature requests, to-dos, bugs, etc.

## Authors

* Brad Powell - [gh](https://github.com/bapowell), [in]( https://www.linkedin.com/in/bradpowell14)

## License

This project is licensed under the Eclipse Public License - see the [LICENSE](LICENSE) file for details.
