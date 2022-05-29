from test_bots import *

# eth_addr = "0x0B36748D853621251D5249c18fC18B5ab47437a1"
alice_eth_addr = "0x4f812c24109BDAf3b4630a0aE8Bea34BEAb7e581"
bob_eth_addr = "0x6b5CBFBF2173b4a2E4BA43aE3CefD0dE84C859b1"
clare_eth_addr = "0x72eda8030E0784d58A101DBBaEa918D18927E06d"
derek_eth_addr = "0xd34803F01A38fC5f2B709Bca3b9681fbf5350A29"

setup = [
    # (admin, "Item 1"),
    # (admin, "open"),
    # (alice, "Single Item Demo"),
    # (alice, alice_eth_addr),
    # (bob, "Single Item Demo"),
    # (bob, bob_eth_addr),
    # (clare, "Single Item Demo"),
    # (clare, clare_eth_addr),
    # (admin, "close"),
    # (admin, "start"),
    # (alice, rc()),
    # (bob, rc()),
    # (clare, rc()),
    # (admin, "stop"),
]

for item in setup:
    item[0](item[1])
