import sqlite3
import random
from datetime import date, timedelta, datetime
import collections

# --- 1. CORE CONFIGURATION ---

DATABASE_FILE = 'usage.db'
NUM_INACTIVE_USERS = 15 # Number of users to make inactive for the last 30 days
HISTORY_DAYS = 180    # Populate data for the last 6 months

# --- 2. USER AND APPLICATION DEFINITIONS ---

FEMALE_NAMES = [
    'Aaradhya', 'Aanya', 'Aashi', 'Aditi', 'Advika', 'Ahana', 'Alia', 'Amara', 'Ananya', 'Angel', 'Anika',
    'Anvi', 'Aria', 'Avani', 'Bhavna', 'Charvi', 'Diya', 'Esha', 'Fatima', 'Gauri', 'Ira', 'Ishani', 'Jiya',
    'Kavya', 'Khushi', 'Kiara', 'Larisa', 'Lavanya', 'Mahika', 'Maryam', 'Maya', 'Meher', 'Myra', 'Navya',
    'Neha', 'Nidhi', 'Pari', 'Priya', 'Rhea', 'Riya', 'Saanvi', 'Sahana', 'Sameera', 'Sara', 'Shreya',

    'Siya', 'Suhana', 'Tara', 'Vanya', 'Veda', 'Zoya', 'Aisha', 'Deepika', 'Freya', 'Inaya', 'Jasmine',
    'Mira', 'Naina', 'Prisha', 'Zara'
]
MALE_NAMES = [
    'Aarav', 'Aayush', 'Abdul', 'Aditya', 'Advik', 'Ahmed', 'Arjun', 'Aryan', 'Atharv', 'Ayush', 'Dev',
    'Dhruv', 'Farhan', 'Hassan', 'Ibrahim', 'Ishaan', 'Kabir', 'Kian', 'Krishna', 'Laksh', 'Madhav',
    'Mohammed', 'Neel', 'Nikhil', 'Parth', 'Pranav', 'Rahul', 'Raj', 'Reyansh', 'Rohan', 'Ronan', 'Rudra',
    'Sai', 'Samar', 'Shaurya', 'Siddharth', 'Veer', 'Vihaan', 'Vivaan', 'Yash'
]
ALL_USERS = FEMALE_NAMES + MALE_NAMES

# App profiles now include realistic duration ranges and legacy status
APP_PROFILES = {
    'VSCode':    {'versions': ['1.72.0', '1.74.2'], 'min_duration': 1800, 'max_duration': 14400, 'legacy': False},
    'Photoshop': {'versions': ['23.5', '24.0'],    'min_duration': 1200, 'max_duration': 10800, 'legacy': False},
    'Figma':     {'versions': ['116.2.4', '116.3.0'],'min_duration': 1200, 'max_duration': 10800, 'legacy': False},
    'Chrome':    {'versions': ['108.0', '109.0'],   'min_duration': 300,  'max_duration': 5400,  'legacy': False},
    'Slack':     {'versions': ['4.29.144', '4.30.0'],'min_duration': 60,   'max_duration': 3600,  'legacy': False},
    'Excel':     {'versions': ['2208', '2210'],      'min_duration': 600,  'max_duration': 7200,  'legacy': False},
    'Zoom':      {'versions': ['5.12.0', '5.13.5'],  'min_duration': 900,  'max_duration': 4500,  'legacy': False},
    'Tableau':   {'versions': ['2022.3', '2022.4'],  'min_duration': 900,  'max_duration': 9000,  'legacy': False},
    'AutoCAD':   {'versions': ['2022', '2023.1'],    'min_duration': 2400, 'max_duration': 18000, 'legacy': True},
    'Blender':   {'versions': ['3.3', '3.4'],       'min_duration': 2400, 'max_duration': 18000, 'legacy': False}
}
APP_NAMES = list(APP_PROFILES.keys())

MONITOR_VERSIONS = ['1.2.0', '1.3.0', '1.3.1']

# --- 3. PERSONA-BASED BEHAVIOR MODELING ---

# --- 3. PERSONA-BASED BEHAVIOR MODELING ---

PERSONAS = {
    'Developer': {
        # Weights for [VSCode, Photoshop, Figma, Chrome, Slack, Excel, Zoom, Tableau, AutoCAD, Blender]
        'app_weights':   [30, 1, 5, 20, 15, 5, 5, 1, 1, 2],
        'platform_weights': [60, 20, 20] # Weights for [Windows, macOS, Linux]
    },
    'Designer': {
        'app_weights':   [5, 30, 30, 10, 5, 1, 2, 2, 1, 15],
        'platform_weights': [30, 65, 5]
    },
    'Manager': {
        # THE FIX IS ON THE NEXT LINE: Added a final '1' to make the list 10 items long.
        'app_weights':   [1, 1, 1, 25, 25, 25, 15, 5, 1, 1],
        'platform_weights': [50, 50, 0]
    },
    'Data Analyst': {
        'app_weights':   [5, 1, 1, 15, 10, 30, 5, 30, 1, 2],
        'platform_weights': [70, 30, 0]
    }
}

