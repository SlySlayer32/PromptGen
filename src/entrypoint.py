#!/usr/bin/env python3

import os
import sys
import json
import glob
import argparse
import logging
from pathlib import Path
import requests
import yaml
from github import Github
from tqdm import tqdm
import git

# Import our transformer module
from transformer import CompLinguisticsTransformer
from utils import setup_logging, set_output, filter_files, create_report, report_usage

# Set up logging
logger = setup_logging()

def parse_args():
    """Parse command line arguments with validation."""
    parser = argparse.ArgumentParser(description='Transform text into computational linguistics style')
    
    parser.add_argument('--intensity', type=float, default=0.7,
                        help='Transformation intensity (0.0-1.0). Must be between 0.0 and 1.0.')
    
    parser.add_argument('--file-patterns', type=str, default='*.md,*.txt,*.rst',
                        help='File patterns to include (comma-separated).')
    
    parser.add_argument('--exclude-patterns', type=str, default='node_modules/**,vendor/**,dist/**',
                        help='File patterns to exclude (comma-separated).')
    
    parser.add_argument('--output-method', type=str, default='artifact',
                        choices=['in-place', 'pr', 'comment', 'artifact'],
                        help='Output method.')
    
    parser.add_argument('--custom-terminology', type=str, default='',
                        help='Path to custom terminology JSON file.')
    
    parser.add_argument('--api-token', type=str, required=True,
                        help='API token for authentication and billing.')
    
    parser.add_argument('--tier-level', type=str, required=True,
                        help='Subscription tier level.')
    
    parser.add_argument('--github-token', type=str, default='',
                        help='GitHub token for PR and comment creation.')
    
    args = parser.parse_args()

    # Validate arguments
    if not (0.0 <= args.intensity <= 1.0):
        parser.error("--intensity must be between 0.0 and 1.0")

    if args.custom_terminology and not Path(args.custom_terminology).is_file():
        parser.error(f"--custom-terminology file '{args.custom_terminology}' does not exist or is not a valid file.")
    
    return args

def process_files(file_patterns, exclude_patterns):
    """Process files matching the specified patterns."""
    logger.info("Filtering files...")
    try:
        included_files = filter_files(file_patterns, exclude_patterns)
        logger.info(f"Found {len(included_files)} files to process.")
        return included_files
    except Exception as e:
        logger.error(f"Error filtering files: {e}")
        sys.exit(1)

def main():
    """Main function to handle the transformation process."""
    args = parse_args()

    # Log execution details
    logger.info("Starting text transformation process...")
    logger.info(f"Transformation intensity: {args.intensity}")
    logger.info(f"Output method: {args.output_method}")

    # Process files
    files_to_process = process_files(args.file_patterns, args.exclude_patterns)

    # Load custom terminology if provided
    terminology = {}
    if args.custom_terminology:
        try:
            with open(args.custom_terminology, 'r') as f:
                terminology = json.load(f)
            logger.info("Custom terminology loaded successfully.")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in custom terminology file: {e}")
            sys.exit(1)

    # Initialize the transformer
    transformer = CompLinguisticsTransformer(intensity=args.intensity, custom_terminology=terminology)

    # Transform files
    for file_path in tqdm(files_to_process, desc="Processing files"):
        try:
            logger.info(f"Transforming file: {file_path}")
            transformer.transform(file_path)
        except Exception as e:
            logger.error(f"Error transforming file '{file_path}': {e}")

    # Generate a report
    try:
        report_path = create_report(files_to_process)
        logger.info(f"Report created at: {report_path}")
    except Exception as e:
        logger.error(f"Error creating report: {e}")

    # Report usage for analytics
    report_usage(args.api_token, tier_level=args.tier_level)

    logger.info("Transformation process completed successfully.")

if __name__ == "__main__":
    main()
