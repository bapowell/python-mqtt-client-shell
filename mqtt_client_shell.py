"""
MQTT Client Shell Utility

@author: Brad Powell
"""
import cmd
import sys
import traceback
import socket
import random
import getpass
import shlex
import binascii
import time
from collections import namedtuple
import paho.mqtt.client as mqtt

# Normalization, to handle Python 2 or 3:
# In Python 3, input  behaves like raw_input in Python2, and the raw_input function does not exist.
input = getattr(__builtins__, 'raw_input', input)
# The urllib modules were restructured in Python 3.
if sys.version_info[0] == 2:
    import urllib2 as urlreq
    from urllib2 import URLError
else:
    import urllib.request as urlreq
    from urllib.error import URLError


def str2bool(s, default=None, msg=None):
    """Helper function to return True/False, based on the given string."""
    b = default
    if s:
        s = s.strip().lower()
        if s in ('true', 't', 'yes', 'y', 'on', 'enable', '1'):
            b = True
        elif s in ('false', 'f', 'no', 'n', 'off', 'disable', '0'):
            b = False
        else:
            print("Invalid value{}; should be True/False, Yes/No, On/Off, Enable/Disable, or 1/0. Defaulting to {}.".
                  format((msg and ' (' + msg + ')' or ''), default))
    return b    


def isfloat(value):
    """Helper function to test if the given argument, e.g. a string, can be converted to a float."""
    try:
        float(value)
        return True
    except ValueError:
        return False


# MQTT client callback functions:
# The userdata object is set to a ConsoleContext instance. 
# -----------------------------------------------------------------------------
def on_connect(mqttclient, userdata, flags, rc):
    if userdata.logging_enabled:
        print("on_connect(): result code = {} ({})".format(rc, mqtt.connack_string(rc)))

def on_disconnect(mqttclient, userdata, rc):
    if userdata.logging_enabled:
        print("on_disconnect(): result code = {}".format(rc))

def on_message(mqttclient, userdata, msg):
    print("on_message(): message received: Topic: {}, QoS: {}, Payload Length: {}".format(msg.topic, msg.qos, len(msg.payload)))
    print("                                Payload (str): {}".format(str(msg.payload)))
    print("                                Payload (hex): {}".format(binascii.hexlify(msg.payload)))

def on_publish(mqttclient, userdata, mid):
    if userdata.logging_enabled:
        print("on_publish(): message published: msg id = {}".format(mid))

def on_subscribe(mqttclient, userdata, mid, granted_qos):
    if userdata.logging_enabled:
        print("on_subscribe(): subscribed: msg id = {}, granted_qos = {}".format(mid, granted_qos))

def on_unsubscribe(mqttclient, userdata, mid):
    if userdata.logging_enabled:
        print("on_unsubscribe(): unsubscribed: msg id = {}".format(mid))

def on_log(mqttclient, userdata, level, string):
    if userdata.logging_enabled:
        print("on_log(): level={} - {}".format(level, string))
# -----------------------------------------------------------------------------


Message = namedtuple('Message', ['topic', 'payload', 'qos', 'retain'])

Subscription = namedtuple('Subscription', ['topic', 'qos'])


class ClientArgs(object):
    """Container to manage arguments for an mqtt.Client object."""
    
    mqtt_protocol_versions = {mqtt.MQTTv31:"MQTTv3.1", mqtt.MQTTv311:"MQTTv3.1.1"}
    mqtt_protocol_versions_str = ", ".join("{} for {}".format(k, v) for (k, v) in mqtt_protocol_versions.items())
    
    def __init__(self, client_id="", clean_session=True, protocol=None):
        """Initialize ClientArgs with default or passed-in values."""
        self._default_client_id = ("paho-" + str(random.randrange(1000, 10000)) + "-" + socket.gethostname())[:23]
        self.client_id = client_id
        self.clean_session = clean_session
        self._default_protocol = mqtt.MQTTv311
        self.protocol = protocol

    @property
    def client_id(self):
        return self._client_id
    
    @client_id.setter
    def client_id(self, value):
        self._client_id = value or self._default_client_id
        
    @property
    def clean_session(self):
        return self._clean_session
    
    @clean_session.setter
    def clean_session(self, value):
        if not value:
            # toggle
            self._clean_session = not self._clean_session
        elif type(value) is str:
            self._clean_session = str2bool(value, default=self._clean_session, msg='for clean_session')
        else:
            self._clean_session = value
             
        if not self._clean_session:
            print("\n***** Be VERY careful connecting with clean_session=False *****")
        
    @property
    def protocol(self):
        return self._protocol
    
    @protocol.setter
    def protocol(self, value):
        if not value:
            self._protocol = self._default_protocol
        elif value in type(self).mqtt_protocol_versions:
            self._protocol = value
        else:
            try:
                value = int(value)
            except ValueError:
                value = None
                
            if value in type(self).mqtt_protocol_versions:
                self._protocol = value
            else:
                print("Invalid protocol value; should be " + type(self).mqtt_protocol_versions_str) 
        
    def __str__(self):
        return "Client args: client_id={}, clean_session={}, protocol={} ({})".format(
               self.client_id,
               self.clean_session or ("***" + str(self.clean_session).upper() + "***"), 
               self.protocol, 
               type(self).mqtt_protocol_versions[self.protocol])


