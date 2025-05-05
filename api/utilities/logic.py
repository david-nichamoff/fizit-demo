def extract_transaction_variables(logic):
    variables = set()

    if isinstance(logic, dict):
        for key, value in logic.items():
            if key == "var" and isinstance(value, str):
                variables.add(value)
            else:
                variables.update(extract_transaction_variables(value))
    elif isinstance(logic, list):
        for item in logic:
            variables.update(extract_transaction_variables(item))

    return variables