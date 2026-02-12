"""
Remove students from CSV attendance files if they don't have images in Images_Attendance folder
"""

import os
import pandas as pd

# Configuration
images_path = 'Images_Attendance'
attendance_folder = 'Attendance_Records'
branches_list = ['AIML', 'CSE', 'CSD', 'CAI', 'CSM']

def get_students_with_images():
    """Get set of (RollNo, Branch) tuples for students that have images"""
    students_with_images = set()
    
    if not os.path.exists(images_path):
        print(f"ERROR: {images_path} folder not found!")
        return students_with_images
    
    for branch in branches_list:
        branch_path = os.path.join(images_path, branch)
        if os.path.exists(branch_path):
            for filename in os.listdir(branch_path):
                if filename.endswith(('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')):
                    # Extract RollNo from filename: RollNo_Name_Branch.jpg
                    parts = os.path.splitext(filename)[0].split('_')
                    if len(parts) >= 3:
                        rollno = parts[0]
                        students_with_images.add((rollno, branch))
                        
    return students_with_images

def clean_csv_files(students_with_images):
    """Remove rows from CSV files for students without images"""
    
    if not os.path.exists(attendance_folder):
        print(f"ERROR: {attendance_folder} folder not found!")
        return
    
    total_removed = 0
    
    for branch in branches_list:
        csv_file = os.path.join(attendance_folder, f'Attendance_{branch}.csv')
        
        if not os.path.exists(csv_file):
            print(f"⏭️  {csv_file} not found, skipping...")
            continue
        
        # Read CSV
        df = pd.read_csv(csv_file)
        original_rows = len(df)
        
        # Filter: keep only students who have images
        df_filtered = df[df.apply(
            lambda row: (str(row['RollNo']).strip(), str(row['Branch']).strip()) in students_with_images,
            axis=1
        )]
        
        removed_rows = original_rows - len(df_filtered)
        
        if removed_rows > 0:
            # Backup original file
            backup_file = csv_file + '.backup'
            df.to_csv(backup_file, index=False)
            print(f"✅ {branch}: Removed {removed_rows} rows (kept {len(df_filtered)} rows)")
            print(f"   📦 Backup saved to: {backup_file}")
            
            # Save cleaned CSV
            df_filtered.to_csv(csv_file, index=False)
        else:
            print(f"✅ {branch}: No changes needed (all {len(df_filtered)} students have images)")
    
    print(f"\n✨ Cleanup complete!")

if __name__ == "__main__":
    print("=" * 80)
    print("CLEANING CSV ATTENDANCE FILES")
    print("=" * 80)
    print()
    
    # Step 1: Get students with images
    print("📁 Scanning Images_Attendance folder...")
    students_with_images = get_students_with_images()
    print(f"✓ Found {len(students_with_images)} students with images")
    print()
    
    # Step 2: Clean CSV files
    print("🧹 Cleaning CSV files...")
    print()
    clean_csv_files(students_with_images)
    print()
    print("=" * 80)