class ConnectionArgs(object):
    """Container to manage arguments for an MQTT connection."""
    
    def __init__(self, host="", port=None, keepalive=None, bind_address="", username="", password="", will=None):
        """Initialize ConnectionArgs with default or passed-in values."""
        self._default_host = "localhost"
        self.host = host
        self._default_port = 1883
        self.port = port
        self._default_keepalive = 60
        self.keepalive = keepalive
        self.bind_address = bind_address
        self.username = username
        self.password = password
        self.will = will  # a Message

    @property
    def host(self):
        return self._host
    
    @host.setter
    def host(self, value):
        self._host = value or self._default_host
        
    @property
    def port(self):
        return self._port
    
    @port.setter
    def port(self, value):
        if not value:
            self._port = self._default_port
        elif not str(value).isdigit():
            print("Invalid port value; should be a positive integer.") 
        else:
            self._port = int(value)
        
    @property
    def keepalive(self):
        return self._keepalive
    
    @keepalive.setter
    def keepalive(self, value):
        if not value:
            self._keepalive = self._default_keepalive
        elif not str(value).isdigit():
            print("Invalid keepalive value; should be a positive integer.") 
        else:
            self._keepalive = int(value)
        
    def __str__(self):
        return "Connection args: host={}, port={}, keepalive={}, bind_address={}, username={}, password={}, will={}".format(
               self.host, self.port, self.keepalive, self.bind_address,
               self.username, '*'*len(self.password), self.will)