def create_user_profiles():
    """Assigns a persona and a random activity level to each user."""
    print("Creating realistic user profiles...")
    profiles = {}
    persona_list = list(PERSONAS.keys())
    for user in ALL_USERS:
        profiles[user] = {
            'persona': random.choice(persona_list),
            'daily_activity_chance': random.uniform(0.65, 0.95) # How likely they are to be active on any given day
        }
    return profiles

# --- 4. DATABASE OPERATIONS ---

def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    return sqlite3.connect(db_file)

def clear_existing_data(conn):
    """Deletes all records from the usage_data table and resets the counter."""
    print("Clearing existing data from the database...")
    cur = conn.cursor()
    cur.execute('DELETE FROM usage_data')
    cur.execute('DELETE FROM sqlite_sequence WHERE name="usage_data"')
    conn.commit()
    print("Database cleared.")

def generate_and_insert_data(conn):
    """Generate and insert realistic test data."""
    
    # Step 1: Create our user behavior models
    user_profiles = create_user_profiles()
    inactive_users = set(random.sample(ALL_USERS, NUM_INACTIVE_USERS))
    print(f"Designated {len(inactive_users)} users to be inactive for the last 30 days.")
    
    print("\nStarting data generation (this may take a moment)...")
    cursor = conn.cursor()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=HISTORY_DAYS)
    thirty_days_ago = end_date - timedelta(days=30)
    
    records_to_insert = []
    total_records = 0
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() >= 5: # Skip weekends
            current_date += timedelta(days=1)
            continue
            
        for user in ALL_USERS:
            # RULE: Skip if user is designated as inactive and the date is within the last 30 days
            if user in inactive_users and current_date > thirty_days_ago:
                continue

            # RULE: Each user has a chance to be inactive on any given day
            profile = user_profiles[user]
            if random.random() > profile['daily_activity_chance']:
                continue

            # User is active today, let's generate a record based on their persona
            persona_data = PERSONAS[profile['persona']]
            
            # Choose app and platform based on weighted probabilities
            app_name = random.choices(APP_NAMES, weights=persona_data['app_weights'], k=1)[0]
            platform = random.choices(['Windows', 'macOS', 'Linux'], weights=persona_data['platform_weights'], k=1)[0]
            
            # Get app-specific details
            app_profile = APP_PROFILES[app_name]
            app_version = random.choice(app_profile['versions'])
            duration = random.randint(app_profile['min_duration'], app_profile['max_duration'])
            
            # Generate a random timestamp within work hours (9 AM to 6 PM UTC)
            log_time = datetime(
                current_date.year, current_date.month, current_date.day,
                random.randint(9, 17), random.randint(0, 59), random.randint(0, 59)
            )
            
            record = (
                random.choice(MONITOR_VERSIONS),
                platform,
                user,
                app_name,
                app_version,
                log_time.isoformat() + "Z", # ISO 8601 format
                app_profile['legacy'],
                duration
            )
            records_to_insert.append(record)

        # Batch insert for efficiency
        if len(records_to_insert) > 1000:
            sql = """INSERT INTO usage_data (monitor_app_version, platform, user, application_name, 
                     application_version, log_date, legacy_app, duration_seconds) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            cursor.executemany(sql, records_to_insert)
            conn.commit()
            total_records += len(records_to_insert)
            print(f"  ... inserted {total_records} records so far.")
            records_to_insert = []
            
        current_date += timedelta(days=1)

    # Insert any remaining records
    if records_to_insert:
        sql = """INSERT INTO usage_data (monitor_app_version, platform, user, application_name, 
                 application_version, log_date, legacy_app, duration_seconds) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor.executemany(sql, records_to_insert)
        conn.commit()
        total_records += len(records_to_insert)

    print("\n---------------------------------")
    print("Data generation complete.")
    print(f"Total realistic records inserted: {total_records}")
    print("---------------------------------")


def main():
    """Main function to orchestrate database population."""
    conn = create_connection(DATABASE_FILE)
    if conn:
        clear_existing_data(conn)
        generate_and_insert_data(conn)
        conn.close()
        print("Database connection closed.")
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()