#!/usr/bin/env python3
"""
generate_dashboard.py
---------------------
Main orchestrator for RHV to OpenShift Virtualization Migration Dashboard.

Usage:
    python generate_dashboard.py <input_excel> [output_html]
    
Example:
    python generate_dashboard.py RHV-NP-ENV.xlsx dashboard.html
"""

import sys
import os
from datetime import datetime

# Import data processor
from data_processor import process_excel

# Import components
from components import (
    get_base_start,
    get_base_end,
    wrap_tab_content,
    generate_tab_overview,
    get_overview_chart_configs,
    generate_tab_sizing,
    get_sizing_chart_configs,
    generate_tab_migration,
    get_migration_chart_configs,
    generate_tab_trends,
    get_trends_chart_configs,
    generate_tab_forecast,
    get_forecast_base_data,
    generate_tab_inventory,
    generate_scripts
)


def generate_dashboard(input_file, output_file=None):
    """
    Generate the complete HTML dashboard from an Excel file.
    
    Args:
        input_file: Path to RHV Excel export
        output_file: Path for output HTML (optional, defaults to input name + .html)
        
    Returns:
        Path to generated HTML file
    """
    
    # Determine output file name
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}_dashboard.html"
    
    print(f"Processing: {input_file}")
    print(f"Output: {output_file}")
    print("-" * 50)
    
    # Step 1: Process Excel data
    print("Step 1/4: Processing Excel data...")
    data = process_excel(input_file)
    print(f"  ✓ Loaded {data['stats']['total_vms']} VMs")
    print(f"  ✓ {data['stats']['total_vcpus']} vCPUs, {data['stats']['total_memory_gb']} GB Memory")
    
    # Step 2: Generate tab HTML content
    print("Step 2/4: Generating tab content...")
    tabs = {
        'overview': generate_tab_overview(data),
        'sizing': generate_tab_sizing(data),
        'migration': generate_tab_migration(data),
        'trends': generate_tab_trends(data),
        'forecast': generate_tab_forecast(data),
        'inventory': generate_tab_inventory(data)
    }
    print(f"  ✓ Generated 6 tabs")
    
    # Step 3: Collect chart configurations
    print("Step 3/4: Preparing chart configurations...")
    chart_configs = {
        'overview': get_overview_chart_configs(data),
        'sizing': get_sizing_chart_configs(data),
        'migration': get_migration_chart_configs(data),
        'trends': get_trends_chart_configs(data),
        'forecast': get_forecast_base_data(data)
    }
    print(f"  ✓ Prepared chart data for all tabs")
    
    # Step 4: Assemble final HTML
    print("Step 4/4: Assembling dashboard...")
    
    # Build HTML structure
    html_parts = []
    
    # Base start (head, header, filters, tab nav, content wrapper start)
    html_parts.append(get_base_start(data))
    
    # Tab contents
    html_parts.append(wrap_tab_content('overview', tabs['overview'], active=True))
    html_parts.append(wrap_tab_content('sizing', tabs['sizing']))
    html_parts.append(wrap_tab_content('migration', tabs['migration']))
    html_parts.append(wrap_tab_content('trends', tabs['trends']))
    html_parts.append(wrap_tab_content('forecast', tabs['forecast']))
    html_parts.append(wrap_tab_content('inventory', tabs['inventory']))
    
    # Generate JavaScript
    scripts = generate_scripts(data, chart_configs)
    
    # Base end (close content wrapper, scripts, close html)
    html_parts.append(get_base_end(scripts))
    
    # Combine all parts
    final_html = ''.join(html_parts)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    file_size = os.path.getsize(output_file) / 1024
    print(f"  ✓ Dashboard generated: {file_size:.1f} KB")
    print("-" * 50)
    print(f"✅ Success! Dashboard saved to: {output_file}")
    
    return output_file


def main():
    """Command line entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("Error: Please provide an input Excel file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        result = generate_dashboard(input_file, output_file)
        return result
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
