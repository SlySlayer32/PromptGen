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
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Transform text into computational linguistics style')
    
    parser.add_argument('--intensity', type=float, default=0.7,
                        help='Transformation intensity (0.0-1.0)')
    
    parser.add_argument('--file-patterns', type=str, default='*.md,*.txt,*.rst',
                        help='File patterns to include (comma-separated)')
    
    parser.add_argument('--exclude-patterns', type=str, default='node_modules/**,vendor/**,dist/**',
                        help='File patterns to exclude (comma-separated)')
    
    parser.add_argument('--output-method', type=str, default='artifact',
                        choices=['in-place', 'pr', 'comment', 'artifact'],
                        help='Output method')
    
    parser.add_argument('--custom-terminology', type=str, default='',
                        help='Path to custom terminology JSON file')
    
    parser.add_argument('--api-token', type=str, required=True,
                        help='API token for authentication and billing')
    
    parser.add_argument('--tier-level', type=str, required=True,
                        help='Subscription tier level')
    
    parser.add_argument('--github-token', type=str, default='',
                        help='GitHub token for PR and comment creation')
    
    return parser.parse_args()
