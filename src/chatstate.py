## State machine support for chat
"""Simple framework for asynchronous, event-driven, stateful chatbot
interaction.  Created by Rich DeVaul, @rdevaul on Github, X


"""

import asyncio

class Reply:
    """Class representing a reply object, media type support is subject to chat client"""
    replytypes = ['text','audio','image','video']
    def __init__(self,
                 content,
                 reply_type = "text"):
        self.content = content
        if reply_type not in self.replytypes:
            raise Exception(f'bad reply_type in Reply init: {reply_type}')
        self.reply_type = reply_typ

    def asdict(self):
        """Produce Python3 dictionary representation of the Reply instance"""
        return {'tag': 'reply',
                'content': self.content,
                'reply_type': self.reply_type }
        
def dict2reply(dct):
    """ convert from a Python3 dict to a Reply object instance"""
    if 'tag' not in dct or dct['tag'] != 'reply':
        raise Exception('bad dictionary passed to dict2reply')
    
    return Reply(dct["content"],
                 dct["reply_type"])

class User:
    """Class representing a chat user"""
    def __init__(self,
                 user_id,       # should be globally unique user identifier (may be same as below)
                 client_id,     # client-specific identifier for user on a chat client
                 name,          # what do we call the user
                 state = {}):   # additional state for the user
        self.user_id = user_id
        self.client_id = client_id
        self.name = name
        self.state = state
        
    def asdict(self):
        """Produce Python3 dictionary representation of a User instance"""
        return {'tag': 'user',
                'user_id': self.user_id,
                'client_id': self.client_id,
                'name': self.name,
                'state': self.state }

def dict2user(dct):
    """ convert from a Python3 dict to a User object instance"""
    if 'tag' not in dct or dct['tag'] != 'user':
        raise Exception('bad dictionary passed to dict2user')
    
    return User(dct["user_id"],
                dct["client_id"],
                dct["name"],
                dct["state"])
    
class ChatState:
    """Class instance represents chat state machine"""
    
    async def default_send(client_id,message):
        """placeholder user message function, which is just a print
        statement. You will almost always want to use something else.

        """ 
        print(f"{x}: {y.content}")
    
    def __init__(self,
                 state_machine,
                 graph,
                 functions,
                 send_message = default_send,
                 timeout = 3600 * 8 ):

        # a list of strings marking the state
        self.stateMachine = state_machine
        # a mapping of each state to a list of successor states
        self.graph = graph
        # a list of functions to go with each state. Each function
        # must return a reply and a string that represents the next state.
        self.funct = functions
        # how do you send a message to the client
        self.sendMessage = send_message
        # how long do we wait to drop chat state
        self.timeout = timeout

        # list of users
        self.users = {}
        # mapping of client ID to state
        self.states = {}

    def verifyGraph(self):
        """ check graph against state machine"""
        for s in self.stateMachine:
            if s not in self.graph.keys():
                print(f"state {s} not matched by a graph node")
                return False
        for key in self.graph.keys():
            if not key in self.stateMachine:
                print(f"key {key} not found in state machine {self.stateMachine}")
                return False
            transitions = self.graph[key]
            for t in transitions:
                if not t in self.stateMachine:
                    print(f"transition {t} not found in state machine {self.stateMachine}")
                    return False
        return True

    def verifyFunctions(self):
        """make sure that all stateMachine states have associated functions"""
        for s in self.stateMachine:
            if s not in self.funct.keys():
                print(f"state {s} not matched by a function")
                return False
        return True

    def verifyState(self):
        """Verify that the ChatState instance is conforming"""
        return self.verifyGraph() and self.verifyFunctions()

    def checkUser(self,client_id):
        """Check to see if a client_id user exists in active users"""
        return client_id in self.users and client_id in self.states

    def addUser(self,newuser: User):
        """Add a new user"""
        client_id = newuser.client_id
        self.users[client_id] = newuser
        self.states[client_id] = undefined

    def updateUserState(self,client_id,nstate):
        """ use a revised state to update the existing user state"""
        self.states[client_id] = {**self.states[client_id], **nstate}

    async def nextInput(self,client_id,in_reply):
        state = None
        nextstate = None
        fn = None
        if self.checkState(client_id):
            state = self.states[client_id]
            nextstate = state['nextstate']
            fn = self.funct[nextstate]
        else:
            state = {'history': [ ]}
            self.states[client_id] = state
            nextstate =self.stateMachine[0]
            state["nextstate"] = nextstate
            fn = self.funct[nextstate]

        # record the state before transition
        state['oldstate'] = state['nextstate']
        # record the reply, convert to Reply object
        state['reply'] = Reply(in_reply)
        # perform state update, if needed
        self.states[client_id] = { **self.states[client_id], **state}
        # invoke state transition function, get reply for user and return
        # value which is a string indicating next state.
        reply, rval = fn(self,client_id,state)
        # debugging
        print(f'graph: {self.graph[nextstate]}')
        # check to make sure next state is legal
        if rval not in self.graph[nextstate]:
            raise Exception(f'Bad state transition from {nextstate} to {rval}')
        # update history
        if not 'history' in self.states[client_id].keys():
            self.states[client_id]['history'] = [ in_reply, reply.content ]
        else:
            self.states[client_id]['history'] += [ in_reply, reply.content ]
        # update new state with return value from state transition funct.
        self.states[client_id]['nextstate'] = rval
        # send the message to the user
        await self.sendMessage(client_id,reply)


## Utility functions for creating command-processing wrapper functions

def process_commands(input_string,
                     command_regex_list, command_functions,
                     cs=None,client_id=None,state={}):
    """
    Process user input strings and call corresponding functions based on matched commands.

    Parameters:
    - input_string: The user input string to process.
    - command_regex_list: A list of regular expressions corresponding to command strings.
    - command_functions: A list of functions corresponding to the commands.

    Returns:
    - return value of matching function, or False if no match
    """
    for regex, func in zip(command_regex_list, command_functions):
        match = re.match(regex, input_string)
        if match:
            remaining_input = input_string[match.end():].strip()
            return func(remaining_input,cs,client_id,state)
    return False

def makeWrapper(regex_list,function_list,state_function):
    """take a list of command-matching regular expressions, a list of
    corresponding command functions, and state-transition function to
    wrap, and return a new function that is the original state
    transition function but wrapped with the process_command function.

    If there is a match to any command regex, the corresponding
    command function will be invoked and become the return value,
    superceeding the state transition function.


    If no command is matched, the state transition function is invoked.

    """

    def wrapper(cs,client_id,state):
        message = state["reply"].content
        rval = process_command(message,
                               regex_list, function_list,
                               cs,client_id,state)
        if not rval:
            return state_function(cs,client_id,state)
        return rval

    return wrapper
