import pandas as pd
csv='Attendance_Records/Attendance_AIML.csv'
df=pd.read_csv(csv)
roll='22FE1A6101'
sub=df[df['RollNo']==roll]
print('rows:', len(sub))
print('dates:', sorted(sub['Date'].unique()))
print(sub.head())
