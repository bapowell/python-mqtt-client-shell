# Python-based MQTT Client Shell

Written in Python *(works with Python 2 and 3)*, and using the [Eclipse Paho](http://eclipse.org/paho/) MQTT Python client library, this is an interactive MQTT client command shell.

## Purpose

The purpose of this utility is to provide a text console-based, interactive shell for exercising various tasks associated with MQTT client communications, including connecting to an MQTT server, subscribing to topics, and publishing messages.

Other MQTT client tools exist, such as [mqtt-spy](https://github.com/kamilfb/mqtt-spy), but they tend to be GUI-based. This project arose from the need for a quick and easy way to test MQTT communications from the command line, e.g. terminal/SSH session.

## Getting Started

### Dependencies

Other than Python itself, the only other dependency is the [Paho Python](http://www.eclipse.org/paho/clients/python/) client library.

### Installation

* Copy the `mqtt_client_shell.py` file to your desired folder location.

* Install the Paho Python client, via PyPI.
  * Alternatively, if security restrictions prohibit installing Python packages in your environment, then the source (src/paho) can simply be copied into a `paho` subfolder in the same folder where the `mqtt_client_shell.py` file resides.

### Running

```
python mqtt_client_shell.py [optional playback file]
```

## Usage

### Basics

The program implements a set of nested *sub* shells (i.e. consoles):

1. Upon startup the initial shell is the **Main** (i.e. Client) shell, where changes can be made to MQTT client parameters, e.g. client_id, protocol version, etc.

2. From the Main shell, the *connection* command takes you to the **Connection** shell, which handles the setting of MQTT connection parameters, e.g. host, port, username, etc.

3. From the Connection shell, the *connect* command initiates a connection to the MQTT server, and then takes you to the **Messaging** shell, for performing pub/sub messaging via the active MQTT connection.

#### Help

Enter ```help``` or ```?``` to show a list of commands that are valid at that point.

To get help for a particular command, enter ```help``` (or ```?```) followed by the command, e.g. ```help publish```.

#### Command Completion and History

If your system supports it (Windows doesn't support TAB completion), then, when entering commands, the TAB key will let the shell try to complete the command or propose alternatives.

Additionally, the up/down arrow keys can be used to cycle through the command history.

#### Exit

Typing ```exit``` or ```quit``` (or pressing Ctrl-D, for those systems supporting it) will exit the current shell. If at the Main shell, then this will quit the program.

### Sample Session

Below is a sample session showing the basics: connecting to an MQTT server, subscribing to all topics (#), and publishing a message. To clarify, once the program was started, the following commands, entered in succession, produced the sample session:

logging off  
connection  
connect  
subscribe #  
publish test/a "hi, world"  
exit  
exit  
exit

```
$ python mqtt_client_shell.py

Welcome to the MQTT client shell.
Type help or ? to list commands.
Pressing <Enter> on an empty line will repeat the last command.

Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: on (indent=30), Recording: off, Pacing: 0
> logging off

Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> connection

Connection args: host=localhost, port=1883, keepalive=60, bind_address=, username=, password=, will=None
Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> connect

***CONNECTED***
Subscriptions:
Connection args: host=localhost, port=1883, keepalive=60, bind_address=, username=, password=, will=None
Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> subscribe #
...msg_id=1, result=0 (No error.)

***CONNECTED***
Subscriptions: (topic=#,qos=0)
Connection args: host=localhost, port=1883, keepalive=60, bind_address=, username=, password=, will=None
Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> publish test/a "hi, world"
...msg_id=2, result=0 (No error.)
                              on_message(): message received: Topic: test/a, QoS: 0, Payload Length: 9
                                                              Payload (str): b'hi, world'
                                                              Payload (hex): b'68692c20776f726c64'

***CONNECTED***
Subscriptions: (topic=#,qos=0)
Connection args: host=localhost, port=1883, keepalive=60, bind_address=, username=, password=, will=None
Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> exit

Connection args: host=localhost, port=1883, keepalive=60, bind_address=, username=, password=, will=None
Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> exit

Client args: client_id=paho-9241-mypc, clean_session=True, protocol=4 (MQTTv3.1.1)
Logging: off, Recording: off, Pacing: 0
> exit
$
```

## Commands

### Global Commands

These commands work in any of the (sub) shells, i.e. consoles.

#### logging *[on | off]*
Turn on/off the display of MQTT client callback messages.
* If on/off argument is not specified, then the setting is toggled.
* Note that this doesn't affect the on_message callback, which always logs when a message is received.
* See ```logging_indent``` command.

#### logging_indent *#spaces*
Control the indentation for the callback messages. This is helpful to distinguish callback messages from the interactive shell input/output.

#### prompt_verbosity *[N | L | M | H]*
Set the amount of detail displayed in the shell prompt: 'N'one, 'L'ow, 'M'edium, 'H'igh.
* If argument is not specified, then setting is reset to default ('H'igh).
* A high verbosity will show essentially all current settings.

#### record *file*
Start recording commands to the given file.
* If the file exists, then commands will be appended to it.

#### stop_recording
Stop recording commands, if currently recording commands to a file.

#### playback *file*
Play back commands from the given file.
* When executing the MQTT shell, a playback file may be specified on the command line, e.g. ```python mqtt_client_shell.py connectsubscribe.cmd```, in which case commands are played back from the given file immediately upon execution.
* See ```pacing``` command.

#### pacing *delay*
Set a delay between commands, when playing back commands from a file.
* A fractional delay value is supported, e.g. 1.5 (seconds).

#### Side note: Scripting

Interestingly, on Unix-like systems that support named pipes, i.e. FIFO, the playback command functionality offers a way to do rudimentary scripting with the MQTT shell. For instance:

Create a FIFO file:
```bash
$ mkfifo test1.fifo
```
Create a shell script, e.g. *publoop.sh*, with the following content:
```bash
#!/bin/bash
F=test1.fifo
SECS=0
echo 'pacing 1.0' > $F
echo 'connection' > $F
echo 'connect' > $F
echo 'subscribe #' > $F
echo 'logging off' > $F
echo 'publish test hi' > $F
COUNTER=0
while [ $COUNTER -lt 5 ]; do
    echo publish test $COUNTER > $F
    sleep $SECS
    let COUNTER=COUNTER+1
done
echo 'exit' > $F
echo 'exit' > $F
echo 'exit' > $F
```
Run the MQTT shell, specifying the FIFO as the playback file:
```bash
$ python mqtt_client_shell.py test1.fifo
```
Finally, in another terminal session, execute the *publoop.sh* script:
```bash
$ sh ./publoop.sh
```
Assuming there's an MQTT server running on localhost, running this will connect to that server, subscribe to all messages, publish a set of test messages, and then cause the MQTT shell to exit back to the command line.

### Main Console Commands

Upon program startup, this is the shell, i.e. console, that is active. It's purpose is to set the MQTT client parameters, before establishing a connection. In addition to the global commands listed above, the following commands are enabled.

#### client_id *[id]*
Set the MQTT client ID.
* If id argument is not specified, then the default id that was established on program startup is used.

#### clean_session *[true | false]*
Enable/disable the MQTT *clean session* setting (default: true)
* If true/false argument is not specified, then the setting is toggled.

#### protocol *[version]*
Set the version of the MQTT protocol to be used.
* Use help, ```help protocol```, to see the versions available.
* If version argument is not specified, then the version is set back to default.

#### connection
Establish an MQTT client, using the current client settings, and go to the Connection console.

### Connection Console Commands


### Messaging Console Commands



## Built With

* Python [Cmd](https://docs.python.org/3/library/cmd.html) module
* [Eclipse Paho Python Client for MQTT](http://www.eclipse.org/paho/clients/python/)

## Tested Environments

* Ubuntu 14.04 LTS - Python 2.7 and 3.4
* Ubuntu 16.04 LTS - Python 2.7 and 3.5
* Red Hat Enterprise Linux 7 - Python 2.7
* Raspberry Pi - Raspbian - Python 2.7 and 3.4
* Windows - Python 2.7 and 3.4

## Requests/Issues/Bugs

This project uses [GitHub Issues](https://github.com/bapowell/python-mqtt-client-shell/issues)
to track feature requests, to-dos, bugs, etc.

## Authors

* Brad Powell - [gh](https://github.com/bapowell), [in]( https://www.linkedin.com/in/bradpowell14)

## License

This project is licensed under the Eclipse Public License - see the [LICENSE](LICENSE) file for details.
