import json
import random
from datetime import datetime, timedelta

def generate_transactions(start_date, period_type, end_date, transact_type):
    records = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    while current_date <= end_date:
        if period_type == "daily":
            # Daily transactions at noon with random offset
            transact_dt = current_date.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(minutes=random.randint(-300, 300))
            volume = random.randint(400, 600)
        elif period_type == "hourly":
            # Hourly transactions at each hour with random offset
            transact_dt = current_date.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=random.randint(0, 10))
            volume = random.randint(10, 30)
        else:
            raise ValueError("Invalid period type. Please choose 'hourly' or 'daily'.")

        transact_id = random.randint(1000, 9999)

        ext_id = {
            "transact_id": transact_id
        }

        if transact_type == "volume":
            price = random.randint(50, 150)
            transact_data = { "volume" : volume, "price" : price }
        else:
            ticket_amt = random.randint(300,600)
            transact_data = {"ticket_amt" : ticket_amt }

        records.append({
            "ext_id": ext_id,
            "transact_dt": transact_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "transact_data": transact_data
        })

        # Increment date based on period type
        if period_type == "daily":
            current_date += timedelta(days=1)
        elif period_type == "hourly":
            current_date += timedelta(hours=1)

    return records

def main():
    start_date = input("Enter start date (YYYY-MM-DD): ")
    period_type = input("Enter period type (hourly or daily): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    transact_type = input("Enter transaction type (volume or ticket): ")

    transactions = generate_transactions(start_date, period_type.lower(), end_date, transact_type.lower())

    with open("transactions.json", "w") as f:
        json.dump(transactions, f, indent=4)

    print(f"Transactions have been generated and saved to 'transactions.json'.")

if __name__ == "__main__":
    main()
