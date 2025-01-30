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
        """
        Validate that all required fields are present in the request data.
        :param data: Dictionary containing request parameters.
        :param required_fields: List of required field names.
        :raises ValidationError: If a required field is missing.
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_contract_type(self, contract_type, registry_manager):
        """
        Validate that the provided contract type exists in the registry.
        :param contract_type: The contract type to validate.
        :param registry_manager: Instance of RegistryManager.
        :raises ValidationError: If the contract type is invalid.
        """
        valid_contract_types = registry_manager.get_contract_types()
        if contract_type not in valid_contract_types:
            raise ValidationError(f"Invalid contract type: {contract_type}. Allowed: {', '.join(valid_contract_types)}")

    def _validate_contract_idx(self, contract_idx, contract_type, contract_api, delay=5, retries=3):
        """
        Validate that the provided contract index (contract_idx) exists within the valid range.

        This method checks if the contract_idx is within the range [0, contract_count - 1].
        If the validation fails, it retries the check after a delay for the specified number of attempts.

        Args:
            contract_type (str): The type of contract being validated.
            contract_idx (int): The contract index to validate.
            contract_api: The contract API instance used to fetch contract count.
            delay (int, optional): Time (in seconds) to wait before retrying. Default is 5 seconds.
            retries (int, optional): Number of retries allowed if validation fails. Default is 3.

        Raises:
            ValidationError: If contract_idx is out of range after all retries.
        """
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
        """
        Validate Ethereum wallet address format.
        :param wallet_address: The wallet address to validate.
        :raises ValidationError: If the address format is invalid.
        """
        if not re.match(r"^0x[a-fA-F0-9]{40}$", wallet_address):
            raise ValidationError(f"Invalid Ethereum address: {wallet_address}")

    def _validate_tx_hash(self, tx_hash):
        """
        Validate Ethereum transaction hash format.
        :param tx_hash: The transaction hash to validate.
        :raises ValidationError: If the transaction hash format is invalid.
        """
        if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
            raise ValidationError(f"Invalid transaction hash: {tx_hash}")

    def _validate_chain(self, chain_name, config_manager):
        """
        Validate that the provided chain exists in the configuration.
        :param chain_name: The chain name to validate.
        :param config_manager: Instance of ConfigManager.
        :raises ValidationError: If the chain is invalid.
        """
        valid_chains = [chain["key"] for chain in config_manager.get_chain_list()]
        if chain_name not in valid_chains:
            raise ValidationError(f"Invalid chain name: {chain_name}. Allowed: {', '.join(valid_chains)}")

    def _validate_positive_number(self, number, field_name):
        """
        Validate that a given number is positive.
        :param number: The number to validate.
        :param field_name: The name of the field being validated.
        :raises ValidationError: If the number is not positive.
        """
        if number is None or number <= 0:
            raise ValidationError(f"{field_name} must be a positive number.")

    def _validate_datetime_format(self, date_str, field_name, date_format="%Y-%m-%d"):
        """
        Validate date format.
        :param date_str: The date string to validate.
        :param field_name: The name of the field being validated.
        :param date_format: The expected date format.
        :raises ValidationError: If the date format is incorrect.
        """
        try:
            datetime.strptime(date_str, date_format)
        except ValueError:
            raise ValidationError(f"{field_name} must be in the format {date_format}.")

    def _validate_enum_value(self, value, valid_values, field_name):
        """
        Validate that a value is in a set of allowed enum values.
        :param value: The value to validate.
        :param valid_values: List of valid values.
        :param field_name: The name of the field being validated.
        :raises ValidationError: If the value is not allowed.
        """
        if value not in valid_values:
            raise ValidationError(f"Invalid {field_name}: {value}. Allowed values: {', '.join(valid_values)}.")

    def _validate_api_key(self, api_key, secrets_manager):
        """
        Validate API key against stored secrets.
        :param api_key: The API key to validate.
        :param secrets_manager: Instance of SecretsManager.
        :raises ValidationError: If the API key is invalid.
        """
        valid_keys = secrets_manager.get_all_partner_keys()  # Expecting valid_keys to be a dictionary
        if api_key not in valid_keys.values():
            raise ValidationError("Invalid API key.")

    def _validate_request_data(self, serializer_class, data, many=False):
        """
        Validate the request data using the given serializer class.

        Args:
            serializer_class: The DRF serializer class for validation.
            data (dict or list): The request data to validate.
            many (bool): Whether to allow multiple records (e.g., list of objects).

        Returns:
            dict or list: Validated data from the serializer.

        Raises:
            ValidationError: If the data does not pass validation.
        """
        serializer = serializer_class(data=data, many=many)  # Pass 'many' here
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _validate_parties(self, party_list, config_manager):
        """
        Validate that all provided parties exist in the configuration.

        Args:
            party_list (list): List of party objects to validate.
            config_manager (ConfigManager): Instance of ConfigManager.

        Raises:
            ValidationError: If a party does not exist in the configuration.
        """
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
        """
        Validate settlement constraints after serialization.

        Ensures:
        - transact_min_dt, transact_max_dt, and settle_due_dt are present and datetime objects.
        - transact_max_dt is before or equal to settle_due_dt.
        - transact_min_dt is before or equal to transact_max_dt.

        Args:
            settlement_list (list): List of settlement dictionaries to validate.

        Raises:
            ValidationError: If any validation check fails.
        """
        if not isinstance(settlement_list, list):
            raise ValidationError("Invalid settlements list. Expected a list of settlement objects.")

        for idx, settlement in enumerate(settlement_list):
            if not isinstance(settlement, dict):
                raise ValidationError(f"Invalid settlement at index {idx}. Expected a dictionary.")

            transact_min_dt = settlement.get("transact_min_dt")
            transact_max_dt = settlement.get("transact_max_dt")
            settle_due_dt = settlement.get("settle_due_dt")

            # Ensure all required fields are present
            if transact_min_dt is None or transact_max_dt is None or settle_due_dt is None:
                raise ValidationError(f"Missing required fields in settlement at index {idx}.")

            # Ensure they are datetime objects (should already be converted by serializer)
            if not all(isinstance(dt, datetime) for dt in [transact_min_dt, transact_max_dt, settle_due_dt]):
                raise ValidationError(f"Invalid date types in settlement at index {idx}. Fields must be datetime objects.")

            # Check constraints
            if transact_max_dt > settle_due_dt:
                raise ValidationError(f"Invalid settlement at index {idx}: transact_max_dt ({transact_max_dt}) must be <= settle_due_dt ({settle_due_dt}).")

            if transact_min_dt > transact_max_dt:
                raise ValidationError(f"Invalid settlement at index {idx}: transact_min_dt ({transact_min_dt}) must be <= transact_max_dt ({transact_max_dt}).")


    def _validate_transactions(self, transaction_list):
        """
        Validate that each transaction contains:
        - `extended_data` as a valid JSON object.
        - `transact_data` as a valid JSON object.
        - `transact_dt` exists and is a valid datetime object.

        Args:
            transaction_list (list): List of transaction dictionaries.

        Raises:
            ValidationError: If any validation check fails.
        """
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
        """
        Validate that each transaction contains:
        - `extended_data` as a valid JSON object.

        Args:
            contract: A contract dictionary

        Raises:
            ValidationError: If any validation check fails.
        """
        # Validate JSON fields
        for field in ["transact_logic", "extended_data"]:
            if field in contract:
                if not is_valid_json(contract[field]):
                    raise ValidationError(f"Invalid JSON for '{field}': '{contract[field]}'.")

        # Validate Boolean fields
        for field in ["is_active", "is_quote"]:
            if not isinstance(contract[field], bool):
                raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be true or false.")

        # Validate min/max threshold amounts
        if Decimal(contract["min_threshold_amt"]) > Decimal(contract["max_threshold_amt"]):
            raise ValidationError(
                f"'min_threshold_amt' ({contract['min_threshold_amt']}) must be less than or equal to 'max_threshold_amt' ({contract['max_threshold_amt']})."
            )

        # Validate contract_name and notes
        for field in ["contract_name", "notes"]:
            if not isinstance(contract[field], str) or not contract[field].strip():
                raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be a non-empty string.")

        # Validate funding_instr
        if contract["funding_instr"]["bank"] not in ['mercury', 'token']:
            raise ValidationError(f"Invalid bank: '{contract['funding_instr']['bank']}'. Valid banks: 'mercury', 'token'.")

        # Validate amounts
        for field in ["min_threshold_amt", "max_threshold_amt"]:
            if not isinstance(contract[field], str) or not is_valid_amount(contract[field], allow_negative=True):
                raise ValidationError(f"Invalid value for '{field}': '{contract[field]}'. Must be a valid amount.")

        # Validate funding_instr and deposit_instr if they exist
        for instr in ["funding_instr", "deposit_instr"]:
            if instr in contract:
                if contract[instr]["bank"] not in ['mercury', 'token']:
                    raise ValidationError(f"Invalid bank: '{contract[instr]['bank']}'. Valid banks: 'mercury', 'token'.")

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

        