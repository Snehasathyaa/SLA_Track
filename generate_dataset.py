
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# --- Config ---
N = 3000

CATEGORIES = ['Housing', 'Education', 'Healthcare', 'Sanitation',
              'Revenue', 'Public Works', 'Social Security', 'Water Supply']

DEPARTMENTS = {
    'Housing': 'Housing Board',
    'Education': 'Education Department',
    'Healthcare': 'Health Department',
    'Sanitation': 'Municipality',
    'Revenue': 'Revenue Department',
    'Public Works': 'PWD',
    'Social Security': 'Social Welfare',
    'Water Supply': 'Kerala Water Authority'
}

PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
PRIORITY_WEIGHTS = [0.30, 0.40, 0.20, 0.10]

DISTRICTS = [
    'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha',
    'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad',
    'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod'
]

# SLA threshold in days by priority
SLA_THRESHOLD = {'Low': 15, 'Medium': 10, 'High': 5, 'Critical': 2}

# Category complexity multiplier (higher = takes longer)
CATEGORY_MULTIPLIER = {
    'Housing': 1.4, 'Education': 1.0, 'Healthcare': 0.85,
    'Sanitation': 0.9, 'Revenue': 1.2, 'Public Works': 1.5,
    'Social Security': 1.1, 'Water Supply': 0.9
}

STATUSES = ['Resolved', 'Pending', 'In Progress', 'Escalated', 'Closed']


def generate_dataset():
    records = []
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)

    for i in range(N):
        category = random.choice(CATEGORIES)
        priority = np.random.choice(PRIORITIES, p=PRIORITY_WEIGHTS)
        district = random.choice(DISTRICTS)
        department = DEPARTMENTS[category]

        # Submission date
        delta_days = (end_date - start_date).days
        submission_date = start_date + timedelta(days=random.randint(0, delta_days))
        day_of_week = submission_date.weekday()  # 0=Mon, 6=Sun

        sla_threshold = SLA_THRESHOLD[priority]
        multiplier = CATEGORY_MULTIPLIER[category]

        # Officer experience (1-20 years), affects resolution speed
        officer_experience = random.randint(1, 20)
        # Workload at time of submission (pending cases)
        workload = random.randint(5, 80)        
        # Is it a resubmission?
        resubmission = np.random.choice([0, 1], p=[0.80, 0.20])
        # Complaint text length proxy
        complaint_length = random.randint(50, 800)
        # Urban vs Rural
        urban = np.random.choice([0, 1], p=[0.45, 0.55])

        # --- Resolution days simulation ---
        base_days = sla_threshold * multiplier
        experience_factor = 1 - (officer_experience / 40)  # more experience = faster
        workload_factor = 1 + (workload / 100)  # more workload = slower
        noise = np.random.normal(0, 2)

        resolution_days = max(1, int(base_days * workload_factor * experience_factor
                                      + (1.5 if resubmission else 0) + noise
                                      + (1 if day_of_week >= 5 else 0)))  # weekend penalty

        sla_violated = int(resolution_days > sla_threshold)
        escalated = int(sla_violated and random.random() > 0.35)

        # Status logic
        days_since = (datetime(2025, 1, 1) - submission_date).days
        if resolution_days <= days_since:
            if escalated:
                status = 'Closed'
            else:
                status = 'Resolved'
        else:
            if escalated:
                status = 'Escalated'
            elif days_since > 0:
                status = 'In Progress'
            else:
                status = 'Pending'

        # Risk score (0-100)
        risk_score = min(100, int(
            (workload / 80) * 30 +
            (1 - officer_experience / 20) * 25 +
            (multiplier - 0.8) / 0.7 * 25 +
            (resubmission * 10) +
            (10 if priority == 'Critical' else 5 if priority == 'High' else 2)
        ))

        records.append({
            'complaint_id': f'KL{2022 + i // 1000}-{str(i+1).zfill(5)}',
            'category': category,
            'department': department,
            'priority': priority,
            'district': district,
            'urban': urban,
            'submission_date': submission_date.strftime('%Y-%m-%d'),
            'day_of_week': day_of_week,
            'officer_experience': officer_experience,
            'workload_at_submission': workload,
            'complaint_length': complaint_length,
            'resubmission': resubmission,
            'sla_threshold_days': sla_threshold,
            'resolution_days': resolution_days,
            'sla_violated': sla_violated,
            'escalated': escalated,
            'status': status,
            'risk_score': risk_score
        })

    df = pd.DataFrame(records)
    df.to_csv('dataset/grievance_dataset.csv', index=False)
    print(f"Dataset generated: {N} records")
    print(df.head())
    print("\nSLA Violation Rate:", df['sla_violated'].mean().round(3))
    print("Escalation Rate:", df['escalated'].mean().round(3))
    print("\nClass Distribution:")
    print(df['sla_violated'].value_counts())
    return df


if __name__ == '__main__':
    import os
    os.makedirs('dataset', exist_ok=True)
    df = generate_dataset()
    print("\nDataset saved to dataset/grievance_dataset.csv")