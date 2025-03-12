# A very simple demo chatbot that talks by sockets to a local TCP
# client.

from chatstate import Reply, User, ChatState, makeWrapper

import asyncio

import re
import colorama
from colorama import Fore, Back, Style

print("=================================================")
print("simple demo chat system that authneticates")
print("a user and echos their text till a /quit command ")
print("==> Created by Rich @rdevaul")
print("=================================================")
print()

      
## Define the state machine for chat

stateMachine = [ 'undefined','auth', 'echo' ]

## Define the legal transitions between states

graph = {
    'undefined': [ 'auth' ],
    'auth': [ 'auth', 'echo', 'undefined' ],
    'echo': [ 'echo', 'undefined' ]
}

## State Transition Functions

# NOTE: state transition functions get passed client_id. If you are
# working with a seperate global user identifier, you need to perform
# a mapping operation to get that. For now, we assume they are
# synonymous

def undefined(cs,client_id,state):
    """function for 'undefined' state"""
    if not cs.checkUser(client_id):
        newuser = User("global:"+client_id,client_id,"anon-kun", {})
        cs.addUser(newuser)
    return Reply("Plese provide your authoriation code"), 'auth'

def isAuth(code):
    """ code authorization utilty function"""
    if code.strip() == '12345': # check for secret code
        return True
    return False

def auth(cs,client_id,state):
    """ function for 'auth' state - will verify code, or ask again"""
    # extract the user's most recent reply
    message = state["reply"].content
    
    if not cs.checkUser(client_id):
        raise Error("user doesn't exist - should never happen")

    # count authorization attempts
    counter = 0
    # get an auth attempt counter, if present.
    if 'authcounter' in state:
        counter = state['authcounter']
    # increment
    counter += 1
    # store the results in the user's state dictionary 
    cs.updateUserState(client_id, {'authcounter': counter})
    
    reply = None
    rval = None
    if counter > 4:             # too many tries
        reply = Reply('Maximum sign-in attempts exceeded')
        rval = 'undefined'
    elif isAuth(message):
        reply = Reply("Thanks for signing in. What can I do for you?")
        rval = 'echo'
    else:
        reply = Reply(f"I'm sorry, I didn't recongize that code. You have {5-counter} attempts left. Could you try again?")
        rval = 'auth'
    return reply, rval
      
def echo(cs,client_id,state):
    """function for 'echo' state - will simply echo back the user's
     message endlessly. NOTE: requires a command wrapper to transition
     to another state.
    
    """
    # extract the user's most recent reply
    message = state["reply"].content
    reply = Reply(f'echo: {message} (/quit to exit)')
    rval = 'echo'
    if not cs.checkUser(client_id):
        raise Error("user doesn't exist - should never happen")
    return reply, rval

## slash commands for bot - define "quit" and "help". Note that slash
## commands can result in state transition or simply result in side
## effects without a state transition.

def quitfunc(message,cs,client_id,state):
    reply = Reply('Signing you out.  Goodby!')
    rval = 'undefined'
    return reply, rval

quit_cmd = r'^\s*/quit'         # match /quit

def helpfunc(message,cs,client_id,state):
    reply=Reply( """
This is a simple demo bot.
The only commands available after you sign in are:
    /help — produces this message, and
    /quit — signs you out.
    """)
    # don't update the state transition
    rval = state['oldstate']
    return reply, rval

help_cmd = r'^\s*/help'         # match /help

# Wrap the echo state transition function with the slash command
# wrapper that implements /help and /quit
echo = makeWrapper([quit_cmd, help_cmd],
                   [quitfunc, helpfunc], echo)

# create the mapping between states and functions

functions = { 'undefined': undefined,
              'auth': auth,
              'echo': echo }

# create the ChatState instance

chatstate = ChatState(stateMachine,
                      graph,
                      functions)

## Verify the state machine
if not chatstate.verifyState():
    raise Exception('Incomplete initialization of chatstate')

async def main():
    client_id="local:testuser"
    while True:
        user_input = input("Enter a prompt: ")
        print()
        await chatstate.nextInput(client_id,user_input)



if __name__ == '__main__':
    asyncio.run(main())
