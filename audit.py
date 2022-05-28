#!/usr/bin/env python3

from random import random, choice
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
from fastapi import FastAPI, Body


class State(Enum):
    INITIALIZATION = 0
    AUDITOR_REGISTRATION = 1
    AUDITOR_REGISTRATION_COMPLETE = 2
    AUDITING = 3
    AUDITING_FINISHED = 4
    CALCULATED_ITEM_RESULTS = 5
    CALCULATED_AUDIT_RESULTS = 6
    CALCULATED_AUDITOR_RESULTS = 7
    WAITING_FOR_CONTRACT = 8
    COMPLETE = 9


class AuditorState(Enum):
    INIT = 0
    REQUESTING_PROJECT = 1
    REQUESTING_CRYPTO_ADDR = 2
    WAITING_CRYPTO_ADDR_CONFIRM = 3
    READY = 4


class Auditor(BaseModel):
    jid: str
    addr: str = ""
    state: AuditorState = AuditorState.INIT
    audit: str = ""
    current_inspection: int | None
    audit_count: int = 0
    audits_aligned: int = 0
    compensation: float = 0


# For communicating with through fastAPI
class AuditInit(BaseModel):
    data: dict
    meta: dict
    id: str
    # name: str
    #
    # admin_jid: str
    # bond: int


class DataDumpRequest(BaseModel):
    name: str


