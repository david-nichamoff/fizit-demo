from api.models import ContractAuxiliary

def save_natural_language(contract_idx, contract_type, contract_release, logic_natural):
    aux, _ = ContractAuxiliary.objects.update_or_create(
        contract_idx=contract_idx,
        contract_type=contract_type,
        contract_release=contract_release,
        defaults={"logic_natural": logic_natural}
    )