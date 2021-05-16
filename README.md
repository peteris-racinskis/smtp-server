# smtp-server - a bare-bones implementation of SMTP in Python

This project was developed for a university assignment; it's not secure, scalable or useful in any other sense.

## How it works

The main program loop hosts a server on a selected port. Incoming connections get dispatched to server threads which accept SMTP requests and stage received e-mails into a shared, thread-safe FIFO queue. These then get periodically consumed by client threads that connect to the next server in the chain. Everything is built and tested for use on a local machine, and wouldn't actually work in most real networks (since outgoing connections targeting port 25 tend to get filtered by the ISP). No real domain resolution is implemented, the server does a simple lookup of whether the recipient domain is in a hardcoded list.

## Usage

1. Clone the repo
2. Execute main.py (default port: 42069; default domains - "localhost.com")