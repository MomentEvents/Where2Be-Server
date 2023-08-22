import os

# Define the directory and output file paths
dir_path = "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/data_UCSD_saved"
output_file = "json_filepaths.txt"

# Open the output file for writing
with open(output_file, 'w') as outfile:
    # Walk through each file in the directory
    for root, _, files in os.walk(dir_path):
        for file in files:
            # Check if the file is a JSON file
            if file.endswith('.json'):
                # Write the full path of the JSON file to the output file
                outfile.write(os.path.join(root, file) + "\n")

print(f"File paths written to {output_file}")
