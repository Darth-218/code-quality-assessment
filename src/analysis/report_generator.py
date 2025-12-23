"""
Module for generating reports from the metrics taxonomy.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

def save_report(filename: str, report: Dict[str, Any]) -> str:
    """
    Save the report to a JSON file.
    
    Args:
        filename: Name of the output file
        report: The report data to save
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # Save to JSON file with pretty formatting
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return os.path.abspath(filename)

def generate_report(taxonomy: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Generate a comprehensive report from the metrics taxonomy.
    
    Args:
        taxonomy: The extracted metrics taxonomy
        output_dir: Directory to save the report
        
    Returns:
        Path to the generated report file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"metrics_taxonomy_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Create metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "total_categories": len(taxonomy),
        "metrics_count": count_metrics(taxonomy),
        "description": "Comprehensive Software Metrics Taxonomy based on research literature"
    }
    
    # Prepare full report
    report = {
        "metadata": metadata,
        "taxonomy": taxonomy
    }
    
    # Save to JSON file
    save_report(filepath, report)
    
    # Also generate a human-readable summary
    generate_summary(taxonomy, output_dir, timestamp)
    
    return filepath

def count_metrics(taxonomy: Dict[str, Any]) -> int:
    """Count total number of metrics in the taxonomy."""
    count = 0
    
    for category, content in taxonomy.items():
        if isinstance(content, list):
            count += len(content)
        elif isinstance(content, dict):
            for subcat, subcontent in content.items():
                if isinstance(subcontent, list):
                    count += len(subcontent)
    
    return count

def generate_summary(taxonomy: Dict[str, Any], output_dir: str, timestamp: str):
    """Generate a human-readable summary report."""
    summary_path = os.path.join(output_dir, f"taxonomy_summary_{timestamp}.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SOFTWARE METRICS TAXONOMY SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Categories: {len(taxonomy)}\n")
        f.write(f"Total Metrics: {count_metrics(taxonomy)}\n\n")
        
        for i, (category, content) in enumerate(taxonomy.items(), 1):
            f.write(f"{i}. {category}\n")
            f.write("-" * 40 + "\n")
            
            if isinstance(content, list):
                f.write(f"   Metrics: {len(content)}\n")
                for metric in content[:5]:
                    name = metric.get('metric_name', metric.get('feature_name', metric.get('target_name', 'Unknown')))
                    desc = metric.get('description', 'No description')
                    f.write(f"   • {name}: {desc[:80]}...\n")
                if len(content) > 5:
                    f.write(f"   ... and {len(content) - 5} more metrics\n")
            
            elif isinstance(content, dict):
                total_sub_metrics = 0
                for subcat, subcontent in content.items():
                    if isinstance(subcontent, list):
                        total_sub_metrics += len(subcontent)
                
                f.write(f"   Sub-categories: {len(content)}\n")
                f.write(f"   Total metrics in category: {total_sub_metrics}\n")
                
                for subcat, subcontent in content.items():
                    if isinstance(subcontent, list):
                        f.write(f"   - {subcat}: {len(subcontent)} metrics\n")
            
            f.write("\n")
        
        # Add statistics
        f.write("\n" + "=" * 80 + "\n")
        f.write("STATISTICS\n")
        f.write("=" * 80 + "\n\n")
        
        categories_stats = []
        for category, content in taxonomy.items():
            if isinstance(content, list):
                categories_stats.append((category, len(content)))
            elif isinstance(content, dict):
                total = 0
                for subcat, subcontent in content.items():
                    if isinstance(subcontent, list):
                        total += len(subcontent)
                categories_stats.append((category, total))
        
        # Sort by number of metrics
        categories_stats.sort(key=lambda x: x[1], reverse=True)
        
        for category, count in categories_stats:
            f.write(f"{category:40} : {count:3} metrics\n")
    
    return summary_path