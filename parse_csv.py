import csv
import json
import re
import sys

csv.field_size_limit(2147483647)

input_file = r"d:\finance product\frontend\public\leads\leads - Sheet1.csv"
output_file = r"d:\finance product\cleaned_leads.json"

leads = []

try:
    with open(input_file, encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        for row in reader:
            if not row or len(row) == 0:
                continue
                
            full_text = row[0]
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            if not lines:
                continue
                
            name = lines[0]
            if name == "Lists (1)":
                continue
                
            designation = ""
            about = ""
            for i, line in enumerate(lines):
                if line == "First time view" or line == "Viewed you":
                    designation = lines[i+1] if i+1 < len(lines) else "Unknown"
                if line == "About" and i + 1 < len(lines) and lines[i+1] != "Relationship" and "Welcome to" not in lines[i+1]:
                    about = lines[i+1]
                    
            if not designation:
                designation = lines[3] if len(lines) > 3 else "Unknown"
            
            leads.append({
                "Name": name,
                "Designation": designation,
                "About": about[:150] # Just the first 150 chars to get context
            })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=4)
        
    print(f"Successfully processed {len(leads)} leads.")
except Exception as e:
    print(f"Error: {e}")
