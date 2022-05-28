#!/usr/bin/env python3

# Slixmpp: The Slick XMPP Library
# Copyright (C) 2010  Nathanael C. Fritz
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.

import logging
from getpass import getpass
from argparse import ArgumentParser
from typing import Dict
from web3 import Web3

import slixmpp

from audit import (
    State,
    AuditorState,
    Auditor,
    Audit,
    Audits,
)


class RWABot(slixmpp.ClientXMPP, Audits):

    """
    A bot that calls functions from XMPP commands
    """

    def __init__(self, jid, password):
        self.bot_jid = jid
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.start)

        self.add_event_handler("message", self.message)
        self.audits = {}

    async def start(self, event):
        """
        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        await self.get_roster()

    state_group = {
        "pre_waiting_states": {
            State.INITIALIZATION,
            State.AUDITOR_REGISTRATION,
            State.AUDITOR_REGISTRATION_COMPLETE,
        },
        "active_states": {State.AUDITING},
        "post_waiting_states": {
            State.AUDITING_FINISHED,
            State.CALCULATED_ITEM_RESULTS,
            State.CALCULATED_AUDIT_RESULTS,
            State.CALCULATED_AUDITOR_RESULTS,
        },
        "post_states": {State.WAITING_FOR_CONTRACT, State.COMPLETE},
    }

    messages = {
        "project_not_found": "Could not find any project by that name.",
        "project_welcome": "Which project would you like to join?",
        "project_registered": "You have registered for project:",
        "addr_request": "Enter your Ethereum address:",
        "addr_invalid": "Invalid Ethereum address.",
        "addr_accepted": "Address Accepted",
        "project_closed": "Requested project is not accepting new auditors",
        "audit_not_complete": "Not all inspections are done. Cannot finish audit",
        "funds_transfer": "The funds will automatically be transferred to the Ehtereum address you supplied",
    }

    def notify_auditors(self, audit: Audit, mbody: str):
        for auditor in audit.auditors:
            self.send_message(mto=auditor, mbody=mbody, mtype="chat")

    def notify_auditor_of_current_inspection(self, audit: Audit, auditor: Auditor):
        mbody = (
            audit.messages["assignment_message"]
            + "\n"
            + audit.inspection_id_to_description(auditor.current_inspection)
        )
        self.send_message(mto=auditor.jid, mbody=mbody, mtype="chat")

    def notify_all_auditors_of_current_inspection(self, audit: Audit):
        for auditor in audit.auditors.values():
            if auditor.current_inspection is not None:
                mbody = (
                    audit.messages["assignment_message"]
                    + "\n"
                    + audit.inspection_id_to_description(auditor.current_inspection)
                )
                self.send_message(mto=auditor.jid, mbody=mbody, mtype="chat")
            else:
                self.send_message(
                    mto=auditor.jid,
                    mbody=audit.messages["auditor_complete"],
                    mtype="chat",
                )

    def notify_auditor_of_compensation(self, audit: Audit, auditor: Auditor):
        mbody = (
            audit.messages["compensation_message"]
            + "\n"
            + str(auditor.compensation)
            + "\n"
            + self.messages["funds_transfer"]
        )
        self.send_message(mto=auditor.jid, mbody=mbody, mtype="chat")

    def notify_all_auditors_of_compensation(self, audit: Audit):
        for auditor in audit.auditors.values():
            self.notify_auditor_of_compensation(audit, auditor)

    def admin_command(self, audit, msg):
        body = msg["body"].strip()
        command = body.split()[0]
        try:
            variable = body.split()[1]
        except:
            variable = None

        try:
            value = " ".join(body.split()[2:])
        except:
            value = None

        try:
            payload = " ".join(body.split()[1:])
        except:
            payload = ""

        match command:
            # Allows users to register
            case "open":
                # Check if in correct state
                if audit.state == State.INITIALIZATION:
                    audit.calculate_inspection_reward()
                    msg.reply(
                        f"Project {audit.name} opened for auditors to register"
                    ).send()
                    msg.reply(
                        f"Reward per inspection set at: {audit.inspection_reward}"
                    ).send()
                    msg.reply(f"Slashing ratio set at: {audit.slashing_ratio}").send()

                    # Set state for next phase
                    audit.state = State.AUDITOR_REGISTRATION
                else:
                    msg.reply(
                        "Command can only be used when audit is in INITIALIZATION state"
                    ).send()

            # Closes registration window
            case "close":
                if audit.state == State.AUDITOR_REGISTRATION:
                    audit.state = State.AUDITOR_REGISTRATION_COMPLETE
                    msg.reply(f"Project {audit.name} closed for registration.").send()
                    self.notify_auditors(audit, audit.messages["registration_closed"])
                else:
                    msg.reply(
                        "Command can only be used when audit is in AUDITOR_REGISTRATION state"
                    ).send()

            # Start audit
            case "start":
                if audit.state == State.AUDITOR_REGISTRATION_COMPLETE:
                    audit.state = State.AUDITING
                    audit.assign_auditors_to_items()
                    msg.reply(f"Audit for project {audit.name} started.").send()
                    self.notify_auditors(audit, audit.messages["start_message"])
                    audit.assign_all_current_inspection()
                    self.notify_all_auditors_of_current_inspection(audit)
                else:
                    msg.reply(
                        "Command can only be used when audit is in AUDITOR_REGISTRATION_COMPLETE state"
                    ).send()

            # Stop Audit
            case "stop":
                if audit.state == State.AUDITING:

                    if audit.check_if_audit_complete():
                        audit.state = State.AUDITING_FINISHED
                        msg.reply(f"Audit for project {audit.name} stopped.").send()
                        self.notify_auditors(audit, audit.messages["auditing_stopped"])

                        audit.calculate_item_results()
                        audit.calculate_audit_results()
                        audit.calculate_auditor_results()
                        audit.calculate_auditor_compensation()

                        self.notify_all_auditors_of_compensation(audit)

                    else:
                        msg.reply(self.messages["audit_not_complete"]).send()
                        msg.reply(audit.get_outstanding_audits_for_print()).send()

                else:
                    msg.reply(
                        "Command can only be used when audit is in AUDITING state"
                    ).send()

            case "state":
                # Report audit state
                msg.reply(f"Audit State: {audit.state}").send()

            # Add a single item to the Audit. Can only be done before audit begins
            case "add":
                if audit.state in [
                    State.INITIALIZATION,
                ]:
                    audit.add_item(payload)
                    msg.reply(f"Item added. Item count: {len(audit.items)}").send()
                else:
                    msg.reply(
                        "Command can only be used when audit is in INITIALIZATION state"
                    ).send()

            # Delete an item from the audit
            case "del":
                if audit.state in [
                    State.INITIALIZATION,
                    State.AUDITOR_REGISTRATION,
                    State.AUDITOR_REGISTRATION_COMPLETE,
                ]:
                    variable = int(variable)
                    msg.reply(f"Item # {variable} : {audit.items[variable]}").send()
                    audit.delete_item(variable)
                    msg.reply(f"Item deleted. Item count: {len(audit.items)}").send()
                else:
                    msg.reply(
                        "Command can only be used when audit is in INITIALIZATION state"
                    ).send()

            # List items in audit
            case "items":
                msg.reply(audit.list_items_for_print()).send()

            # Show insepctions that are outstanding still
            case "outstanding_inspections":
                msg.reply(audit.get_outstanding_audits_for_print()).send()

            # Set a variable
            # TODO Decide whether to keep this guy - possibly hidden command
            # Not sure if this should stay, possible individual commands might be better
            case "set" if variable is not None:
                msg.reply(
                    f"Initial value of {variable}: {getattr(audit, variable)}"
                ).send()
                setattr(audit, variable, value)
                msg.reply(
                    f"Value of {variable} set to: {getattr(audit, variable)}"
                ).send()

            # Get the value of a variable
            case "get" if variable is not None:
                msg.reply(str(getattr(audit, variable))).send()

            # Show all public variables in audit object, with their current values
            case "list":
                for item in vars(audit):
                    msg.reply(f"{item} : {getattr(audit, item)}").send()

            # Display if no matches found
            case other:
                msg.reply(
                    f"\nYou are the admin for project\n {audit.name}\n======================="
                ).send()
                msg.reply("Command not found, or incorrect amount of arguments.").send()
                msg.reply("\nMain commands are:\n=======================").send()
                msg.reply("open : Allows auditors to register").send()
                msg.reply("close : Closes registration").send()
                msg.reply("start : Start the audit").send()
                msg.reply("stop : Stop the audit").send()
                msg.reply("state : Returns the current state of the audit").send()
                msg.reply("add <description> : Adds an item to the audit").send()
                msg.reply("items : Returns the items in the audit").send()
                msg.reply(
                    "del <number> : Deletess item from the audit. <number> is obtained from `item list`"
                ).send()
                msg.reply(
                    "set num_items <value> : Sets the number of items that need to be audited"
                ).send()
                msg.reply(
                    "set num_audits_per_item <value> : Sets the number audits per item (needs to be an odd number)"
                ).send()
                msg.reply(
                    "outstanding_inspections : Returns the outstanding audits"
                ).send()

                msg.reply("\nAvailable commands are:\n=======================").send()
                msg.reply(
                    "set slashing_ratio <value> : Sets the severity of the slash an auditor will receive for every incorrect observation"
                ).send()
                msg.reply("get <var>").send()
                msg.reply("list").send()

        return

    def auditor_command(self, audit: Audit, auditor: Auditor, msg):

        if audit.auditor_done(auditor):
            msg.reply(audit.messages["auditor_complete"]).send()
            return

        body = msg["body"].strip().lower()

        answer_true = {"yes", "true", "1", "y", "t"}
        answer_false = {"no", "false", "0", "n", "f"}

        if body in answer_true:
            audit.inspections[auditor.current_inspection].finding = True
            audit.inspections[auditor.current_inspection].completed = True
            if audit.assign_current_inspection(auditor):
                self.notify_auditor_of_current_inspection(audit, auditor)
            else:
                msg.reply(audit.messages["auditor_complete"]).send()

        elif body in answer_false:
            audit.inspections[auditor.current_inspection].finding = False
            audit.inspections[auditor.current_inspection].completed = True
            if audit.assign_current_inspection(auditor):
                self.notify_auditor_of_current_inspection(audit, auditor)
            else:
                msg.reply(audit.messages["auditor_complete"]).send()

        else:
            msg.reply("Answer not recognised.").send()
            msg.reply("Accepted replies for True are:").send()
            msg.reply(str(answer_true)).send()
            msg.reply("Accepted replies for False are:").send()
            msg.reply(str(answer_false)).send()
            msg.reply("Answers are case-insensitive").send()

            self.notify_auditor_of_current_inspection(audit, auditor)

    def message(self, msg):
        """
        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg["type"] in ("chat", "normal"):
            # Get relevant info from message
            jid = msg["from"].bare
            body = msg["body"].strip()

            # Check if client is admin -> present admin commands
            audit = self.jid_in_admin(jid)
            if audit is not None:
                self.admin_command(audit, msg)
                return

            # Check if client is registered with an audit
            (audit, auditor, state) = self.jid_in_audit(jid)
            if auditor is None:
                state = AuditorState.REQUESTING_PROJECT
                auditor = Auditor(**{"jid": jid})

            match state:
                # New user, get the project they interested in
                case AuditorState.REQUESTING_PROJECT:
                    if body in self.audits:
                        if self.audits[body].state == State.AUDITOR_REGISTRATION:
                            # Assign audit to auditor
                            auditor.audit = msg["body"]
                            # Add auditor to audit's auditor list
                            self.audits[msg["body"]].auditors[jid] = auditor
                            # Update state
                            auditor.state = AuditorState.REQUESTING_CRYPTO_ADDR
                            # Add auditor to audit
                            self.audits[auditor.audit].auditors[jid] = auditor
                            # Update user via xmpp
                            msg.reply(self.messages["project_registered"]).send()
                            msg.reply(auditor.audit).send()
                            msg.reply(
                                f"The per-inspection reward for this project is:\n{self.audits[body].inspection_reward}"
                            ).send()
                            msg.reply(
                                f"The slashing ratio for this project is:\n{self.audits[body].slashing_ratio}"
                            ).send()

                            msg.reply(self.messages["addr_request"]).send()
                        else:
                            if self.audits[body].state == State.INITIALIZATION:
                                # Project still being initialized, try again later
                                msg.reply(
                                    self.audits[body].messages["project_not_open_yet"]
                                ).send()
                                msg.reply(self.messages["project_welcome"]).send()
                            else:
                                # Audit is not accepting new auditors
                                msg.reply(self.messages["project_closed"]).send()
                                msg.reply(self.messages["project_welcome"]).send()

                    else:
                        # Audit name not valid, retry
                        msg.reply(self.messages["project_not_found"]).send()
                        msg.reply(self.messages["project_welcome"]).send()

                # Get user's crypto address
                case AuditorState.REQUESTING_CRYPTO_ADDR:
                    # Check if Ethereum address is valid
                    if Web3.isChecksumAddress(body):
                        auditor.addr = body
                        msg.reply(self.messages["addr_accepted"]).send()
                        msg.reply(audit.messages["welcome_message"]).send()
                        # Update state
                        auditor.state = AuditorState.READY
                    else:
                        # Invalid ethereum address
                        msg.reply(self.messages["addr_invalid"]).send()
                        msg.reply(self.messages["addr_request"]).send()

                # Message from registered user
                case AuditorState.READY:
                    if audit.state in self.state_group["pre_waiting_states"]:
                        msg.reply(audit.messages["waiting_for_start"]).send()
                    elif audit.state in self.state_group["active_states"]:
                        self.auditor_command(audit, auditor, msg)
                    elif audit.state in self.state_group["post_waiting_states"]:
                        msg.reply(audit.messages["waiting_for_calculations"]).send()
                    elif audit.state in self.state_group["post_states"]:
                        self.notify_auditor_of_compensation(audit, auditor)

                # self.auditor_command(audit, auditor, msg)

                # Nothing matched - probably a bug
                case other:
                    print("Somthing went wrong")


if __name__ == "__main__":
    # Setup the command line arguments.
    parser = ArgumentParser(description=RWABot.__doc__)

    # Output verbosity options.
    parser.add_argument(
        "-q",
        "--quiet",
        help="set logging to ERROR",
        action="store_const",
        dest="loglevel",
        const=logging.ERROR,
        default=logging.INFO,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="set logging to DEBUG",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid", help="JID to use")
    parser.add_argument("-p", "--password", dest="password", help="password to use")

    args = parser.parse_args()

    args.jid = "botty@foxhole"
    args.password = "botty"

    # Setup logging.
    logging.basicConfig(level=args.loglevel, format="%(levelname)-8s %(message)s")

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")

    # Setup the RWABot
    xmpp = RWABot(args.jid, args.password)

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