class MessagePublisher(object):
    """Assist with publishing a message via MQTT.
    """
    
    @staticmethod
    def parse_msg_input(line):
        """Parse a space-delimited line of text designating the parameters for a message: topic payload qos retain
        topic (string) - may be quoted, e.g. if contains whitespace
        payload (string) - may be quoted, e.g. if contains whitespace;
                           if starts with "from-url:", then contents of the specified resource will be used, e.g. from-url:file:///tmp/test.txt
        qos (integer, optional: defaults to 0)
        retain (boolean, optional: defaults to False)
        """
        (topic, payload, qos_str, retain_str) = (shlex.split(line) + [None]*4)[:4]
        
        if (payload and payload.lower().startswith("from-url:")):
            try:
                url = payload[9:]        
                print('For payload, reading from: ' + url)
                r = urlreq.urlopen(url)
                url_payload = r.read()
                contenttype = None
                charset = None
                if sys.version_info[0] == 2:
                    contenttype = r.headers.getheaders('content-type')
                    charset = r.headers.getparam('charset')
                else:
                    contenttype = r.headers.get_content_type()
                    charset = r.headers.get_content_charset()
                print('Payload: length={}, content-type={}, charset={}'.format(len(url_payload), contenttype, charset))
                try:
                    payload = url_payload.decode(charset or 'ascii')
                except UnicodeDecodeError as e:
                    print('Problem trying to decode payload:\n' + str(e))
                    print('Converting to bytearray')
                    payload = bytearray(url_payload)
            except URLError as e:
                print('Problem trying to read from the URL:\n' + str(e))
                print('Reverting payload back to: ' + payload)
        
        qos = 0
        if qos_str:
            if qos_str.isdigit() and (0 <= int(qos_str) <= 2):
                qos = int(qos_str)
            else:
                print("Invalid QoS value; should be 0, 1, or 2. Defaulting to 0.")
                 
        retain = str2bool(retain_str, default=False, msg="for retain")
                
        return Message(topic, payload, qos, retain)    

    def __init__(self, mqttclient):
        """Initialize, with an MQTT client instance.
        A message sequence counter is also reset (incremented each time a message is successfully published)."""
        self._mqttclient = mqttclient
        self._msg_seq = 1

    def publish(self, topic, payload, qos=0, retain=False):
        """Publish a message, with the given parameters.
        Substitute in the _msg_seq if the payload contains {seq}."""
        if not topic:
            print("Topic must be specified")
        elif not payload: 
            print("Payload must be specified")
        else:
            if (not isinstance(payload, bytearray)) and ("{seq}" in payload):
                payload = payload.format(seq=self._msg_seq)
            (result, msg_id) = self._mqttclient.publish(topic=topic, payload=payload, qos=qos, retain=retain)
            print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))
            if result == mqtt.MQTT_ERR_SUCCESS:
                self._msg_seq += 1

    def publish_msg(self, msg):
        """Publish the given Message (namedtuple).
        Substitute in the _msg_seq if the payload contains {seq}."""
        self.publish(topic=msg.topic, payload=msg.payload, qos=msg.qos, retain=msg.retain)

    def parse_publish(self, line):
        """Publish a message, after parsing the parameters from the given string, which
        should be formatted as follows:
            topic  payload  [qos  [retain]]
        topic and payload can be quoted (e.g. contain spaces)
        qos (0, 1, or 2) is optional; defaults to 0
        retain (true/false or yes/no) is optional; defaults to false"""
        msg = self.parse_msg_input(line)
        self.publish_msg(msg)
        

class SubscriptionHandler(object):
    """Assist with MQTT subscriptions.
    """
    
    @staticmethod
    def parse_sub_input(line):
        """Parse a space-delimited line of text designating the parameters for a topic subscription: topic qos
        topic (string) - may be quoted, e.g. if contains whitespace
        qos (integer, optional: defaults to 0)
        """
        (topic, qos_str) = (shlex.split(line) + [None]*2)[:2]
        qos = 0
        if qos_str:
            if qos_str.isdigit() and (0 <= int(qos_str) <= 2):
                qos = int(qos_str)
            else:
                print("Invalid QoS value; should be 0, 1, or 2. Defaulting to 0.")
        return Subscription(topic, qos)    

    def __init__(self, mqttclient):
        """Initialize, with an MQTT client instance.
        A set, to contain active subscriptions (Subscription namedtuples), is also created."""
        self._mqttclient = mqttclient
        self._subscriptions = set()

    def _discard_sub(self, topic):
        """Remove a Subscription, identified with the given topic, from the _subscriptions set."""  
        for s in self._subscriptions.copy():
            if s.topic == topic:
                self._subscriptions.remove(s)

    def subscribe(self, sub):
        """Subscribe to a topic, using the Subscription (namedtuple)."""
        if not sub.topic:
            print("Topic must be specified")
        else:
            (result, msg_id) = self._mqttclient.subscribe(topic=sub.topic, qos=(sub.qos or 0))
            print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))
            if result == mqtt.MQTT_ERR_SUCCESS:
                self._discard_sub(sub.topic)   # do not want two Subscriptions with same topic, but different qos
                self._subscriptions.add(sub)

    def parse_subscribe(self, line):
        """Subscribe to a topic, after parsing the parameters from the given string, which
        should be formatted as follows:
            topic [qos]
        topic can be quoted (e.g. contain spaces)
        qos (0, 1, or 2) is optional; defaults to 0"""
        sub = self.parse_sub_input(line)
        self.subscribe(sub)
        
    def unsubscribe(self, topic):
        """Unsubscribe from a topic."""
        if not topic:
            print("Topic must be specified")
        else:
            (result, msg_id) = self._mqttclient.unsubscribe(topic)
            print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))
            if result == mqtt.MQTT_ERR_SUCCESS:
                self._discard_sub(topic)

    def unsubscribe_all(self):
        """Unsubscribe from all active subscriptions."""
        for s in self._subscriptions.copy():
            self.unsubscribe(s.topic)

    def subscription_topics_str(self):
        """Return a comma-separated list of the currently active subscriptions."""
        sorted_subs = sorted(self._subscriptions, key=lambda sub: sub.topic)
        return ', '.join(["(topic={},qos={})".format(s.topic, s.qos) for s in sorted_subs])


