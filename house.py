import toml
import xml.etree.ElementTree as ET
from fsm import StateMachine

filename = "house.xml"

xmltree = ET.parse(filename)
xmlcfg = xmltree.getroot()

def onAction(xml_action):
    pass

# The constants are a TOML config inside the XML-file
const = toml.loads(xmlcfg.find('constants').text)
xml_sm = xmlcfg.find('statemachine')
sm = StateMachine.from_xml_element(xml_sm)
sm.start()
