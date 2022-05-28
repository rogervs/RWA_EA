#!/usr/bin/env python3


import json
from eth_abi import encode_abi
from fastapi import FastAPI, Body
import logging
import asyncio

# import uvicorn
from uvicorn import Config, Server

from audit import Audits, Audit, AuditInit, Auditor, DataDumpRequest
from getpass import getpass
from argparse import ArgumentParser
from xmpp_interface import RWABot


# from xmpp_interface import *


app = FastAPI()


@app.post("/register_audit/")
async def register_audit(payload: dict = Body(...)):
    audit_init = payload["data"]
    print("Data unit stuff audit init")
    print(audit_init)
    audit = Audit(
        name=audit_init["name"],
        admin_jid=audit_init["admin_jid"],
        bond=audit_init["bond"],
    )
    return xmpp.add_audit(audit)


@app.get("/clear_audits/")
async def clear_audits():
    xmpp.audits.clear()


@app.post("/data_dump/")
async def data_dump(payload: dict = Body(...)):
    data_request = payload["data"]
    addresses, amounts = xmpp.get_audit_outcome(data_request["name"])

    bytedata = "0x" + encode_abi(["address[]", "uint16[]"], [addresses, amounts]).hex()
    http_conclude_response = {"data": {"response": bytedata}}

    return http_conclude_response


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    args = {}
    args["jid"] = "botty@foxhole"
    args["password"] = "botty"

    xmpp = RWABot(args["jid"], args["password"])

    xmpp.connect()

    config = Config(app=app, loop=xmpp.loop, port=8080)
    server = Server(config)

    xmpp.loop.run_until_complete(server.serve())