class ConsoleContext(object):
    """Container for sharing objects among consoles."""

    _prompt_verbosity_levels = {"N":"None", "L":"Low", "M":"Medium", "H":"High"}
    _prompt_verbosity_levels_str = ", ".join("{}={}".format(k, v) for (k, v) in _prompt_verbosity_levels.items())
    
    @classmethod
    def prompt_verbosity_levels(cls):
        return cls._prompt_verbosity_levels

    @classmethod
    def prompt_verbosity_levels_str(cls):
        return cls._prompt_verbosity_levels_str

    def __init__(self, logging_enabled=True, recording_file=None, playback_file=None, pacing=0,
                 prompt_verbosity=None, client_args=None, mqttclient=None, connection_args=None):
        """Initialize ConsoleContext with default or passed-in values."""
        self.logging_enabled = logging_enabled
        self.recording_file = recording_file
        self.playback_file = playback_file
        self._default_pacing = 0
        self.pacing = pacing
        self._default_prompt_verbosity = "H"
        self.prompt_verbosity = prompt_verbosity
        self.client_args = client_args
        self.mqttclient = mqttclient
        self.connection_args = connection_args
    
    @property
    def prompt_verbosity(self):
        return self._prompt_verbosity
    
    @prompt_verbosity.setter
    def prompt_verbosity(self, value):
        if not value:
            self._prompt_verbosity = self._default_prompt_verbosity
        else:
            value = (str(value)[0].upper())
            if value not in self.prompt_verbosity_levels().keys():
                print("Invalid prompt_verbosity value; should be " + self.prompt_verbosity_levels_str())
            else: 
                self._prompt_verbosity = value
        
    @property
    def pacing(self):
        return self._pacing
    
    @pacing.setter
    def pacing(self, value):
        if not value:
            self._pacing = self._default_pacing
        elif ((not isfloat(value)) or (float(value) < 0)):
            print("Invalid pacing value; should be a non-negative floating point number.") 
        else:
            self._pacing = float(value)
        
    def close_recording_file(self):
        """Close the recording file, if currently open."""
        #print("Check closing recording file")
        if self.recording_file:
            print("Closing recording file: {}".format(self.recording_file.name))
            self.recording_file.close()
            self.recording_file = None
           
    def close_playback_file(self):
        """Close the playback file, if currently open."""
        #print("Check closing playback file")
        if self.playback_file:
            print("Closing playback file: {}".format(self.playback_file.name))
            self.playback_file.close()
            self.playback_file = None


