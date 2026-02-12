"""
Remove duplicate attendance records from CSV files
Duplicates are identified by: RollNo, Date, and Period columns
"""

import os
import pandas as pd

# Configuration
attendance_folder = 'Attendance_Records'
branches_list = ['AIML', 'CSE', 'CSD', 'CAI', 'CSM']

def remove_duplicates_from_csv():
    """Remove duplicate rows from CSV attendance files"""
    
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

        if original_rows == 0:
            print(f"✅ {branch}: No duplicates found (0 rows)")
            continue

        # First remove exact duplicate rows (all columns identical)
        df_noexact = df.drop_duplicates()

        # Deduplicate by RollNo + Date: merge rows so that any 'Present'-like value wins for each period
        # Detect period columns (Period1..Period6 or any column starting with 'Period')
        period_cols = [c for c in df_noexact.columns if c.lower().startswith('period')]

        def reduce_periods(series):
            # If any value in the group indicates presence, return 'Present', else 'Absent' (preserves common labels)
            vals = series.dropna().astype(str).str.strip().str.lower()
            for v in vals:
                if v.startswith('pres') or v.startswith('p') or v in ('1', 'true', 'yes'):
                    return 'Present'
            return 'Absent'

        agg_dict = {'Name': 'first', 'Branch': 'first'}
        for p in period_cols:
            agg_dict[p] = reduce_periods

        # Some CSVs may have additional columns; keep them by taking first occurrence
        other_cols = [c for c in df_noexact.columns if c not in (['RollNo', 'Date'] + list(agg_dict.keys()))]
        for c in other_cols:
            agg_dict[c] = 'first'

        grouped = df_noexact.groupby(['RollNo', 'Date'], dropna=False).agg(agg_dict).reset_index()

        removed_rows = original_rows - len(grouped)

        if removed_rows > 0:
            # Backup original file
            backup_file = csv_file + '.backup_duplicates'
            df.to_csv(backup_file, index=False)
            print(f"✅ {branch}: Removed {removed_rows} duplicate RollNo+Date entries (kept {len(grouped)} rows)")
            print(f"   📦 Backup saved to: {backup_file}")

            # Reorder columns: RollNo, Name, Branch, Periods..., Date, others
            header = ['RollNo']
            if 'Name' in grouped.columns:
                header.append('Name')
            if 'Branch' in grouped.columns:
                header.append('Branch')
            header += period_cols
            if 'Date' in grouped.columns:
                header.append('Date')
            # append any other columns present
            for c in grouped.columns:
                if c not in header:
                    header.append(c)

            # Ensure all header columns exist
            header = [c for c in header if c in grouped.columns]

            grouped = grouped[header]
            grouped.to_csv(csv_file, index=False)
        else:
            print(f"✅ {branch}: No duplicates found ({len(grouped)} rows)")


def reconcile_aiml_names_with_images(images_path='Images_Attendance'):
    """For AIML: if same RollNo has different Names in CSV, keep only rows whose Name has an image file.

    Image filenames are expected in the format: <RollNo>_<Name>_<Branch>.<ext>
    This function looks inside `Images_Attendance/AIML/` and keeps rows whose Name matches
    an image entry for the same RollNo. If none of the names for a roll have images, no rows
    are removed for that roll and a warning is printed.
    """
    aiml_csv = os.path.join(attendance_folder, 'Attendance_AIML.csv')
    aiml_images_dir = os.path.join(images_path, 'AIML')

    if not os.path.exists(aiml_csv):
        print(f"ℹ️  {aiml_csv} not found — skipping AIML name reconciliation.")
        return

    if not os.path.exists(aiml_images_dir):
        print(f"ℹ️  {aiml_images_dir} not found — cannot verify images for AIML.")
        return

    df = pd.read_csv(aiml_csv)
    original_rows = len(df)

    # Build index of images by roll -> set(names)
    from collections import defaultdict
    images_by_roll = defaultdict(set)
    for root, dirs, files in os.walk(aiml_images_dir):
        for fn in files:
            base, _ = os.path.splitext(fn)
            parts = base.split('_')
            if len(parts) >= 3:
                r, n, b = parts[0], parts[1], parts[2]
                if r and n:
                    images_by_roll[r].add(n.strip().upper())

    # Find roll numbers with multiple distinct names
    rolls = df.groupby('RollNo')
    rows_to_keep = []
    removed_count = 0
    for roll, group in rolls:
        names = set(group['Name'].astype(str).str.strip())
        if len(names) <= 1:
            # Nothing to do — keep all
            rows_to_keep.extend(group.index.tolist())
            continue

        # Determine which names have images
        names_with_images = set()
        for name in names:
            if name.strip().upper() in images_by_roll.get(roll, set()):
                names_with_images.add(name)

        if len(names_with_images) == 0:
            print(f"⚠️  RollNo {roll} has multiple names {sorted(names)} but no matching images found; leaving unchanged.")
            rows_to_keep.extend(group.index.tolist())
        else:
            # Keep only rows with names that have images
            keep_mask = group['Name'].astype(str).str.strip().isin(names_with_images)
            kept = group[keep_mask].index.tolist()
            removed = group[~keep_mask].index.tolist()
            rows_to_keep.extend(kept)
            removed_count += len(removed)
            if removed:
                print(f"🗑️  RollNo {roll}: removed rows for names {sorted(set(group.loc[removed,'Name'].astype(str).str.strip()))}")

    if removed_count > 0:
        backup_file = aiml_csv + '.backup_name_mismatch'
        df.to_csv(backup_file, index=False)
        new_df = df.loc[sorted(rows_to_keep)].reset_index(drop=True)
        new_df.to_csv(aiml_csv, index=False)
        print(f"✅ AIML: Removed {removed_count} rows with name mismatch; backup saved to {backup_file}")
    else:
        print("✅ AIML: No name-image mismatches found.")
    
    print(f"\n✨ Deduplication complete!")

if __name__ == "__main__":
    print("=" * 80)
    print("REMOVING DUPLICATE ATTENDANCE RECORDS")
    print("=" * 80)
    print()
    
    print("🧹 Processing CSV files...")
    print()
    remove_duplicates_from_csv()
    print()
    # Also reconcile AIML names with images (remove CSV rows where name has no image)
    print("🔎 Reconciling AIML names with image files...")
    reconcile_aiml_names_with_images()
    print()
    print("=" * 80)
