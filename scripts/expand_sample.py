import csv
import random
from datetime import datetime, timedelta

# Configuration
NUM_ROWS = 1200
OUTPUT_FILE = "resources/samples/sample_masterlist.csv"

# Sample data pools
FIRST_NAMES = ["Juan", "Maria", "Pedro", "Ana", "Lisa", "Carlos", "Jose", "Elena", "Antonio", "Rosa"]
LAST_NAMES = ["Dela Cruz", "Santos", "Reyes", "Garcia", "Wong", "Mendoza", "Villanueva", "Lopez", "Bautista", "Aquino"]
MUNICIPALITIES = ["Manila", "Quezon City", "Makati", "Cebu City", "Davao City", "Pasig", "Taguig"]
SCHOOLS = ["Rizal Elementary School", "Bonifacio High School", "Mabini Academy", "Cebu Central School", "Quezon Science High", "Davao National High"]
SEXES = ["M", "F", "m", "f", "X", "Unknown"]

def generate_random_date():
    start_date = datetime(2005, 1, 1)
    end_date = datetime(2015, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def create_sample():
    rows = []
    header = ["learner_id", "learner_name", "birthdate", "sex", "municipality", "school", "age"]
    
    # 1. Add some fixed known duplicates and edge cases first
    rows.append(["LRN-001", "juan dela cruz", "15/03/2010", "M", "manila", "Rizal Elementary School", "14"])
    rows.append(["LRN-001", "Juan Dela Cruz", "2010-03-15", "M", "Manila", "Rizal Elementary School", "14"]) # Duplicate
    rows.append(["LRN-002", "MARIA SANTOS", "2011-07-22", "F", "Quezon City", "Bonifacio High School", "13"])
    rows.append(["lrn-003", "  Pedro   Reyes  ", "03-15-2009", "m", "Invalid Town", "Mabini Academy", "16"]) # Dirty
    rows.append(["", "Ana Garcia", "01/01/2012", "X", "Makati", "Unknown School", "12"]) # Missing ID, Invalid Sex
    
    # 2. Generate random bulk data
    for i in range(len(rows), NUM_ROWS):
        l_id = f"LRN-{i+1:04d}"
        
        # Randomly inject dirty data
        rand = random.random()
        
        # Name
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        name = f"{fname} {lname}"
        if rand < 0.1: name = name.lower()
        if rand < 0.05: name = f"  {name}  "
        
        # Date
        dt = generate_random_date()
        dt_str = dt.strftime("%Y-%m-%d")
        if rand < 0.1: dt_str = dt.strftime("%d/%m/%Y")
        if rand < 0.05: dt_str = "Invalid Date"
        
        # Sex
        sex = random.choice(SEXES) if rand < 0.1 else random.choice(["M", "F"])
        
        # Municipality
        muni = random.choice(MUNICIPALITIES)
        if rand < 0.05: muni = "Nowhere" # Validation failure
        
        # Age
        age = random.randint(5, 18)
        if rand < 0.02: age = 99 # Out of range
        
        # School
        school = random.choice(SCHOOLS)
        
        # Occasionally create a duplicate group
        if rand < 0.03 and len(rows) > 10:
            dup_target = random.choice(rows[5:])
            rows.append(dup_target.copy())
        else:
            rows.append([l_id, name, dt_str, sex, muni, school, str(age)])

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    
    print(f"Generated {len(rows)} rows in {OUTPUT_FILE}")

if __name__ == "__main__":
    create_sample()
