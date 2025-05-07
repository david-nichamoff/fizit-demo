import json
import openai
import os

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

def translate_transact_logic_to_natural(secrets_manager, transact_logic):
    client = openai.OpenAI(api_key=secrets_manager.get_openai_key())

    if isinstance(transact_logic, str):
        try:
            transact_logic = json.loads(transact_logic)
        except Exception:
            return "Invalid JSON logic"

    try:
        prompt = (
            "Translate the following JSON Logic expression into a plain English description "
            "suitable for business users:\n\n"
            f"{json.dumps(transact_logic, indent=2)}"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates JSON logic into plain English."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.2,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Failed to generate natural language: {str(e)}"