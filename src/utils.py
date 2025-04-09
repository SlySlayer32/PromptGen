import os
import re
import sys
import logging
import fnmatch
import requests
from datetime import datetime

def setup_logging():
    """Set up logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

def set_output(name, value):
    """Set GitHub Actions output variable."""
    # GitHub Actions environment file
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for testing outside GitHub Actions
        print(f"::set-output name={name}::{value}")

def filter_files(files, exclude_patterns):
    """
    Filter files based on exclude patterns.
    
    Args:
        files (list): List of file paths
        exclude_patterns (list): List of glob patterns to exclude
        
    Returns:
        list: Filtered list of file paths
    """
    if not exclude_patterns:
        return files
        
    filtered_files = []
    for file_path in files:
        excluded = False
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern.strip()):
                excluded = True
                break
        if not excluded:
            filtered_files.append(file_path)
    
    return filtered_files

def create_report(results):
    """
    Create a markdown report of transformation results.
    
    Args:
        results (dict): Transformation results
        
    Returns:
        str: Markdown formatted report
    """
    if results['transformed_files'] == 0:
        return "No files were transformed."
        
    report = []
    report.append("### Files Transformed")
    report.append("")
    
    # Add table header
    report.append("| File | Words | Characters |")
    report.append("|------|-------|------------|")
    
    # Sort files by transformation size
    sorted_files = sorted(
        results['files'], 
        key=lambda x: x['chars_transformed'], 
        reverse=True
    )
    
    # Add top 10 files to table
    for file_info in sorted_files[:10]:
        file_path = file_info['path']
        words = file_info['words_transformed']
        chars = file_info['chars_transformed']
        report.append(f"| {file_path} | {words} | {chars} |")
    
    if len(sorted_files) > 10:
        report.append("")
        report.append(f"*... and {len(sorted_files) - 10} more files*")
    
    return "\n".join(report)

def report_usage(api_token, tier_level, files_processed, files_transformed, words_transformed, chars_transformed):
    """
    Report usage statistics to the API for billing and analytics.
    
    Args:
        api_token (str): API token
        tier_level (str): Subscription tier level
        files_processed (int): Number of files processed
        files_transformed (int): Number of files transformed
        words_transformed (int): Number of words transformed
        chars_transformed (int): Number of characters transformed
    """
    try:
        # Prepare usage data
        usage_data = {
            "token": api_token,
            "tier": tier_level,
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "files_processed": files_processed,
                "files_transformed": files_transformed,
                "words_transformed": words_transformed,
                "chars_transformed": chars_transformed
            }
        }
        
        # Send usage data to API
        response = requests.post(
            "https://api.comp-linguistics.io/v1/usage",
            json=usage_data,
            headers={"Content-Type": "application/json"},
            timeout=5  # Short timeout to avoid blocking
        )
        
        if response.status_code != 200:
            logger = logging.getLogger()
            logger.warning(f"Failed to report usage: {response.status_code} - {response.text}")
            
    except Exception as e:
        # Don't fail the action if usage reporting fails
        logger = logging.getLogger()
        logger.warning(f"Error reporting usage: {str(e)}")
        pass
