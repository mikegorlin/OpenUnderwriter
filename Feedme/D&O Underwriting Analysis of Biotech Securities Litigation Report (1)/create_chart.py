#!/usr/bin/env python3
"""Create visual breakdown charts for the Swiss Re document analysis."""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

# --- Chart 1: Page allocation by category ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Pie chart
categories = ['Filler/Dividers\n(8 pages)', 'Basic Knowledge\n(7 pages)', 
              'Mixed: Shallow\nUnderwriting Points\n(5 pages)', 'Genuine D&O\nInsight\n(2 pages)']
sizes = [8, 7, 5, 2]
colors = ['#D32F2F', '#FF9800', '#FFC107', '#2E7D32']
explode = (0, 0, 0, 0.1)

wedges, texts, autotexts = axes[0].pie(sizes, explode=explode, labels=categories, 
    autopct='%1.0f%%', colors=colors, startangle=90,
    textprops={'fontsize': 9}, pctdistance=0.75)
for autotext in autotexts:
    autotext.set_fontsize(11)
    autotext.set_fontweight('bold')
axes[0].set_title('Swiss Re BioTech Presentation\nPage Allocation by Content Type', 
                   fontsize=13, fontweight='bold', pad=20)

# Stacked bar chart - content vs what's needed
categories_bar = ['Swiss Re\nDocument', 'What an Underwriter\nActually Needs']
filler = [36, 0]
basic = [32, 0]
shallow_uw = [23, 10]
deep_uw = [9, 40]
claims_data = [0, 25]
legal_framework = [0, 25]

bar_width = 0.5
x = np.arange(len(categories_bar))

p1 = axes[1].bar(x, filler, bar_width, label='Filler/Dividers', color='#D32F2F')
p2 = axes[1].bar(x, basic, bar_width, bottom=filler, label='Basic Knowledge', color='#FF9800')
p3 = axes[1].bar(x, shallow_uw, bar_width, bottom=[f+b for f,b in zip(filler,basic)], 
                  label='Shallow Underwriting Points', color='#FFC107')
p4 = axes[1].bar(x, deep_uw, bar_width, bottom=[f+b+s for f,b,s in zip(filler,basic,shallow_uw)], 
                  label='Deep D&O Underwriting Insight', color='#2E7D32')
p5 = axes[1].bar(x, claims_data, bar_width, 
                  bottom=[f+b+s+d for f,b,s,d in zip(filler,basic,shallow_uw,deep_uw)], 
                  label='Empirical Claims/Litigation Data', color='#1565C0')
p6 = axes[1].bar(x, legal_framework, bar_width, 
                  bottom=[f+b+s+d+c for f,b,s,d,c in zip(filler,basic,shallow_uw,deep_uw,claims_data)], 
                  label='Legal Framework (PSLRA/Omnicare)', color='#6A1B9A')

axes[1].set_ylabel('% of Content', fontsize=11)
axes[1].set_title('Content Composition:\nSwiss Re vs. What Underwriters Need', 
                   fontsize=13, fontweight='bold', pad=20)
axes[1].set_xticks(x)
axes[1].set_xticklabels(categories_bar, fontsize=10)
axes[1].set_ylim(0, 105)
axes[1].legend(loc='upper right', fontsize=7, framealpha=0.9)

plt.tight_layout(pad=3)
plt.savefig('/home/ubuntu/output/content_breakdown_chart.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Chart 1 saved.")

# --- Chart 2: What's Missing visual ---
fig2, ax = plt.subplots(figsize=(12, 7))

missing_items = [
    'Dismissal rate data (68% for dev-stage biotech)',
    'Omnicare v. Laborers (2015) - opinion protection',
    'PSLRA safe harbor for forward-looking statements',
    'Phase-specific litigation frequency & severity',
    'Therapeutic area risk differentiation',
    'FDA communication characterization risk',
    'Commercialization transition risk (43% of claims)',
    'Insider trading / 10b5-1 plan analysis',
    'Section 11 / IPO / SPAC offering risk',
    'Settlement range data by company size',
    'Form 483 / CRL disclosure obligations',
    'Gene therapy / device-specific risk profiles',
    'Scienter analysis framework',
    'Technology valuation vs. litigation exposure link',
    'Plaintiff law firm concentration data'
]

severity = [10, 10, 9, 9, 8, 10, 9, 7, 8, 8, 7, 7, 9, 6, 5]

# Sort by severity
sorted_pairs = sorted(zip(severity, missing_items), reverse=True)
severity_sorted = [s for s, _ in sorted_pairs]
items_sorted = [i for _, i in sorted_pairs]

colors_bar = ['#B71C1C' if s >= 9 else '#E65100' if s >= 7 else '#F9A825' for s in severity_sorted]

bars = ax.barh(range(len(items_sorted)), severity_sorted, color=colors_bar, edgecolor='white', height=0.7)
ax.set_yticks(range(len(items_sorted)))
ax.set_yticklabels(items_sorted, fontsize=9)
ax.set_xlabel('Underwriting Impact (1-10)', fontsize=11)
ax.set_title('Critical Omissions from Swiss Re Document\nRanked by Underwriting Impact', 
             fontsize=14, fontweight='bold', pad=15)
ax.set_xlim(0, 11)
ax.invert_yaxis()

# Add severity labels
for bar, val in zip(bars, severity_sorted):
    ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height()/2, 
            str(val), va='center', fontsize=9, fontweight='bold')

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#B71C1C', label='Critical (9-10)'),
                   Patch(facecolor='#E65100', label='High (7-8)'),
                   Patch(facecolor='#F9A825', label='Moderate (5-6)')]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig('/home/ubuntu/output/missing_items_chart.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Chart 2 saved.")
print("All charts complete.")
