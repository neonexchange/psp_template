Overview
========

The ``nex-psp`` project is a template for a Payment Service Provider on the NEX Platform.  This is an example implementation of sending/receiving both NEO/Gas and fiat
to and from users.

This implementation uses the Dwolla payment service for interfacting with bank ACH tranfers in the United States. It should be easily replaceable with another fiat transfer API

What it currently does
^^^^^^^^^^^^^^^^^^^^^^

-  Accept ACH fiat transfers and sends them via the Dwolla payment network
-  Send and receive NEO/Gas based on those fiat transfers


