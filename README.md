# async-chat
Python3 state machine code intended to support asynchronous, event-driven chatbot (and similar) apps

## overview

There are a number of state-machine driven chatbot frameworks, such as
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot),
that utilize a state machine to allow for stateful interaction by
clients with the chatbot code, but none that I've found that are
agnostic to the client.

So if, hypothetically, you wanted to create a chatbot that was
interacting in a stateful way via Telegram and WhatsApp and Discord,
you'd be out of luck.

This code lets you define the state machine and transitions, then
associate handlers with state transitions. This means you can build
your chatbot back-end without dependencies on any particular
client-specific library or front-end.

To use this for real, you will need a ASGI server framework, such as
[uvicorn](https://www.uvicorn.org/) or
[hypercorn](https://github.com/pgjones/hypercorn), and create webhooks
or similar to do the interaction with the chat clients.

## license

This code is distributed under the terms of the MIT license.
