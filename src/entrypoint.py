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
from typing import List, Dict, Any

# Import our transformer module
from transformer import CompLinguisticsTransformer
from utils import setup_logging, set_output, filter_files, create_report, report_usage

# Version information
__version__ = '1.0.0'

# Set up logging
logger = setup_logging()

def check_dependencies() -> None:
    """Verify that all required dependencies are available."""
    required_modules = ['requests', 'yaml', 'github', 'tqdm', 'git']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Missing required dependencies: {', '.join(missing_modules)}")
        logger.error("Please install them using: pip install " + " ".join(missing_modules))
        sys.exit(1)
    
    # Add a requirements.txt file creation suggestion
    logger.info("Consider creating a requirements.txt file for dependency management.")

def validate_token(token: str, token_name: str) -> bool:
    """Basic validation for API tokens."""
    if not token:
        logger.error(f"{token_name} cannot be empty")
        return False
    
    # Basic validation - tokens are typically at least 10 chars
    if len(token) < 10:
        logger.warning(f"{token_name} seems too short, it might be invalid")
        return False
    
    return True

def parse_args() -> argparse.Namespace:
    """Parse command line arguments with validation."""
    parser = argparse.ArgumentParser(description='Transform text into computational linguistics style')
    
    parser.add_argument('--version', action='version', 
                        version=f'%(prog)s {__version__}')
    
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
    
    parser.add_argument('--api-token', type=str, 
                        default=os.environ.get('API_TOKEN'),
                        help='API token for authentication and billing. Can also be set via API_TOKEN environment variable.')
    
    parser.add_argument('--tier-level', type=str, 
                        default=os.environ.get('TIER_LEVEL'),
                        help='Subscription tier level. Can also be set via TIER_LEVEL environment variable.')
    
    parser.add_argument('--github-token', type=str, 
                        default=os.environ.get('GITHUB_TOKEN', ''),
                        help='GitHub token for PR and comment creation. Can also be set via GITHUB_TOKEN environment variable.')
    
    args = parser.parse_args()

    # Validate arguments
    if not (0.0 <= args.intensity <= 1.0):
        parser.error("--intensity must be between 0.0 and 1.0")

    if args.custom_terminology and not Path(args.custom_terminology).is_file():
        parser.error(f"--custom-terminology file '{args.custom_terminology}' does not exist or is not a valid file.")
    
    # Validate required arguments
    if not args.api_token:
        parser.error("--api-token is required or set API_TOKEN environment variable")
    
    if not args.tier_level:
        parser.error("--tier-level is required or set TIER_LEVEL environment variable")
    
    # Validate token formats
    validate_token(args.api_token, "API token")
    if args.github_token:
        validate_token(args.github_token, "GitHub token")
    
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
        return []  # Return an empty list instead of exiting

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
