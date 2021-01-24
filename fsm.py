import xml.etree.ElementTree as ET
STATE_TAGS = ["machine","state","sm","statemachine","submachine"]
TRANSITION_TAGS = [ "tr", "transition" ]
ENTRY_TAGS = [ "entry", "onentry", "on_entry", "entry_action"]
EXIT_TAGS = [ "exit", "onexit", "on_exit", "exit_action"]
INIT_TAGS = [ "init" ]

class Transition:
    def __init__(self, target_state, name, action = None):
        self.target_state = target_state
        self.name = name
        self.action = action

    def execute_action(self):
        if self.action:
            self.action()

class State:
    def __init__(self, name = None, transitions = []):
        self.name = name
        self.transtions = transitions
        self.entry_action = None
        self.exit_action = None
        self.parent_sm = None

    def add_transition(self, transition):
        self.transitions.append(transition)

    def has_transition(self,transition):
        for tr in self.transtions:
            if tr is transition:
                return True
        return False
        

    def add_entry_action(self, action):
        self.entry_action = action

    def add_exit_action(self, action):
        self.exit_action = action

    def execute_entry_action(self):
        if self.entry_action:
            self.entry_action()

    def execute_exit_action(self):
        if self.exit_action:
            self.exit_action()

    def is_statemachine(self):
        return False


class StateMachine(State):
    def __init__(self, name):
        self.name = name
        self.states = []
        self.current_state = None
        self.init_action = None
        self.parent_sm = None

    def is_statemachine(self):
        return True

    def is_top_statemachine(self):
        return (self.parent_sm == None)

    def add_state(self, state):
        self.states.append(state)
        state.parent_sm = self

    def add_initaction(self, init_action):
        self.init_action = init_action

    def  set_init_state(self, init_state):
        self.current_state = init_state

    def trigger_transition(self, transition):
        if self.current_state.has_transition(transition):
            self.current_state.execute_exit_action()
            transition.execute_action()
            self.current_state = transition.target_state
            self.current_state.execute_entry_action()

    def start(self):
        # Start a statemachine in its 
        # 1) defined init state
        # 2) execute init action which is a callback returning the init state

        if not self.current_state:
            if not self.init_action:
                raise Exception("No init action or init state defined for statemachine "+self.name)
            else:
                self.current_state = self.init_action()
                if not isinstance(self.current_state, State):
                    raise Exception("Init action does not return a valid state")
        if self.current_state.is_statemachine():
            self.current_state.start()
        else:
            self.current_state.execute_entry_action()

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

        for xml_element in xml_element_transition:
            if xml_element.tag in [ "action" ]:
                raise NotImplemented()

        new_transition = Transition(target_state_name, transition_name)
        return new_transition

    @staticmethod
    def _parse_init_state(xml_element_init):
        try:
            init_state = xml_element_init.attrib['state']
        except KeyError:
            raise Exception("Init state without state defined")
        return init_state

    @staticmethod
    def _parse_state(xml_element_state,parent_state = None):
        # The sm MUST have a name otherwise we cannot refer to the state
        try:
            smname = xml_element_state.attrib['name']
        except KeyError:
            raise Exception("Statemachine without name".format())

        # Create the state
        new_state = State(smname)
        if parent_state:
            parent_state.add_state(new_state)

        for xml_element in xml_element_state:
            tag = xml_element.tag.lower()
            if tag in STATE_TAGS:
               # if this state contain substate, parse again
                for subtag in STATE_TAGS:
                    if xml_element.find(subtag):
                        StateMachine._parse_state(xml_element, parent_state)
                        break
            elif tag in TRANSITION_TAGS:
                if not parent_state:
                    raise Exception("Top state cannot have transitions")
                transition = StateMachine._parse_transition(xml_element, parent_state)
                new_state.add_transition(transition)
            elif tag in ENTRY_TAGS:
                new_state.add_entry_action(xml_element)
            elif tag in EXIT_TAGS:
                new_state.add_exit_action(xml_element)
            elif tag in INIT_TAGS:
                init_state = StateMachine._parse_init_state(xml_element)
                new_state.set_init_state(init_state)
            else:
                raise Exception("Unknown tag: {}"+xml_element.tag)
 
        return new_state

    @staticmethod
    def from_xml_element(xml_sm):
        return StateMachine._parse_state(xml_sm)


