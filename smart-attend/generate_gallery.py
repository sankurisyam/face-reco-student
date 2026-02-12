import os
import pandas as pd

# Configuration
IMAGES_DIR = 'Images_Attendance'
ATTENDANCE_DIR = 'Attendance_Records'
BRANCHES = ['AIML', 'CSE', 'CSD', 'CAI', 'CSM']
OUTPUT = 'student_gallery.html'

# Build image index: (rollno, branch) -> filename
image_index = {}
for branch in BRANCHES:
    branch_path = os.path.join(IMAGES_DIR, branch)
    if not os.path.exists(branch_path):
        continue
    for fname in sorted(os.listdir(branch_path)):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            # prefer files that start with rollno
            parts = os.path.splitext(fname)[0].split('_')
            if len(parts) >= 1:
                rollno = parts[0]
                key = (rollno, branch)
                image_index[key] = os.path.join(branch_path, fname)

# Collect students from CSVs
students = []  # list of dicts
for branch in BRANCHES:
    csv_file = os.path.join(ATTENDANCE_DIR, f'Attendance_{branch}.csv')
    if not os.path.exists(csv_file):
        continue
    try:
        df = pd.read_csv(csv_file, dtype=str)
    except Exception:
        # fallback: skip
        continue
    # use unique combinations
    uniq = df[['RollNo', 'Name', 'Branch']].drop_duplicates()
    for _, r in uniq.iterrows():
        rollno = str(r['RollNo']).strip()
        name = str(r['Name']).strip()
        branch_name = str(r['Branch']).strip()
        key = (rollno, branch_name)
        img = image_index.get(key)
        # if not found by exact key, try to find any file in branch starting with rollno
        if not img:
            branch_path = os.path.join(IMAGES_DIR, branch_name)
            if os.path.exists(branch_path):
                for fname in os.listdir(branch_path):
                    if fname.lower().endswith(('.jpg', '.jpeg', '.png')) and fname.startswith(rollno):
                        img = os.path.join(branch_path, fname)
                        break
        students.append({'rollno': rollno, 'name': name, 'branch': branch_name, 'image': img})

# Build HTML
html_lines = []
html_lines.append('<!doctype html>')
html_lines.append('<html><head><meta charset="utf-8"><title>Student Gallery</title>')
html_lines.append('<style>body{font-family:Arial,Helvetica,sans-serif} .student{display:flex;align-items:center;margin:8px;padding:8px;border-bottom:1px solid #ddd} .thumb{width:160px;height:160px;display:flex;align-items:center;justify-content:center;border:1px solid #ccc;margin-right:12px;background:#f8f8f8} img{max-width:100%;max-height:100%} .info{min-width:360px}</style>')
html_lines.append('</head><body>')
html_lines.append('<h1>Student Image Gallery</h1>')
html_lines.append('<p>Generated from CSVs in <code>Attendance_Records</code> and images in <code>Images_Attendance</code>.</p>')

count_with = 0
count_total = len(students)

# Group by branch
from collections import defaultdict
by_branch = defaultdict(list)
for s in students:
    by_branch[s['branch']].append(s)

for branch in BRANCHES:
    html_lines.append(f'<h2>Branch: {branch} (count: {len(by_branch.get(branch,[]))})</h2>')
    for s in by_branch.get(branch,[]):
        html_lines.append('<div class="student">')
        if s['image'] and os.path.exists(s['image']):
            # use relative path
            rel = s['image'].replace('\\', '/')
            html_lines.append(f'<div class="thumb"><img src="{rel}" alt="{s["rollno"]}"></div>')
            count_with += 1
        else:
            html_lines.append('<div class="thumb">No image</div>')
        html_lines.append('<div class="info"><b>RollNo:</b> ' + s['rollno'] + '<br><b>Name:</b> ' + s['name'] + '<br><b>Branch:</b> ' + s['branch'] + '</div>')
        html_lines.append('</div>')

html_lines.append('<hr>')
html_lines.append(f'<p>Total students: {count_total} &nbsp; | &nbsp; With images: {count_with} &nbsp; | &nbsp; Missing images: {count_total - count_with}</p>')
html_lines.append('</body></html>')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(html_lines))

print('Gallery generated:', os.path.abspath(OUTPUT))
print('Total students:', count_total, 'With images:', count_with, 'Missing:', count_total - count_with)
print('Open the generated file in your browser to view the gallery.')