class RootConsole(cmd.Cmd):
    """Parent of other Console (Cmd) objects."""
    
    def __init__(self, context):
        """Initialize, with a context."""
        cmd.Cmd.__init__(self)
        self.context = context

    def build_prompt(self):
        """Build and return the prompt string for this console.
        Override this in child consoles."""
        p = "> "
        if self.context.prompt_verbosity in ("M", "H"):
            p = "Logging: {}, Recording: {}, Pacing: {}\n> ".format(
                    self.context.logging_enabled and 'on' or 'off',
                    self.context.recording_file and self.context.recording_file.name or 'off',
                    self.context.pacing)
            if self.context.prompt_verbosity == "H":
                p = "\n" + p
        return p

    def update_prompt(self):
        """Refresh the prompt."""
        self.prompt = self.build_prompt() 

    def _playback_file_cmd(self):
        """Check playback file, and run next command, if available."""
        if self.context.playback_file:
            playcmd = self.context.playback_file.readline().rstrip("\r\n")
            if playcmd:
                if self.context.pacing:
                    time.sleep(self.context.pacing)
                print("--> Running command: '{}'\t({})".format(playcmd, self.__class__.__name__))
                self.cmdqueue.extend([playcmd])
            else:
                self.context.close_playback_file()

    def preloop(self):
        """(override) Executed once when cmdloop() is called."""
        #print("{} - preloop".format(self.__class__.__name__))
        self._playback_file_cmd()   # necessary when dispatching a "child" console
    
    def precmd(self, line):
        """(override) Called just before the command line 'line' is interpreted."""
        if self.context.recording_file and line:
            if not any(substr in line.lower() for substr in ['playback', 'stop_recording']):
                self.context.recording_file.write(line + '\n')
        return line
    
    def postcmd(self, stop, line):
        """(override) Called after any command dispatch is finished."""
        #print("{} - postcmd".format(self.__class__.__name__))
        if not stop:
            self._playback_file_cmd()
        self.update_prompt()
        return stop
    
    def do_logging(self, arg):
        """Turn MQTT client callback logging on/off, e.g. logging on
        If on/off is not specified, then toggle current setting."""
        if arg:
            self.context.logging_enabled = str2bool(arg, default=self.context.logging_enabled, msg='for logging')
        else:
            self.context.logging_enabled = not self.context.logging_enabled
        #print("Turning MQTT client callback logging " + (self.context.logging_enabled and 'ON' or 'OFF'))
        self.update_prompt()

    def do_prompt_verbosity(self, arg):
        """Set the verbosity level of the console prompt"""
        self.context.prompt_verbosity = arg

    def help_prompt_verbosity(self):
        print("Set the verbosity level, currently {}, of the console prompt ({}) (blank arg sets back to default), e.g. prompt_verbosity {}".format(
              self.context.prompt_verbosity, self.context.prompt_verbosity_levels_str(), next(iter(self.context.prompt_verbosity_levels()))))

    def do_record(self, arg):
        """Start recording commands to the given file, e.g. record session1.cmd
        If the file exists, commands will be appended to it."""
        if arg:
            self.context.recording_file = open(arg, 'a')
            print("Commands will now be recorded to file: {}.".format(arg))
        else:
            print("Must specify a file to record to")

    def do_stop_recording(self, arg):
        """Stop recording commands to the given file"""
        if not self.context.recording_file:
            print("Not currently recording commands")
        else:
            print("Command recording stopped")
            self.context.close_recording_file()
            
    def do_playback(self, arg):
        """Play back commands from the given file, e.g. playback session1.cmd"""
        try:
            self.context.playback_file = open(arg, 'r')
        except:
            print("Unexpected error:")
            traceback.print_exc()

    def do_pacing(self, arg):
        """Set a delay (seconds) between commands, when playing back commands from a file, e.g. pacing 1.5"""
        if arg:
            self.context.pacing = arg
        else:
            print("Current pacing value: {}".format(self.context.pacing))

    def do_exit(self, arg):
        """Exit the current console"""
        return True

    def do_quit(self, arg):
        """Exit the current console"""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """For those systems supporting it, allows using Ctrl-D to exit the current console"""
        return self.do_exit(arg)


class MainConsole(RootConsole):
    """Primary console:
    1) Handles setting MQTT client parameters.
    2) Dispatches the Connection console.
    """

    intro = "\nWelcome to the MQTT client shell.\nType help or ? to list commands.\nPressing <Enter> on an empty line will repeat the last command."
    
    def __init__(self, context):
        """Initialize, with a context."""
        RootConsole.__init__(self, context)
        self.update_prompt()

    def build_prompt(self):
        """Build and return the prompt string for this console."""
        p = ""
        if self.context.prompt_verbosity == "H":
            p = "\n{}".format(self.context.client_args)
        elif self.context.prompt_verbosity in ("M", "L"):
            cs = self.context.client_args.clean_session
            if self.context.prompt_verbosity == "M":
                p = "client_id={}, clean_session={}, ".format(self.context.client_args.client_id, cs or str(cs).upper())
            elif not cs:
                p = "clean_session=" + str(cs).upper()
        return p + RootConsole.build_prompt(self)

    def do_client_id(self, arg):
        """Set the MQTT client ID (blank arg sets back to default), e.g. client_id MyMqttClient1"""
        self.context.client_args.client_id = arg

    def do_clean_session(self, arg):
        """Enable/disable the MQTT client clean_session setting, e.g. clean_session true
        If true/false is not specified, then toggle current setting."""
        self.context.client_args.clean_session = arg

    def do_protocol(self, arg):
        """Set the MQTT protocol version (blank arg sets back to default), e.g. protocol 3"""
        self.context.client_args.protocol = arg

    def help_protocol(self):
        print("Set the MQTT protocol version (" + ClientArgs.mqtt_protocol_versions_str + ")" +
              " (blank arg sets back to default), e.g. protocol " + str(ClientArgs.mqtt_protocol_versions.keys()[0]))

    def do_connection(self, arg):
        """Go to the Connection console, after establishing an MQTT client (using the current MQTT client args)"""
        ca = self.context.client_args
        self.context.mqttclient = mqtt.Client(client_id=ca.client_id, clean_session=ca.clean_session, userdata=self.context, protocol=ca.protocol)
        # Set the client callbacks:
        self.context.mqttclient.on_connect = on_connect
        self.context.mqttclient.on_disconnect = on_disconnect
        self.context.mqttclient.on_message = on_message
        self.context.mqttclient.on_publish = on_publish
        self.context.mqttclient.on_subscribe = on_subscribe
        self.context.mqttclient.on_unsubscribe = on_unsubscribe
        self.context.mqttclient.on_log = on_log
        # Initiate the "Connection" console.
        ConnectionConsole(self.context).cmdloop()
        # Clean up, after returning from "Connection" console.
        self.context.mqttclient = None
        

