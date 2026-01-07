import re

def remove_last_column_and_bold():
    file_path = 'analysis_mdfiles/30min_opening_patterns_analysis.md'
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    new_lines = []
    in_q3_table = False
    
    for line in lines:
        # Remove bold markers globally
        clean_line = line.replace('**', '')
        
        # Check if we are in Question 3 section
        if "Question 3:" in clean_line:
            in_q3_table = True # Entering Q3 section, but tables start later
            
        # Specific logic for Question 3 tables
        # The tables have header | Pattern ... | ... | Win Rate |
        if in_q3_table and "|" in clean_line:
            # Check if it's the specific table we want to modify
            if "Win Rate" in clean_line and "Pattern" in clean_line:
                # Header row: Remove last column
                parts = clean_line.split('|')
                # Expected: ['', ' Pattern...', ' Occurrences ', ' Day Closes BULL ', ' Day Closes BEAR ', ' Win Rate ', '\n']
                # Remove the second to last element (' Win Rate ')
                if len(parts) >= 3:
                     # Reconstruct excluding the last data column
                     # parts[0] is empty string before first |
                     # parts[-1] is newline after last |
                     # parts[-2] is the column to remove
                     new_parts = parts[:-2] + parts[-1:]
                     clean_line = "|".join(new_parts)
            elif ":-" in clean_line and "-:": # Alignment row
                 # Detect by checking length or content
                 parts = clean_line.split('|')
                 if len(parts) >= 6: # standard 5 col table has 7 parts split by |
                     new_parts = parts[:-2] + parts[-1:]
                     clean_line = "|".join(new_parts)
            else:
                 # Data row
                 parts = clean_line.split('|')
                 if len(parts) >= 6: 
                     # Check if the last column looks like percentage or win rate data
                     # But safer to just remove last column for all rows in this section if they match column count
                     new_parts = parts[:-2] + parts[-1:]
                     clean_line = "|".join(new_parts)

        new_lines.append(clean_line)

    with open(file_path, 'w') as f:
        f.writelines(new_lines)

    print("Successfully processed file.")

if __name__ == "__main__":
    remove_last_column_and_bold()