class Audit(BaseModel):
    class Config:
        underscore_attrs_are_private = True

    class Inspection(BaseModel):
        auditor: str
        item: int
        inspection_id: int
        completed: bool = False
        finding: bool = False
        aligned: bool = False

    name: str
    admin_jid: str
    bond: float
    inspection_reward: float = 0

    auditors: Dict[str, Auditor] = {}

    messages = {
        "welcome_message": "You will be notified when the audit begins",
        "waiting_for_start": "Hold your horses",
        "project_not_open_yet": "Requested project is not accepting new auditors yet, please try again later",
        "registration_closed": "Registration for new auditors has closed",
        "start_message": "Audit has started",
        "auditing_stopped": "Audit has finished",
        "waiting_for_calculations": "Outcomes are being calculated. You will be notified once the results are ready.",
        "assignment_message": "You have been assigned the following inspection: ",
        "auditor_complete": "You have complete all your tasks. You will be notified when this phase is complete",
        "compensation_message": "Your compensation is :",
    }

    number_of_audits_per_item: int = 3

    items: List[str] = []

    def number_of_items(self):
        return len(self.items)

    slashing_ratio: float = 0.5

    state: State = State.INITIALIZATION

    inspections: List[Inspection] = []

    _item_results: List[bool] = []
    # _auditor_audits_aligned: List[int] = []
    # _auditor_audits_count: List[int] = []

    # auditor_compensation: List[float] = []

    def register_auditor(self, auditor: Auditor):
        assert self.state == State.AUDITOR_REGISTRATION
        self.auditors[auditor.jid] = auditor

    def is_jid_registered(self, jid: str):
        return jid in self.auditors

    def add_item(self, description: str):
        self.items.append(description)

    def delete_item(self, number):
        del self.items[number]

    def list_items(self):
        return self.items

    def list_items_for_print(self):
        output = ""
        for number, description in enumerate(self.items):
            output += f"{number} : {description}\n"
        return output

    def calculate_inspection_reward(self):
        self.inspection_reward = self.bond / (
            len(self.items) * self.number_of_audits_per_item
        )

    def assign_auditors_to_items(self):
        inspection_count = 0
        auditors = []
        for key in self.auditors.keys():
            auditors.append(key)
        auditor_iterator = 0
        num_auditors = len(auditors)

        for item_iterator in range(len(self.items)):
            for audit_per_item_iterator in range(self.number_of_audits_per_item):
                self.inspections.append(
                    self.Inspection(
                        **{
                            "auditor": auditors[auditor_iterator],
                            "item": item_iterator,
                            "inspection_id": inspection_count,
                        }
                    )
                )
                inspection_count += 1
                auditor_iterator += 1
                if auditor_iterator >= num_auditors:
                    auditor_iterator = 0

    def get_item_audits(self, item):
        item_audits = []

        for inspect in self.inspections:
            if inspect.item == item:
                item_audits.append(inspect)

        return item_audits

    def get_auditor_audits(self, auditor: Auditor):
        auditor_audits = []

        for inspect in self.inspections:
            if inspect.auditor == auditor.jid:
                auditor_audits.append(inspect)

        return auditor_audits

    def get_outstanding_item_audits(self, item):
        outstanding_audits = []
        audits = self.get_item_audits(item)
        for audit in audits:
            if not audit.completed:
                outstanding_audits.append(audit)
        return outstanding_audits

    def get_outstanding_auditor_audits(self, auditor: Auditor):
        outstanding_audits = []
        audits = self.get_auditor_audits(auditor)
        for audit in audits:
            if not audit.completed:
                outstanding_audits.append(audit)
        return outstanding_audits

    def auditor_done(self, auditor):
        return len(self.get_outstanding_auditor_audits(auditor)) == 0

    def assign_current_inspection(self, auditor: Auditor):
        # Randomly assign an auditor an inspection to perform
        outstanding_audits = self.get_outstanding_auditor_audits(auditor)
        if len(outstanding_audits) > 0:
            auditor.current_inspection = choice(outstanding_audits).inspection_id
            return True
        else:
            auditor.current_inspection = None
        return False

    def assign_all_current_inspection(self):
        for auditor in self.auditors.values():
            self.assign_current_inspection(auditor)

    def get_outstanding_audits(self):
        outstanding_audits = []
        for inspection in self.inspections:
            if not inspection.completed:
                outstanding_audits.append(inspection)
        return outstanding_audits

    def get_outstanding_audits_for_print(self):
        outstanding_audits = []
        for inspection in self.inspections:
            if not inspection.completed:
                outstanding_audits.append(
                    f"{inspection.auditor} -> {self.items[inspection.item]}"
                )
        return "\n".join(outstanding_audits)

    def inspection_id_to_description(self, id: int):
        return self.items[self.inspections[id].item]

    def auditor_current_inspection(self, auditor: Auditor):
        current_inspection = auditor.current_inspection
        self.inspection_id_to_description(current_inspection)

    def set_audit(self, auditor, item, finding):
        assert self.state == State.AUDITING, "Not currently auditing"
        audit_found = False
        audits = self.get_auditor_audits(auditor)
        for audit in audits:
            if audit.item == item:
                audit_found = True
                temp_audit = audit
                temp_audit.finding = finding
                temp_audit.completed = True
                self.inspections[temp_audit.inspection_id] = temp_audit
                break

        if audit_found:
            return True
        else:
            return False

    def set_audit_by_audit(self, audit, finding):
        assert self.state == State.AUDITING, "Not currently auditing"
        temp_audit = self.inspections[audit]
        temp_audit.completed = True
        temp_audit.finding = finding
        self.inspections[audit] = temp_audit

    def check_if_audit_complete(self):
        return len(self.get_outstanding_audits()) == 0

    def calculate_item_results(self):
        # Check if in correct state
        assert self.check_if_audit_complete(), "Audit not complete"
        assert self.state == State.AUDITING_FINISHED, "Not in AUDITING_FINISHED state"
        self._item_results = []
        for item in range(self.number_of_items()):
            item_finding = 0
            for audit in self.get_item_audits(item):
                if audit.finding:
                    item_finding += 1
                else:
                    item_finding -= 1
            self._item_results.append(item_finding > 0)

        # Set state for next phase
        self.state = State.CALCULATED_ITEM_RESULTS

    def calculate_audit_results(self):
        assert (
            self.state == State.CALCULATED_ITEM_RESULTS
        ), "Not currently calculating item results"
        self.state = State.CALCULATED_AUDIT_RESULTS
        for audit in self.inspections:
            audit.aligned = audit.finding == self._item_results[audit.item]

    def calculate_auditor_results(self):
        # Check if in correct state
        assert (
            self.state == State.CALCULATED_AUDIT_RESULTS
        ), "Not currently calculating audit results"

        for auditor in self.auditors.values():
            audit_count = 0
            aligned_count = 0
            for audit in self.get_auditor_audits(auditor):
                audit_count += 1
                if audit.aligned:
                    aligned_count += 1
            auditor.audit_count = audit_count
            auditor.audits_aligned = aligned_count

        # Set state for next phase
        self.state = State.CALCULATED_AUDITOR_RESULTS

    def calculate_auditor_compensation(self):
        # Check if in correct state
        assert (
            self.state == State.CALCULATED_AUDITOR_RESULTS
        ), "Not currently calculating auditor results"

        for auditor in self.auditors.values():
            incorrect_answers = auditor.audit_count - auditor.audits_aligned
            compensation_units = max(
                0,
                auditor.audits_aligned - self.slashing_ratio * incorrect_answers,
            )
            auditor.compensation = compensation_units * self.inspection_reward

        # Set state for next phase
        self.state = State.WAITING_FOR_CONTRACT


class Audits:
    def __init__(self):
        self.audits = dict()

    def add_audit(self, audit: Audit):
        if audit.name in self.audits:
            return "9"
        self.audits[audit.name] = audit
        return 200

    def jid_in_audit(self, jid):
        for audit in self.audits.values():
            if jid in audit.auditors:
                return audit, audit.auditors[jid], audit.auditors[jid].state
        return (None, None, None)

    def jid_in_admin(self, jid):
        for audit in self.audits.values():
            if jid == audit.admin_jid:
                return audit
        return None

    def jid_to_auditor(self, jid):
        for audit in self.audits.values():
            if jid in audit.auditors:
                return audit.auditors[jid]
        return None

    def get_audit_outcome(self, audit_name):
        audit = self.audits.get(audit_name, None)

        if audit == None:
            return [], []

        if audit.state != State.WAITING_FOR_CONTRACT:
            return [], []

        addresses = []
        amounts = []
        for beneficiary in audit.auditors.values():
            addresses.append(beneficiary.addr)
            amounts.append(int(beneficiary.compensation))

        print("Addresses:")
        print(addresses)
        print("Amounts")
        print(amounts)

        audit.state = State.COMPLETE

        return addresses, amounts