class ConnectionConsole(RootConsole):
    """Console for establishing an MQTT connection:
    1) Handles setting connection parameters.
    2) Dispatches the Messaging console.
    """

    def __init__(self, context):
        """Initialize, with a context."""
        RootConsole.__init__(self, context)
        self.update_prompt()

    def build_prompt(self):
        """Build and return the prompt string for this console."""
        p = ""
        if self.context.prompt_verbosity == "H":
            p = ("\n{}".format(self.context.connection_args) + 
                 "\n{}".format(self.context.client_args))
        elif self.context.prompt_verbosity in ("M", "L"):
            cs = self.context.client_args.clean_session
            if self.context.prompt_verbosity == "M":
                p = "{}, client_id={}, clean_session={}, ".format(
                    self.context.connection_args.host + ":" + str(self.context.connection_args.port),
                    self.context.client_args.client_id,
                    cs or str(cs).upper())
            elif not cs:
                p = "clean_session=" + str(cs).upper()
        return p + RootConsole.build_prompt(self)

    def do_host(self, arg):
        """Set the hostname or IP address of the MQTT server (blank arg sets back to default), e.g. host mymqttserver"""
        self.context.connection_args.host = arg

    def do_port(self, arg):
        """Set the network port to connect to, on the MQTT server (blank arg sets back to default), e.g. port 1883"""
        self.context.connection_args.port = arg

    def do_keepalive(self, arg):
        """Set the keep-alive time, in seconds (blank arg sets back to default), e.g. keepalive 60"""
        self.context.connection_args.keepalive = arg

    def do_bind_address(self, arg):
        """Set the IP address of a local network interface to bind the client to, assuming multiple interfaces exist (defaults to blank)"""
        self.context.connection_args.bind_address = arg

    def do_username(self, arg):
        """Set the username for MQTT server authentication"""
        self.context.connection_args.username = arg

    def do_password(self, arg):
        """Prompt for the password for MQTT server authentication (if username is blank, then this is not used)"""
        self.context.connection_args.password = getpass.getpass()

    def do_will(self, arg):
        """Set a Will (a.k.a. Last Will and Testament), e.g. will topic [payload [qos [retain]]]
        topic can be quoted (e.g. contains spaces)
        payload can be quoted (e.g. contains spaces);
        qos (0, 1, or 2) is optional; defaults to 0
        retain (true/false or yes/no) is optional; defaults to false"""
        self.context.connection_args.will = MessagePublisher.parse_msg_input(arg)

    def do_connect(self, arg):
        """Connect to the MQTT server, using the current connection parameters.
        If connection successful, then go to the Messaging console."""
        connected = None
        ca = self.context.connection_args
        
        if ca.username:
            self.context.mqttclient.username_pw_set(ca.username, ca.password)
        else:
            self.context.mqttclient.username_pw_set("", None)

        if ca.will:
            self.context.mqttclient.will_set(topic=ca.will.topic, payload=ca.will.payload, qos=ca.will.qos, retain=ca.will.retain)

        try:
            rc = self.context.mqttclient.connect(host=ca.host, port=ca.port, keepalive=ca.keepalive, bind_address=ca.bind_address)
            connected = (rc == mqtt.MQTT_ERR_SUCCESS)
        except socket.error as e:
            print(e)
        else:
            if not connected:
                print("Unable to connect")
            else:
                self.context.mqttclient.loop_start()
                # Initiate the "Messaging" console.
                MessagingConsole(self.context).cmdloop()
                # Clean up (disconnect), after returning from "Messaging" console.
                self.context.mqttclient.disconnect()
                connected = False
                self.context.mqttclient.loop_stop()


