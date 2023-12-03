import asyncio
## State machine support for chat

class Reply:
    """Class representing a reply object, media type support is subject to chat client"""
    def __init__(self,
                 content,
                 reply_type = "text"):
        self.content = content
        self.reply_type = reply_type

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
        

class ChatState:
    """Class instance represents chat state machine"""
    async def default_send(client_id,message):
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
        return self.verifyGraph() and self.verifyFunctions()

    def checkState(self,client_id):
        return client_id in self.users and client_id in self.states

    def updateState(self,client_id,nstate):
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
        state['reply'] = Reply(in_reply)
        self.states[client_id] = { **self.states[client_id], **state}
        reply, rval = fn(self,client_id,state)
        print(f'graph: {self.graph[nextstate]}')
        if rval not in self.graph[nextstate]:
            raise Exception(f'Bad state transition from {nextstate} to {rval}')
        if not 'history' in self.states[client_id].keys():
            self.states[client_id]['history'] = [ in_reply, reply.content ]
        else:
            self.states[client_id]['history'] += [ in_reply, reply.content ]
        # update new state
        self.states[client_id]['nextstate'] = rval
        # self.states[client_id] = { **self.states[client_id], **state}
        await self.sendMessage(client_id,reply)
