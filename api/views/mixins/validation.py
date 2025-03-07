import re
import time
import json
from decimal import Decimal

from datetime import datetime
from django.core.exceptions import ValidationError

from api.utilities.logging import log_info, log_error, log_warning
from api.utilities.validation import is_valid_json, is_valid_amount, is_valid_percentage

class ValidationMixin:
    """
    Mixin for validating request parameters, contract types, addresses, dates, and other fields.
    """

    def _validate_required_params(self, data, required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_contract_type(self, contract_type, registry_manager):
        valid_contract_types = registry_manager.get_contract_types()
        if contract_type not in valid_contract_types:
            raise ValidationError(f"Invalid contract type: {contract_type}. Allowed: {', '.join(valid_contract_types)}")

    def _validate_contract_idx(self, contract_idx, contract_type, contract_api, delay=5, retries=3):

        if not isinstance(contract_idx, int) or contract_idx < 0:
            raise ValidationError(f"Invalid contract index: {contract_idx}. Must be a non-negative integer.")

        for attempt in range(retries):
            try:
                response = contract_api.get_contract_count(contract_type)

                if response["status"] != 200:
                    raise ValidationError(f"Failed to retrieve contract count: {response.get('message', 'Unknown error')}")

                contract_count = response["data"]["count"]

                if 0 <= contract_idx < contract_count:
                    return  # Validation successful

                log_warning(self.logger, f"Contract index {contract_idx} is out of range (0 to {contract_count - 1}). "
                                        f"Attempt {attempt + 1} of {retries}. Retrying in {delay} seconds...")

            except Exception as e:
                log_error(self.logger, f"Error validating contract index: {e}")
                if attempt == retries - 1:
                    raise ValidationError(f"Validation failed for contract index {contract_idx}: {e}")

            time.sleep(delay)  # Sleep only when there's an issue

        raise ValidationError(f"Contract index {contract_idx} is out of range. Expected range: 0 to {contract_count - 1}.")

    def _validate_wallet_address(self, wallet_address):
        if not re.match(r"^0x[a-fA-F0-9]{40}$", wallet_address):
            raise ValidationError(f"Invalid Ethereum address: {wallet_address}")

    def _validate_tx_hash(self, tx_hash):
        if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
            raise ValidationError(f"Invalid transaction hash: {tx_hash}")

    def _validate_chain(self, chain_name, config_manager):
        valid_chains = [chain["key"] for chain in config_manager.get_chain_list()]
        if chain_name not in valid_chains:
            raise ValidationError(f"Invalid chain name: {chain_name}. Allowed: {', '.join(valid_chains)}")

    def _validate_positive_number(self, number, field_name):
        if number is None or number <= 0:
            raise ValidationError(f"{field_name} must be a positive number.")

    def _validate_datetime_format(self, date_str, field_name, date_format="%Y-%m-%d"):
        try:
            datetime.strptime(date_str, date_format)
        except ValueError:
            raise ValidationError(f"{field_name} must be in the format {date_format}.")

    def _validate_enum_value(self, value, valid_values, field_name):
        if value not in valid_values:
            raise ValidationError(f"Invalid {field_name}: {value}. Allowed values: {', '.join(valid_values)}.")

    def _validate_api_key(self, api_key, secrets_manager):
        valid_keys = secrets_manager.get_all_partner_keys()  # Expecting valid_keys to be a dictionary
        if api_key not in valid_keys.values():
            raise ValidationError("Invalid API key.")

    def _validate_request_data(self, serializer_class, data, many=False):
        serializer = serializer_class(data=data, many=many)  # Pass 'many' here
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _validate_parties(self, party_list, config_manager):

        if not isinstance(party_list, list):
            raise ValidationError("Invalid party list. Expected a list of party objects.")

        invalid_parties = []
        for party in party_list:
            party_code = party.get("party_code")
            if not party_code:
                raise ValidationError(f"Party entry is missing 'party_code': {party}")

            if not config_manager.get_party_address(party_code):
                invalid_parties.append(party_code)

        if invalid_parties:
            raise ValidationError(f"Invalid parties found: {', '.join(invalid_parties)}. "
                                  f"These parties do not exist in the configuration.")

    def _validate_settlements(self, settlement_list):

        if not isinstance(settlement_list, list):
            raise ValidationError("Invalid settlements list. Expected a list of settlement objects.")

        for idx, settlement in enumerate(settlement_list):
            if not isinstance(settlement, dict):
                raise ValidationError(f"Invalid settlement at index {idx}. Expected a dictionary.")

            transact_min_dt = settlement.get("transact_min_dt")
            transact_max_dt = settlement.get("transact_max_dt")
            settle_due_dt = settlement.get("settle_due_dt")

            # Ensure they are datetime objects (should already be converted by serializer)
            for field in ["transact_min_dt", "transact_max_dt", "settle_due_dt"]:
                if field in settlement:
                    if not isinstance(settlement[field], datetime):
                        raise ValidationError(f"Invalid date types in settlement at index {idx}. Field {field} must be datetime object.")

            # Check constraints
            if "transact_max_dt" in settlement:
                if transact_max_dt > settle_due_dt:
                    raise ValidationError(f"Invalid settlement at index {idx}: transact_max_dt ({transact_max_dt}) must be <= settle_due_dt ({settle_due_dt}).")

            if "transact_min_dt" in settlement:
                if transact_min_dt > transact_max_dt:
                    raise ValidationError(f"Invalid settlement at index {idx}: transact_min_dt ({transact_min_dt}) must be <= transact_max_dt ({transact_max_dt}).")

    def _validate_transactions(self, transaction_list):

        if not isinstance(transaction_list, list):
            raise ValidationError("Invalid transaction list. Expected a list of transaction objects.")

        for idx, transaction in enumerate(transaction_list):
            if not isinstance(transaction, dict):
                raise ValidationError(f"Invalid transaction at index {idx}. Expected a dictionary.")

            # Validate `extended_data`
            if "extended_data" not in transaction:
                raise ValidationError(f"Missing 'extended_data' in transaction at index {idx}.")
            if not isinstance(transaction["extended_data"], dict):
                raise ValidationError(f"'extended_data' must be a dictionary (parsed JSON) at index {idx}.")

            # Validate `transact_data`
            if "transact_data" not in transaction:
                raise ValidationError(f"Missing 'transact_data' in transaction at index {idx}.")
            if not isinstance(transaction["transact_data"], dict):
                raise ValidationError(f"'transact_data' must be a dictionary (parsed JSON) at index {idx}.")

            # Validate `transact_dt` (must be a datetime object at this stage)
            if "transact_dt" not in transaction:
                raise ValidationError(f"Missing 'transact_dt' in transaction at index {idx}.")
            if not isinstance(transaction["transact_dt"], datetime):
                raise ValidationError(f"'transact_dt' must be a datetime object at index {idx}. Ensure the serializer converts it properly.")

    def _validate_contract(self, contract):

        # Validate JSON fields
        for field in ["transact_logic", "extended_data"]:
            if field in contract:
                if not is_valid_json(contract[field]):
                    raise ValidationError(f"Invalid JSON for '{field}': '{contract[field]}'.")

        # Validate Boolean fields
        for field in ["is_active", "is_quote"]:
            if not isinstance(contract[field], bool):
                raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be true or false.")

        # Validate contract_name and notes
        for field in ["contract_name"]:
            if field in contract:
                if not isinstance(contract[field], str) or not contract[field].strip():
                    raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be a non-empty string.")

        # Validate min/max threshold amounts
        for field in ["min_threshold_amt", "max_threshold_amt"]:
            if field in contract:
                if not isinstance(contract[field], str) or not is_valid_amount(contract[field], allow_negative=True):
                    raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be a valid amount.")
                if Decimal(contract["min_threshold_amt"]) > Decimal(contract["max_threshold_amt"]):
                    raise ValidationError(
                        f"'min_threshold_amt' ({contract['min_threshold_amt']}) must be less than or equal to 'max_threshold_amt' ({contract['max_threshold_amt']})."
                )

        # Validate funding_instr
        if contract["funding_instr"]["bank"] not in self.registry_manager.get_banks():
            raise ValidationError(f"Invalid bank: '{contract['funding_instr']['bank']}'")

        # Validate funding_instr and deposit_instr if they exist
        for instr in ["funding_instr", "deposit_instr"]:
            if instr in contract:
                if contract[instr]["bank"] not in self.registry_manager.get_banks():
                    raise ValidationError(f"Invalid bank: '{contract[instr]['bank']}'")

        # Validate percentage fields
        for field in ["service_fee_pct", "service_fee_max", "advance_pct", "late_fee_pct"]:
            if field in contract:
                if not isinstance(contract[field], str) or not is_valid_percentage(contract[field]):
                    raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be in the form X.XXXX and between 0.0000 and 1.0000.")

        # Validate amount fields
        for field in ["service_fee_amt", "max_threshold_amt"]:
            if field in contract:
                if not isinstance(contract[field], str) or not is_valid_amount(contract[field]):
                    raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be a valid amount.")

        # Validate service_fee_max <= service_fee_pct if both exist
        if "service_fee_pct" in contract and "service_fee_max" in contract:
            if contract["service_fee_pct"] > contract["service_fee_max"]:
                raise ValidationError(
                f"'service_fee_max' must be less than or equal to 'service_fee_pct'."
            )