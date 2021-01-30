#from presence import Domoticz
import xml.etree.ElementTree as ET
from fsm import StateMachine
import time

filename = "house.xml"


def onAction(xml_actions):
    print(format(xml_actions))
    for xml_action in xml_actions:
        tag = xml_action.tag.lower()
        if tag == "lamp":
            alias = xml_action.attrib['alias']
            state = xml_action.attrib['state']
            print("Set lamp {} to {}".format(alias,state))
            #dcz.lamp(idx).on
            
    # Find all lamps


class Event:
    def __init__(self):
        pass

class TimerEvent(Event):
    # This class captures events from Domoticz
    # most likely a timer expiry
    pass

class DomoticzEvent(Event):
    # This class captures events from Domoticz
    # most likely a button press, but also timers set in Domoticz
    pass


xmltree = ET.parse(filename)
xmlcfg = xmltree.getroot()
# The constants are a TOML config inside the XML-file
# const = toml.loads(xmlcfg.find('constants').text)
xml_const = xmlcfg.find('constants')
xml_dcz = xmlcfg.find('domoticz')
try:
    xml_triggers = xml_dcz.find('triggers')
    for trigger in xml_triggers.get('event'):
        name = trigger.attrib['name']
        print(name)
except:
    print("No triggers defined")    

print(xml_const.text)
print(xml_dcz.text)

xml_sm = xmlcfg.find('statemachine')
sm = StateMachine.from_xml_element(xml_sm, onAction)
#sm.add_entry_action(onAction)
sm.start()

while True:
    # Wait for events 
    time.sleep(1)
