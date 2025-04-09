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

def validate_token_and_tier(api_token, tier_level):
    """Validate if the token allows feature usage based on tier."""
    # Validate token with API
    try:
        response = requests.post(
            "https://api.comp-linguistics.io/v1/validate",
            json={"token": api_token},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error(f"API token validation failed: {response.text}")
            sys.exit(1)
            
        validation = response.json()
        if not validation.get("valid", False):
            logger.error("Invalid API token")
            sys.exit(1)
            
        # Check if token matches tier
        if validation.get("tier") != tier_level:
            logger.warning(f"Token tier ({validation.get('tier')}) does not match provided tier ({tier_level})")
            # Use the tier from validation for consistency
            tier_level = validation.get("tier")
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to validation API: {str(e)}")
        # Fallback to local validation if API is unreachable
        logger.warning("Using local tier validation as fallback")
    
    # Get tier features
    # Free tier restrictions
    if tier_level == 'free':
        logger.info("Using free tier with limited features")
        return {
            'max_files': 5,
            'max_chars_per_file': 10000,
            'custom_terminology': False,
            'advanced_transforms': False,
            'bulk_processing': False
        }
    # Pro tier
    elif tier_level == 'pro':
        logger.info("Using pro tier with standard features")
        return {
            'max_files': 100,
            'max_chars_per_file': 100000,
            'custom_terminology': True,
            'advanced_transforms': True,
            'bulk_processing': False
        }
    # Enterprise tier
    elif tier_level == 'enterprise':
        logger.info("Using enterprise tier with all features")
        return {
            'max_files': None,  # Unlimited
            'max_chars_per_file': None,  # Unlimited
            'custom_terminology': True,
            'advanced_transforms': True,
            'bulk_processing': True
        }
    else:
        logger.error(f"Unknown tier level: {tier_level}")
        sys.exit(1)

def load_custom_terminology(terminology_path, tier_features):
    """Load custom terminology if allowed by tier and file exists."""
    if not terminology_path:
        return {}
        
    if not tier_features['custom_terminology']:
        logger.warning("Custom terminology not available in your tier. Upgrade for this feature.")
        return {}
        
    try:
        with open(terminology_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Custom terminology file not found: {terminology_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in custom terminology file: {terminology_path}")
        return {}

def main():
    """Main function to run the transformer."""
    # Parse arguments
    args = parse_args()
    
    # Validate token and get tier features
    tier_features = validate_token_and_tier(args.api_token, args.tier_level)
    
    # Load custom terminology if provided and allowed by tier
    custom_terminology = load_custom_terminology(args.custom_terminology, tier_features)
    
    # Initialize transformer
    transformer = CompLinguisticsTransformer(custom_terminology=custom_terminology)
    
    # Process files
    results, output_dir = process_files(
        transformer, 
        args.file_patterns, 
        args.exclude_patterns, 
        tier_features
    )
    
    # Handle GitHub-specific outputs
    handle_github_outputs(results, output_dir, args)
    
    # Print summary
    logger.info(f"Transformation complete: {results['transformed_files']} of {results['processed_files']} files transformed")
    logger.info(f"Words transformed: {results['transformed_words']}")
    logger.info(f"Characters transformed: {results['transformed_chars']}")
    
    return 0

def process_files(transformer, file_patterns, exclude_patterns, tier_features):
    """Find and process files based on patterns and tier limits."""
    # Find files matching the patterns
    include_patterns = file_patterns.split(',')
    exclude_patterns = exclude_patterns.split(',')
    
    all_files = []
    for pattern in include_patterns:
        all_files.extend(glob.glob(pattern.strip(), recursive=True))
    
    # Filter files based on exclude patterns
    filtered_files = filter_files(all_files, exclude_patterns)
    
    # Apply tier limits
    if tier_features['max_files'] is not None and len(filtered_files) > tier_features['max_files']:
        logger.warning(f"File limit exceeded for your tier: {len(filtered_files)} files found, limit is {tier_features['max_files']}")
        filtered_files = filtered_files[:tier_features['max_files']]
    
    # Process each file
    results = {
        'processed_files': len(filtered_files),
        'transformed_files': 0,
        'transformed_words': 0,
        'transformed_chars': 0,
        'files': []
    }
    
    # Create output directory for artifact method
    output_dir = None
    if args.output_method == 'artifact':
        output_dir = os.path.join(os.getcwd(), 'transformed-output')
        os.makedirs(output_dir, exist_ok=True)
    
    for file_path in tqdm(filtered_files, desc="Transforming files"):
        try:
            # Check file size limit
            file_size = os.path.getsize(file_path)
            if tier_features['max_chars_per_file'] is not None and file_size > tier_features['max_chars_per_file']:
                logger.warning(f"File too large for your tier: {file_path}")
                continue
                
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Transform content
            transformed, stats = transformer.transform(
                content, 
                intensity=args.intensity,
                advanced=tier_features['advanced_transforms']
            )
            
            # Skip if no changes
            if transformed == content:
                logger.info(f"No changes made to {file_path}")
                continue
            
            # Handle output based on method
            if args.output_method == 'in-place':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transformed)
            elif args.output_method == 'artifact':
                # Create relative path structure in output directory
                rel_path = os.path.relpath(file_path, os.getcwd())
                output_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(transformed)
            
            # Update statistics
            results['transformed_files'] += 1
            results['transformed_words'] += stats['words']
            results['transformed_chars'] += stats['chars']
            results['files'].append({
                'path': file_path,
                'words_transformed': stats['words'],
                'chars_transformed': stats['chars']
            })
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
    
    return results, output_dir

def handle_github_outputs(results, output_dir, args):
    """Handle GitHub specific outputs based on the output method."""
    
    # Set GitHub Actions outputs
    set_output('processed_files', str(results['processed_files']))
    set_output('transformed_files', str(results['transformed_files']))
    set_output('transformed_words', str(results['transformed_words']))
    set_output('transformed_chars', str(results['transformed_chars']))
    
    # Generate transformation report
    report = create_report(results)
    set_output('transformation_report', report)
    
    # Report usage statistics for billing
    report_usage(
        api_token=args.api_token,
        tier_level=args.tier_level,
        files_processed=results['processed_files'],
        files_transformed=results['transformed_files'],
        words_transformed=results['transformed_words'],
        chars_transformed=results['transformed_chars']
    )
    
    # Handle output method specific actions
    if args.output_method == 'artifact':
        set_output('output_dir', output_dir)
    
    elif args.output_method == 'comment' and args.github_token:
        try:
            # This assumes we're in a PR context
            github_context = os.getenv('GITHUB_CONTEXT')
            if not github_context:
                logger.error("No GitHub context found")
                return
                
            context = json.loads(github_context)
            if 'event' not in context or 'pull_request' not in context['event']:
                logger.error("Not in a pull request context")
                return
                
            pr_number = context['event']['pull_request']['number']
            repo_name = context['repository']
            
            # Initialize GitHub client
            g = Github(args.github_token)
            repo = g.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Create comment with transformation report
            comment_body = f"""
## Computational Linguistics Transformation Report

This PR has been processed with the Computational Linguistics Transformer.

### Transformation Statistics
- Files processed: {results['processed_files']}
- Files transformed: {results['transformed_files']}
- Words transformed: {results['transformed_words']}
- Characters transformed: {results['transformed_chars']}

{report}

_Generated by [Computational Linguistics Transformer](https://github.com/marketplace/actions/computational-linguistics-transformer)_
"""
            pr.create_issue_comment(comment_body)
            logger.info(f"Created comment on PR #{pr_number}")
            
        except Exception as e:
            logger.error(f"Error creating PR comment: {str(e)}")
    
    elif args.output_method == 'pr' and args.github_token:
        # PR creation is handled by the peter-evans/create-pull-request action
        # in the workflow file, so we don't need to do anything here
        pass

if __name__ == "__main__":
    sys.exit(main())
