from presence import sec_to_hour
import xml.etree.ElementTree as ET
import threading
import time

STATE_TAGS = ["machine","state","sm","statemachine","submachine"]
TRANSITION_TAGS = [ "tr", "transition" ]
ENTRY_TAGS = [ "entry", "onentry", "on_entry", "entry_action"]
EXIT_TAGS = [ "exit", "onexit", "on_exit", "exit_action"]
INIT_TAGS = [ "init" ]

def levelprint(level, str):
    print("{}{}".format('  '*level,str))

class Transition:
    def __init__(self, target_state, name, action = None):
        self.target_state = target_state
        self.name = name
        self.action = action

   def execute_action(self):
        if self.action:
            self.action()



class StateMachine:
    def __init__(self, name, on_action = None, parent = None):
        self.name = name
        self.transitions = []
        self.states = []
        if callable(on_action):
            self.on_action = on_action
            print("Added action function: {}".format(self.on_action))
        else:
            raise Exception("Object is not a function: {}".format(on_action))
        self.on_action = on_action
        self.parent = parent
        self.current_state = None

    def add_transition(self, transition):
        self.transitions.append(transition)

    def has_transition(self,transition):
        for tr in self.transtions:
            if tr is transition:
                return True
        return False

    def add_entry_actions(self, xml_action_elmt):
        self.xml_entry_action_elmt = xml_action_elmt

    def add_exit_action(self, xml_action_elmt):
        self.xml_exit_action_elmt = xml_action_elmt

    def execute_entry_action(self):
        print("Enter state {}".format(self.name))
        if self.on_action:
            self.on_action(self.xml_entry_action_elmt)

        # Check if there is a self trigger timeout
        if self.self_trigger_timeout_s:
            # Start a timer and exectte
            timer.start(self.self_trigger_timeout_s, self.transitions[transition_name].function)

    def execute_exit_action(self):
        print("Exit state {}".format(self.name))
        if self.on_action:
            print(format(self.entry_action))
            self.on_action(self.xml_exit_action_elmt)

    def is_top_statemachine(self):
        return self.parent == None

    def is_statemachine(self):
        return len(self.states)>0

    def is_state(self):
        return not self.is_statemachine()

    def set_self_trigger_transition_timeout_s(self,sec):
        self.self_trigger_timeout_s = sec

    def add_state(self, state):
        # print("adding state: {} to {}".format(state.name,self.name))
        self.states.append(state)
        state.parent_sm = self

    def get_substate_by_name(self, substate_name):
        for state in self.states:
            if state.name.lower() == substate_name.lower():
                return state
        return None

    def add_init_action(self, init_action):
        self.init_action = init_action

    def set_init_state_name(self, init_state_name):
        self.init_state_name = init_state_name

    def trigger_transition(self, transition):
        if self.running:
            self.mutex.acquire()
            try:
                if self.current_state.has_transition(transition):
                    self.current_state.execute_exit_action()
                    transition.execute_action()
                    self.current_state = transition.target_state
                    self.current_state.execute_entry_action()
                    self._run()
            finally:
                self.mutex.release()
        else:
            raise Exception("State machine is not started")

    def _run(self):
        self.mutex = threading.Lock()
        while self.running:
            time.sleep(1)


    def start(self):
        # Start a statemachine in its 
        # 1) defined init state
        # 2) execute init action which is a callback returning the init state

        print("Starting statemachine "+self.name)
        if not self.current_state:
            if self.init_state_name:
                print("Setting init state: "+self.init_state_name)
                self.current_state = self.get_substate_by_name(self.init_state_name)
            elif self.init_action:
                self.current_state = self.init_action()
            else:
                raise Exception("No init action or init state defined for statemachine "+self.name)

        if self.current_state.is_statemachine():
            self.current_state.start()
        else:
            self.running = True
            self.current_state.execute_entry_action()
            self.smthread = threading.Thread(target=self._run)

    def stop(self):
        self.running = False
        self.smthread.join()
        
    @staticmethod
    def _parse_transition(xml_element_transition, from_state):
        try: 
            target_state_name = xml_element_transition.attrib['to']
        except KeyError:
            raise Exception("Transition without a \"to\" attribute defining a target state")

        try:
            transition_name = xml_element_transition.attrib['name']
        except KeyError:
            transition_name = from_state.name + "_to_" + target_state_name

        new_transition = Transition(target_state_name, transition_name)

        for xml_element in xml_element_transition:
            if xml_element.tag in [ "action" ]:
                raise NotImplemented()
            if xml_element.tag in [ "trigger" ]:
                for xml_element_trigger in xml_element:
                    if xml_element_trigger.tag in [ "timeout" ]:
                        try:
                            sec = xml_element_trigger.attrib['sec']
                            new_transition.add_self_trigger_timeout_s(int(sec))
                        except:
                            pass



        return new_transition

    @staticmethod
    def _parse_init_state(xml_element_init):
        try:
            init_state_name = xml_element_init.attrib['state']
        except KeyError:
            raise Exception("Init state without state defined: {} "+format(xml_element_init))
        return init_state_name

    @staticmethod
    def _parse_state(xml_element_state, on_action, parent_state = None, level=0):
        # The sm MUST have a name otherwise we cannot refer to the state
        try:
            smname = xml_element_state.attrib['name']
        except KeyError:
            raise Exception("Statemachine without name".format())
        
        # Create the state
        new_state = StateMachine(name=smname, on_action=on_action, parent=parent_state)
        if parent_state:
            parent_state.add_state(new_state)
        if new_state.is_top_statemachine():
            levelprint(level,"Building statemachine "+smname)            
        else:
            levelprint(level,"Building state "+smname)

        for xml_element in xml_element_state:
            tag = xml_element.tag.lower()
            if tag in STATE_TAGS:
                StateMachine._parse_state(xml_element, on_action, new_state, level+1)

            elif tag in TRANSITION_TAGS:
                transition = StateMachine._parse_transition(xml_element, new_state)
                levelprint(level+1,"added transition: "+transition.name)
                new_state.add_transition(transition)
            elif tag in ENTRY_TAGS:
                new_state.add_entry_actions(xml_element)
            elif tag in EXIT_TAGS:
                new_state.add_exit_action(xml_element)
            elif tag in INIT_TAGS:
                init_state_name = StateMachine._parse_init_state(xml_element)
                levelprint(level, "with init state: "+init_state_name)

                new_state.set_init_state_name(init_state_name)
            else:
                raise Exception("Unknown tag: {}"+xml_element.tag)
 
        return new_state

    @staticmethod
    def from_xml_element(xml_sm, on_action):
        return StateMachine._parse_state(xml_sm, on_action)


