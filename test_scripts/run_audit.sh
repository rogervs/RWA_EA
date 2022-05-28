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


if __name__ == "__main__":

    # eth_addr = "0x0B36748D853621251D5249c18fC18B5ab47437a1"
    alice_eth_addr = "0x4f812c24109BDAf3b4630a0aE8Bea34BEAb7e581"
    bob_eth_addr = "0x6b5CBFBF2173b4a2E4BA43aE3CefD0dE84C859b1"
    clare_eth_addr = "0x72eda8030E0784d58A101DBBaEa918D18927E06d"
    derek_eth_addr = "0xd34803F01A38fC5f2B709Bca3b9681fbf5350A29"

    setup = [
        (admin, "add Room 1"),
        (admin, "add Room 2"),
        (admin, "add Room 3"),
        (admin, "add Room 4"),
        (admin, "add Room 5"),
        (admin, "open"),
        (alice, "Demo Project A"),
        (alice, alice_eth_addr),
        (bob, "Demo Project A"),
        (bob, bob_eth_addr),
        (clare, "Demo Project A"),
        (clare, clare_eth_addr),
        (derek, "Demo Project A"),
        (derek, derek_eth_addr),
        (admin, "close"),
        (admin, "start"),
        # (admin, "outstanding_inspections"),
        (alice, rc()),
        (alice, rc()),
        (alice, rc()),
        (alice, rc()),
        (bob, rc()),
        (bob, rc()),
        (bob, rc()),
        (bob, rc()),
        (clare, rc()),
        (clare, rc()),
        (clare, rc()),
        (clare, rc()),
        (derek, rc()),
        (derek, rc()),
        (derek, rc()),
        (derek, rc()),
        (admin, "stop"),
    ]

    for item in setup:
        item[0](item[1])
