# Real Word Assessor

A tool to coordinate and incentivise a set of independent actors to assess a set of independent criteria, using Chain link and XMPP to link block chain payment rails to real world activity.
Actors are assigned randomly to various criterion, with each criterion having at least three actors assessing it.
The system rewards actors whose assessment aligns with that of the majority, and penalizes assessments that go against.
Once an assessor has registered on chain, all other interaction between the assessor and the system is done via XMPP (Instant messaging), using Chain link to bring the results back on chain to automatically execute payment.

This is the external adapter/bot that talks to the chainlink node, either receiving instruction to initiate an audit, or sending the settlement details back to be executed.

## 5 Minute overview of what it does
[![5 Minutes Intro Video](https://img.youtube.com/vi/VxIKy8hyWeo/0.jpg)](https://www.youtube.com/watch?v=VxIKy8hyWeo)

## Contracts
The contracts are here https://github.com/rogervs/RWA_contracts

## Install
1. Create a python virtual environment using something like `pyenv-virtualenv`
2. Install dependencies. `pip install -r requirements.txt`

## Run
`python rwa.py`

## Tips
TCPFlow is a program that shows you the TCP stream going in and out of a port.
`sudo tcpflow -c -i lo port 8080`
