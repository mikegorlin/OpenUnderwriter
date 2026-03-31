#!/usr/bin/env python3
"""Create visual comparison chart for Phase II vs Phase III failure impact."""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

# Data for the chart
phases = ['Phase II Failure', 'Phase III Failure']

# Metrics
failure_rate = [71, 42]  # % of trials that fail at this stage
stock_drop = [55, 75]    # Typical % stock drop (midpoint of ranges)
market_cap_risk = [25, 85] # Relative index of market cap at risk (Phase III is much higher)
settlement_severity = [30, 80] # Relative index of settlement severity

x = np.arange(len(phases))
width = 0.2

fig, ax = plt.subplots(figsize=(10, 6))

rects1 = ax.bar(x - width*1.5, failure_rate, width, label='Clinical Failure Rate (%)', color='#757575')
rects2 = ax.bar(x - width*0.5, stock_drop, width, label='Typical Stock Drop (%)', color='#D32F2F')
rects3 = ax.bar(x + width*0.5, market_cap_risk, width, label='Relative Market Cap at Risk', color='#1976D2')
rects4 = ax.bar(x + width*1.5, settlement_severity, width, label='Relative D&O Severity Risk', color='#388E3C')

ax.set_ylabel('Percentage / Relative Index (0-100)', fontsize=11)
ax.set_title('The D&O Underwriting Reality: Phase II vs. Phase III Failures', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(phases, fontsize=12, fontweight='bold')
ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
ax.set_ylim(0, 105)

# Add value labels
def autolabel(rects, suffix=''):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height}{suffix}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

autolabel(rects1, '%')
autolabel(rects2, '%')

plt.tight_layout()
plt.savefig('/home/ubuntu/output/phase_comparison_chart.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Chart saved.")
