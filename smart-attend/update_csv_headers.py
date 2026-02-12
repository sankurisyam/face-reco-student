import os
import pandas as pd

attendance_folder = "Attendance_Records"
header = ['RollNo', 'Name', 'Branch', 'Period1', 'Period2', 'Period3', 'Period4', 'Period5', 'Period6', 'Date']
branches = ['CSE', 'AIML', 'CSD', 'CAI', 'CSM']

for branch in branches:
    csv_file = os.path.join(attendance_folder, f"Attendance_{branch}.csv")
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        before = len(df)
        # Remove duplicates for the same RollNo and Date, keeping the first occurrence
        df = df.drop_duplicates(subset=['RollNo', 'Date'], keep='first')
        after = len(df)
        # Reorder or add missing columns
        for col in header:
            if col not in df.columns:
                df[col] = ''
        df = df[header]
        df.to_csv(csv_file, index=False)
        print(f"{csv_file}: {before} rows -> {after} rows (duplicates removed)")
    else:
        print(f"{csv_file} not found.")