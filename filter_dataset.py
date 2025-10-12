'''
This script filters a CSV file to remove rows containing specific keywords in the 'text' column.
'''
import pandas as pd

# Keywords to identify website-related content
KEYWORDS = ['http', 'www', '.com', 'link', 'situs', 'website', 'daftar', 'kunjungi', 'gabung', 'di sini', 'bio']

# Read the dataset
df = pd.read_csv('data/dataset.csv')

# Filter out rows containing the keywords (case-insensitive)
filtered_df = df[~df['text'].str.contains('|'.join(KEYWORDS), case=False, na=False)]

# Save the filtered dataset
filtered_df.to_csv('data/dataset_filtered.csv', index=False)

print("Dataset filtered. Saved to data/dataset_filtered.csv")