#!/usr/bin/env python3

import logging
from getpass import getpass
from argparse import ArgumentParser
from random import choice

import slixmpp


class Auditor(slixmpp.ClientXMPP):
    def __init__(self, jid, password, msg):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.msg = msg

    async def start(self, event):
        self.send_presence()
        await self.get_roster()

        self.botty()

        self.disconnect()

    def botty(self):
        self.send_message(mto="botty@foxhole", mbody=self.msg, mtype="chat")


def alice(msg):
    xmpp = Auditor("alice_anderson@foxhole", "alice_anderson", msg)
    xmpp.connect()
    xmpp.process(forever=False)


def bob(msg):
    xmpp = Auditor("bob_abbott@foxhole", "bob_abbott", msg)
    xmpp.connect()
    xmpp.process(forever=False)


def clare(msg):
    xmpp = Auditor("clare_aldridge@foxhole", "clare_aldridge", msg)
    xmpp.connect()
    xmpp.process(forever=False)


def derek(msg):
    xmpp = Auditor("derek_archer@foxhole", "derek_archer", msg)
    xmpp.connect()
    xmpp.process(forever=False)


def admin(msg):
    xmpp = Auditor("audit_admin_a@foxhole", "audit_admin_a", msg)
    xmpp.connect()
    xmpp.process(forever=False)


def rc():  # Random Choice : rc
    return choice(["y", "n"])
