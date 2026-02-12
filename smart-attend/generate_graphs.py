import json
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).parent
data = json.load(open(ROOT / 'analysis.json'))

# Feature coverage chart
features = list(data['project']['features_detected'].keys())
values = [1 if data['project']['features_detected'][f] else 0 for f in features]

plt.figure(figsize=(10,5))
plt.barh(features, values, color=['#2ca02c' if v==1 else '#d62728' for v in values])
plt.xlim(-0.1,1.1)
plt.xlabel('Implemented (1) / Not implemented (0)')
plt.title('Paper Feature Coverage by Project')
for i,v in enumerate(values):
    plt.text(v+0.02, i, str(v), va='center')
plt.tight_layout()
plt.savefig(ROOT / 'feature_coverage.png')
plt.close()

# Module counts chart
mc = data['project']['module_counts']
labels = list(mc.keys())
counts = [mc[k] for k in labels]

plt.figure(figsize=(8,5))
plt.bar(labels, counts, color='#1f77b4')
plt.ylabel('File count (approx)')
plt.title('Project Module File Counts')
plt.xticks(rotation=30, ha='right')
for i,c in enumerate(counts):
    plt.text(i, c+0.1, str(c), ha='center')
plt.tight_layout()
plt.savefig(ROOT / 'module_counts.png')
plt.close()

print('Generated feature_coverage.png and module_counts.png')
