#!/bin/bash

# Check if both input and PDB files are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_file> <pdb_file>"
    exit 1
fi

input_file=$1
pdb_file=$2

# Get the directory and base name of the input file
input_dir=$(dirname "$input_file")
input_base=$(basename "$input_file" .inp)

# Define output files
output_ppm="${input_dir}/${input_base}.ppm"
output_png="${input_dir}/${input_base}.png"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file $input_file not found!"
    exit 1
fi

# Check if PDB file exists
if [ ! -f "$pdb_file" ]; then
    echo "PDB file $pdb_file not found!"
    exit 1
fi

# Run the illustrate command with the input file
./illustrate <"$input_file"

# Convert the output to PNG with transparency
magick ${output_ppm} opacity.pnm -compose copy-opacity -composite ${output_png}

# Clean up temporary files
rm -f opacity.pnm
rm -f ${output_ppm}

echo "Generated image: ${output_png}"
