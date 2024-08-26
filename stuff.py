import re

# Step 1: Define your regex patterns with descriptive keys
patterns = {
    'pattern_1': r'regex_pattern_1',
    'pattern_2': r'regex_pattern_2',
    # Add all 18 patterns here...
    'pattern_18': r'regex_pattern_18'
}

# Step 2: Initialize a dictionary to store the matches
matches = {key: None for key in patterns.keys()}

# Step 3: Read the file and find the patterns
with open('yourfile.txt', 'r') as file:
    for line in file:
        for key, pattern in patterns.items():
            if matches[key] is None:  # Only search if this pattern hasn't been matched yet
                match = re.search(pattern, line)
                if match:
                    matches[key] = match.group(0)
        
        # Step 4: Stop if all patterns have been found
        if all(matches.values()):
            break

# Matches dictionary now contains the first occurrence of each pattern
print(matches)
