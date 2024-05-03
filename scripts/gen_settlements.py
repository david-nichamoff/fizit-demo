import json
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

def generate_records(first_invoice_start_date, period_type, number_of_periods, first_transaction_start_date):
    records = []
    current_invoice_date = datetime.strptime(first_invoice_start_date, "%Y-%m-%d")
    current_transaction_min_date = datetime.strptime(first_transaction_start_date, "%Y-%m-%d")
    
    if period_type == "weekly":
        invoice_delta = relativedelta(weeks=1)
        transaction_delta = relativedelta(weeks=1)
    elif period_type == "monthly":
        invoice_delta = relativedelta(months=1)
        transaction_delta = relativedelta(months=1)
    else:
        raise ValueError("Invalid period type. Please choose 'weekly' or 'monthly'.")

    for i in range(number_of_periods):
        settle_due_dt = (current_invoice_date + (i * invoice_delta)).strftime("%Y-%m-%d")
        transact_min_dt = current_transaction_min_date + (i * transaction_delta)
        transact_max_dt = transact_min_dt + transaction_delta
        
        ref_no = random.randint(1000, 9999)
        ext_id = {"ref_no": ref_no}
        
        records.append({
            "settle_due_dt": settle_due_dt,
            "transact_min_dt": transact_min_dt.strftime("%Y-%m-%d"),
            "transact_max_dt": transact_max_dt.strftime("%Y-%m-%d"),
            "ext_id": ext_id
        })

    return records

def main():
    first_invoice_start_date = input("Enter first settlement due date (YYYY-MM-DD): ")
    first_transaction_start_date = input("Enter first transaction start date (YYYY-MM-DD): ")
    period_type = input("Enter period type (weekly or monthly): ")
    number_of_periods = int(input("Enter number of periods: "))

    records = generate_records(first_invoice_start_date, period_type.lower(), number_of_periods, first_transaction_start_date)

    with open("settlements.json", "w") as f:
        json.dump(records, f, indent=4)

    print(f"{number_of_periods} records have been generated and saved to 'settlements.json'.")

if __name__ == "__main__":
    main()
