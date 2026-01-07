import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# Configuration
DIRECTORIES = ["../../output/trend_patterns/bull", "../../output/trend_patterns/bear"]

def process_file(file_path):
    print(f"Processing {file_path}...")
    
    try:
        # Read CSV but skip the last row (count row)
        df = pd.read_csv(file_path)
        
        if df.empty:
            print("  Skipping empty file.")
            return

        # Remove the footer row if it exists
        if df.iloc[-1, 0] == 'total_days':
            df = df[:-1]
            
        # Convert columns to numeric
        cols_to_convert = ['bar_index', 'prob_high_set_exact']
        for col in cols_to_convert:
            df[col] = pd.to_numeric(df[col])

        # Calculate Probability Mass Function (PMF)
        # Difference between cumulative probability = probability at that specific bar
        df['high_formed_prob'] = df['prob_high_set_exact'].diff().fillna(df['prob_high_set_exact'])
        df['high_formed_pct'] = df['high_formed_prob'] * 100

        # Aggregate into 30-minute buckets (6 bars each)
        df['bucket_id'] = (df['bar_index'] - 1) // 6
        bucket_df = df.groupby('bucket_id')['high_formed_pct'].sum().reset_index()
        
        # Create labels
        start_hour = 9
        start_min = 15
        labels = []
        for i in bucket_df['bucket_id']:
            bucket_start_min = start_min + (i * 30)
            h1 = start_hour + (bucket_start_min // 60)
            m1 = bucket_start_min % 60
            
            bucket_end_min = bucket_start_min + 30
            h2 = start_hour + (bucket_end_min // 60)
            m2 = bucket_end_min % 60
            
            # Safe string concatenation
            label = f"{int(h1):02d}:{int(m1):02d}" + "\n-\n" + f"{int(h2):02d}:{int(m2):02d}"
            labels.append(label)

        bucket_df['label'] = labels

        # --- PLOTTING ---
        plt.figure(figsize=(12, 7))
        
        # Bar Chart
        bars = plt.bar(bucket_df.index, bucket_df['high_formed_pct'], color='skyblue', edgecolor='blue', alpha=0.7)
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                     f'{height:.1f}%',
                     ha='center', va='bottom', fontsize=9)

        # Title
        file_name = os.path.basename(file_path).replace('.csv', '')
        parent_dir = os.path.basename(os.path.dirname(file_path))
        title_text = f'High of Day Formation Time\nScenario: {file_name} ({parent_dir})'
        # Check if the title text needs explicit concatenation for safety
        title_text = "High of Day Formation Time" + "\n" + f"Scenario: {file_name} ({parent_dir})"
        plt.title(title_text, fontsize=14)
        plt.xlabel('Time Bucket', fontsize=11)
        plt.ylabel('Percentage of Days (%)', fontsize=11)
        
        plt.xticks(bucket_df.index, bucket_df['label'], rotation=0, fontsize=8)
        plt.grid(True, axis='y', alpha=0.3)
        plt.ylim(0, max(bucket_df['high_formed_pct'].max() * 1.15, 10)) # Add headroom
        
        # Save
        output_plot_path = file_path.replace('.csv', '-distribution.png')
        plt.savefig(output_plot_path)
        plt.close()
        print(f"  Saved plot to {output_plot_path}")

    except Exception as e:
        print(f"  Error processing {file_path}: {e}")

def main():
    for d in DIRECTORIES:
        if not os.path.exists(d):
            print(f"Directory {d} not found. Skipping.")
            continue
            
        csv_files = glob.glob(os.path.join(d, "*.csv"))
        print(f"\n--- Scanning {d} ({len(csv_files)} files) ---")
        
        for f in csv_files:
            process_file(f)

if __name__ == "__main__":
    main()
