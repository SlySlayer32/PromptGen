import os
import re
import sys
import logging
import fnmatch
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

# Constants
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(name: str = "transformer") -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger(name)
    
    # Add configurable logging levels
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Only add handler if not already added
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger

def set_output(name: str, value: str) -> None:
    """Set GitHub Actions output variable."""
    # Mask sensitive data
    if name.lower() == 'api_token':
        value = '***MASKED***'
    
    # GitHub Actions environment file
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        try:
            with open(github_output, 'a') as f:
                f.write(f"{name}={value}\n")
        except IOError as e:
            print(f"Error writing to GITHUB_OUTPUT: {e}")
            # Fallback to stdout
            print(f"::set-output name={name}::{value}")
    else:
        # Fallback for testing outside GitHub Actions
        print(f"::set-output name={name}::{value}")

def filter_files(files: List[str], exclude_patterns: Optional[List[str]] = None) -> List[str]:
    """
    Filter files based on exclude patterns.
    
    Args:
        files (List[str]): List of file paths
        exclude_patterns (Optional[List[str]]): List of glob patterns to exclude
        
    Returns:
        List[str]: Filtered list of file paths
    """
    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        raise TypeError("files must be a list of strings")
    
    if exclude_patterns is None:
        exclude_patterns = []
    elif not isinstance(exclude_patterns, list):
        raise TypeError("exclude_patterns must be a list of strings")
        
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

def create_report(results: Dict[str, Any]) -> str:
    """
    Create a markdown report of transformation results.
    
    Args:
        results (Dict[str, Any]): Transformation results
        
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

def report_usage(
    api_token: str, 
    tier_level: str, 
    files_processed: int, 
    files_transformed: int, 
    words_transformed: int, 
    chars_transformed: int
) -> None:
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
    logger = logging.getLogger("transformer")
    
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
            logger.warning(f"Failed to report usage: {response.status_code} - {response.text}")
            
    except Exception as e:
        # Don't fail the action if usage reporting fails
        logger.warning(f"Error reporting usage: {str(e)}")