class MessagingConsole(RootConsole):
    """Console for performing pub/sub messaging, via an active MQTT connection.
    """
    
    def __init__(self, context):
        """Initialize, with a context."""
        RootConsole.__init__(self, context)
        self._msg_publisher = MessagePublisher(self.context.mqttclient)
        self._sub_handler = SubscriptionHandler(self.context.mqttclient)
        self.update_prompt()

    def build_prompt(self):
        """Build and return the prompt string for this console."""
        p = ""
        if self.context.prompt_verbosity == "H":
            p = ("\n***CONNECTED***" + 
                 "\nSubscriptions: {}".format(self._sub_handler.subscription_topics_str()) + 
                 "\n{}".format(self.context.connection_args) + 
                 "\n{}".format(self.context.client_args))
        elif self.context.prompt_verbosity in ("M", "L"):
            cs = self.context.client_args.clean_session
            if self.context.prompt_verbosity == "M":
                p = "CONNECTED, {}, client_id={}, clean_session={}, ".format(
                    self.context.connection_args.host + ":" + str(self.context.connection_args.port),
                    self.context.client_args.client_id,
                    cs or str(cs).upper())
            else:
                p = "CONNECTED" + ((not cs) and (",clean_session=" + str(cs).upper()) or "")
        return p + RootConsole.build_prompt(self)

    def do_disconnect(self, arg):
        """Disconnect from the MQTT server.
        Note that exiting this console session, via exit, quit, etc., will also disconnect."""
        return True

    def do_publish(self, arg):
        """Publish a message, e.g. publish topic payload [qos [retain]]
        topic can be quoted (e.g. contains spaces)
        payload can be quoted (e.g. contains spaces);
            if contains "{seq}", then published message sequence# will be substituted;
            if starts with "from-url:", then contents of the specified resource will be used, e.g. from-url:file:///home/fred/test.txt
        qos (0, 1, or 2) is optional; defaults to 0
        retain (true/false or yes/no) is optional; defaults to false"""
        try:
            self._msg_publisher.parse_publish(arg)
        except:
            print("Unexpected error:")
            traceback.print_exc()

    def do_subscribe(self, arg):
        """Subscribe to a topic, e.g. subscribe topic [qos]
        topic can be quoted (e.g. contains spaces)
        qos (0, 1, or 2) is optional; defaults to 0"""
        try:
            self._sub_handler.parse_subscribe(arg)
        except:
            print("Unexpected error:")
            traceback.print_exc()

    def do_unsubscribe(self, arg):
        """Unsubscribe from a topic, e.g. unsubscribe topic
        topic can be quoted (e.g. contains spaces)"""
        self._sub_handler.unsubscribe(arg)

    def do_unsubscribe_all(self, arg):
        """Unsubscribe from all active topic subscriptions, e.g. unsubscribe_all"""
        self._sub_handler.unsubscribe_all()

    def do_list_subscriptions(self, arg):
        """List the currently active topic subscriptions"""
        print("Active topic subscriptions: {}".format(self._sub_handler.subscription_topics_str()))


if __name__ == '__main__':
    ctx = ConsoleContext(client_args=ClientArgs(), connection_args=ConnectionArgs())
    console = MainConsole(ctx)
    if len(sys.argv) > 1:
        # optional command-line argument is treated as a playback file
        console.cmdqueue.extend(["playback " + sys.argv[1]])
    console.cmdloop()
    # cleanup:
    ctx.close_recording_file()
    ctx.close_playback_file()
    if ctx.mqttclient:
        ctx.mqttclient.disconnect()
        ctx.mqttclient.loop_stop()
