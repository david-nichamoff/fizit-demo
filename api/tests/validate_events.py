import requests
import time
import json
from rest_framework import status

import packages.load_config as load_config

config = load_config.load_config()

def validate_events(contract_idx, contract_addr, headers, expected_events, retries=3, delay=5):
    url = f"{config['url']}/api/contract-events/?contract_idx={contract_idx}&contract_addr={contract_addr}"
    time.sleep(delay)

    for attempt in range(retries):
        response = requests.get(url, headers=headers)

        if response.status_code == status.HTTP_200_OK:
            events = response.json()
            event_found = {event_type: False for event_type in expected_events}

            for event in events:
                event_type = event['event_type']
                if event_type in expected_events:
                    if event_type in ["SettlementAdded", "TransactionAdded", "PartyDeleted", "PartiesDeleted",
                                      "TransactionsDelete","SettlementsDeleted"]:
                        # Simply mark the event as found, without checking event_details
                        event_found[event_type] = True
                        print(f"{event_type} event found for contract {contract_idx}")
                    else:
                        # Handle function-based comparison for other event types
                        if expected_events[event_type](event):
                            event_found[event_type] = True
                            print(f"{event_type} event found for contract {contract_idx}")

            if all(event_found.values()):
                return event_found
            else:
                print(f"Not all events found: {event_found}. Retrying in {delay} seconds...")
                time.sleep(delay)
        else:
            print(f"Failed to get contract events for contract {contract_idx}, status code: {response.status_code}, response: {response.text}")
            time.sleep(delay)

    # If retries are exhausted and not all events are found, raise an error
    print(f"Events found: {events}")
    raise AssertionError(f"Failed to validate all expected events for contract {contract_idx}")