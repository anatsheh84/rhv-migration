"""
data_processor.py
-----------------
Loads RHV Excel export and transforms data for dashboard generation.
All tabs consume data from this module.
"""

import pandas as pd
from datetime import datetime
from collections import defaultdict
import re


# Column mapping: expected name -> possible variations in Excel
COLUMN_MAPPING = {
    'vm_name': ['vm_name', 'name', 'vm'],
    'cluster_name': ['cluster_name', 'cluster'],
    'storage_pool_name': ['storage_pool_name', 'storage_pool', 'storage_domain'],
    'guest_os': ['guest_os', 'os', 'operating_system'],
    'vm_host': ['vm_host', 'host', 'hypervisor'],
    'status': ['On/Off', 'status', 'power_state', 'state'],
    'mem_size_GB': ['mem_size_GB', 'memory', 'ram', 'mem_gb'],
    'num_of_cpus': ['num_of_cpus', 'vcpus', 'cpus', 'cpu'],
    'storage_size_GB': ['storage_size-GB', 'storage_size_GB', 'provisioned_storage', 'storage'],
    'used_size_GB': ['used_size-GB', 'used_size_GB', 'used_storage'],
    'creation_date': ['creation_date', 'created', 'create_date']
}


def find_column(df_columns, expected_name):
    """Find matching column from possible variations."""
    variations = COLUMN_MAPPING.get(expected_name, [expected_name])
    for var in variations:
        for col in df_columns:
            if col.lower().strip() == var.lower().strip():
                return col
    return None


def load_excel(filepath):
    """Load Excel file and normalize column names."""
    df = pd.read_excel(filepath)
    
    # Map columns to standardized names
    column_map = {}
    for std_name in COLUMN_MAPPING.keys():
        found = find_column(df.columns, std_name)
        if found:
            column_map[found] = std_name
    
    df = df.rename(columns=column_map)
    return df


def clean_data(df):
    """Filter out invalid rows and handle data types."""
    # Remove rows without vm_name (likely summary rows)
    df = df[df['vm_name'].notna() & (df['vm_name'] != '')]
    
    # Remove potential total/summary rows (unusually high values)
    if len(df) > 1:
        mem_threshold = df['mem_size_GB'].quantile(0.99) * 10
        df = df[df['mem_size_GB'] <= mem_threshold]
    
    # Ensure numeric columns
    df['mem_size_GB'] = pd.to_numeric(df['mem_size_GB'], errors='coerce').fillna(0).astype(int)
    df['num_of_cpus'] = pd.to_numeric(df['num_of_cpus'], errors='coerce').fillna(0).astype(int)
    df['storage_size_GB'] = pd.to_numeric(df['storage_size_GB'], errors='coerce').fillna(0)
    df['used_size_GB'] = pd.to_numeric(df['used_size_GB'], errors='coerce').fillna(0)
    
    # Parse dates
    df['creation_date'] = pd.to_datetime(df['creation_date'], errors='coerce')
    
    return df.reset_index(drop=True)


def get_os_family(guest_os):
    """Determine OS family from guest OS string."""
    if pd.isna(guest_os):
        return 'Unknown'
    os_lower = str(guest_os).lower()
    if 'windows' in os_lower:
        return 'Windows'
    return 'Linux'


def get_consolidated_os(guest_os):
    """Consolidate OS versions (e.g., RHEL 8.6 -> RHEL 8)."""
    if pd.isna(guest_os):
        return 'Unknown'
    
    os_str = str(guest_os).strip()
    
    # RHEL consolidation: RHEL 8.x -> RHEL 8, RHEL 9.x -> RHEL 9
    rhel_match = re.match(r'(RHEL|Red Hat Enterprise Linux)\s*(\d+)', os_str, re.IGNORECASE)
    if rhel_match:
        major_ver = rhel_match.group(2)
        return f'RHEL {major_ver}'
    
    # Windows consolidation
    if 'windows' in os_str.lower():
        # Windows Server versions
        win_match = re.match(r'Windows\s*(Server\s*)?(\d+)', os_str, re.IGNORECASE)
        if win_match:
            year = win_match.group(2)
            return f'Windows {year}'
        # Windows 10/11
        win_client = re.match(r'Windows\s*(\d+)', os_str, re.IGNORECASE)
        if win_client:
            return f'Windows {win_client.group(1)}'
    
    return os_str


def get_size_category(mem_gb, vcpus):
    """
    Categorize VM by size.
    Small: ≤8 GB RAM, ≤4 vCPU
    Medium: ≤32 GB RAM, ≤8 vCPU
    Large: ≤64 GB RAM, ≤16 vCPU
    X-Large: >64 GB RAM or >16 vCPU
    """
    if mem_gb > 64 or vcpus > 16:
        return 'X-Large'
    if mem_gb > 32 or vcpus > 8:
        return 'Large'
    if mem_gb > 8 or vcpus > 4:
        return 'Medium'
    return 'Small'


def get_migration_complexity(guest_os, os_family, mem_gb, vcpus):
    """
    Determine migration complexity.
    Low: Linux VMs (RHEL 8/9) with standard sizing
    Medium: Windows VMs, RHEL 7, or large VMs (>64GB or >16 vCPU)
    High: Large Windows VMs (>64GB RAM or >16 vCPU)
    """
    is_large = mem_gb > 64 or vcpus > 16
    is_rhel7 = 'rhel 7' in str(guest_os).lower() or 'rhel7' in str(guest_os).lower()
    
    if os_family == 'Windows':
        if is_large:
            return 'High'
        return 'Medium'
    
    # Linux
    if is_rhel7:
        return 'Medium'
    if is_large:
        return 'Medium'
    
    return 'Low'


def add_derived_fields(df):
    """Add computed fields to dataframe."""
    df['os_family'] = df['guest_os'].apply(get_os_family)
    df['os_consolidated'] = df['guest_os'].apply(get_consolidated_os)
    df['size_category'] = df.apply(lambda r: get_size_category(r['mem_size_GB'], r['num_of_cpus']), axis=1)
    df['complexity'] = df.apply(
        lambda r: get_migration_complexity(r['guest_os'], r['os_family'], r['mem_size_GB'], r['num_of_cpus']), 
        axis=1
    )
    df['storage_efficiency'] = df.apply(
        lambda r: round((r['used_size_GB'] / r['storage_size_GB']) * 100, 1) if r['storage_size_GB'] > 0 else 0,
        axis=1
    )
    return df


def compute_statistics(df):
    """Compute aggregate statistics for dashboard."""
    stats = {
        'total_vms': len(df),
        'total_vcpus': int(df['num_of_cpus'].sum()),
        'total_memory_gb': int(df['mem_size_GB'].sum()),
        'total_storage_provisioned_gb': round(df['storage_size_GB'].sum(), 2),
        'total_storage_used_gb': round(df['used_size_GB'].sum(), 2),
        'clusters': df['cluster_name'].nunique(),
        'hosts': df['vm_host'].nunique(),
        'running_vms': len(df[df['status'] == 'On']),
        'stopped_vms': len(df[df['status'] == 'Off']),
    }
    
    # Date statistics
    valid_dates = df[df['creation_date'].notna()]['creation_date']
    if len(valid_dates) > 0:
        stats['first_vm_date'] = valid_dates.min().strftime('%Y-%m-%d')
        stats['last_vm_date'] = valid_dates.max().strftime('%Y-%m-%d')
        
        # Monthly VM creation stats
        df_with_dates = df[df['creation_date'].notna()].copy()
        df_with_dates['month'] = df_with_dates['creation_date'].dt.to_period('M')
        monthly_counts = df_with_dates.groupby('month').size()
        
        if len(monthly_counts) > 0:
            stats['avg_vms_per_month'] = round(monthly_counts.mean(), 1)
            stats['peak_month'] = str(monthly_counts.idxmax())
            stats['peak_month_count'] = int(monthly_counts.max())
    
    return stats


def compute_distributions(df):
    """Compute distribution data for charts."""
    distributions = {}
    
    # OS Family distribution
    distributions['os_family'] = df['os_family'].value_counts().to_dict()
    
    # Consolidated OS distribution
    distributions['os_consolidated'] = df['os_consolidated'].value_counts().to_dict()
    
    # Size category distribution
    distributions['size_category'] = df['size_category'].value_counts().to_dict()
    
    # Complexity distribution
    distributions['complexity'] = df['complexity'].value_counts().to_dict()
    
    # Status distribution
    distributions['status'] = df['status'].value_counts().to_dict()
    
    # Cluster distribution
    cluster_stats = df.groupby('cluster_name').agg({
        'vm_name': 'count',
        'num_of_cpus': 'sum',
        'mem_size_GB': 'sum',
        'storage_size_GB': 'sum',
        'used_size_GB': 'sum'
    }).rename(columns={'vm_name': 'vm_count'})
    distributions['by_cluster'] = cluster_stats.to_dict('index')
    
    # Host distribution
    host_stats = df.groupby('vm_host').agg({
        'vm_name': 'count',
        'num_of_cpus': 'sum',
        'mem_size_GB': 'sum'
    }).rename(columns={'vm_name': 'vm_count'})
    distributions['by_host'] = host_stats.to_dict('index')
    
    return distributions


def compute_size_category_details(df):
    """Compute detailed breakdown by size category."""
    size_order = ['Small', 'Medium', 'Large', 'X-Large']
    size_specs = {
        'Small': {'cpu_range': '≤4', 'mem_range': '≤8 GB'},
        'Medium': {'cpu_range': '≤8', 'mem_range': '≤32 GB'},
        'Large': {'cpu_range': '≤16', 'mem_range': '≤64 GB'},
        'X-Large': {'cpu_range': '>16', 'mem_range': '>64 GB'}
    }
    
    details = []
    for size in size_order:
        subset = df[df['size_category'] == size]
        if len(subset) > 0:
            details.append({
                'category': size,
                'cpu_range': size_specs[size]['cpu_range'],
                'mem_range': size_specs[size]['mem_range'],
                'vm_count': len(subset),
                'total_vcpus': int(subset['num_of_cpus'].sum()),
                'total_memory': int(subset['mem_size_GB'].sum()),
                'total_storage': round(subset['storage_size_GB'].sum(), 2)
            })
    
    return details


def compute_migration_waves(df):
    """Generate suggested migration waves."""
    waves = []
    
    # Wave 1: Low complexity Linux VMs (RHEL 8/9, small/medium)
    wave1 = df[(df['complexity'] == 'Low') & (df['os_family'] == 'Linux')]
    if len(wave1) > 0:
        waves.append({
            'wave': 1,
            'name': 'Pilot - Low Complexity Linux',
            'description': 'RHEL 8/9 VMs with standard sizing',
            'criteria': 'Linux, Low complexity, Small/Medium size',
            'vm_count': len(wave1),
            'vcpus': int(wave1['num_of_cpus'].sum()),
            'memory_gb': int(wave1['mem_size_GB'].sum())
        })
    
    # Wave 2: Medium complexity Linux (RHEL 7, large Linux)
    wave2 = df[(df['complexity'] == 'Medium') & (df['os_family'] == 'Linux')]
    if len(wave2) > 0:
        waves.append({
            'wave': 2,
            'name': 'Linux Extended',
            'description': 'RHEL 7 and large Linux VMs',
            'criteria': 'Linux, Medium complexity (RHEL 7 or >64GB/>16 vCPU)',
            'vm_count': len(wave2),
            'vcpus': int(wave2['num_of_cpus'].sum()),
            'memory_gb': int(wave2['mem_size_GB'].sum())
        })
    
    # Wave 3: Medium complexity Windows (standard Windows)
    wave3 = df[(df['complexity'] == 'Medium') & (df['os_family'] == 'Windows')]
    if len(wave3) > 0:
        waves.append({
            'wave': 3,
            'name': 'Windows Standard',
            'description': 'Windows VMs with standard sizing',
            'criteria': 'Windows, ≤64GB RAM, ≤16 vCPU',
            'vm_count': len(wave3),
            'vcpus': int(wave3['num_of_cpus'].sum()),
            'memory_gb': int(wave3['mem_size_GB'].sum())
        })
    
    # Wave 4: High complexity (large Windows)
    wave4 = df[df['complexity'] == 'High']
    if len(wave4) > 0:
        waves.append({
            'wave': 4,
            'name': 'High Complexity',
            'description': 'Large Windows VMs requiring special attention',
            'criteria': 'Windows, >64GB RAM or >16 vCPU',
            'vm_count': len(wave4),
            'vcpus': int(wave4['num_of_cpus'].sum()),
            'memory_gb': int(wave4['mem_size_GB'].sum())
        })
    
    return waves


def compute_growth_trends(df):
    """Compute historical growth data for trend charts."""
    df_dated = df[df['creation_date'].notna()].copy()
    if len(df_dated) == 0:
        return None
    
    df_dated = df_dated.sort_values('creation_date')
    df_dated['month'] = df_dated['creation_date'].dt.to_period('M')
    
    # Monthly aggregations
    monthly = df_dated.groupby('month').agg({
        'vm_name': 'count',
        'num_of_cpus': 'sum',
        'mem_size_GB': 'sum',
        'storage_size_GB': 'sum'
    }).rename(columns={'vm_name': 'vm_count'})
    
    # Cumulative values
    monthly['cumulative_vms'] = monthly['vm_count'].cumsum()
    monthly['cumulative_vcpus'] = monthly['num_of_cpus'].cumsum()
    monthly['cumulative_memory'] = monthly['mem_size_GB'].cumsum()
    
    # Convert to serializable format
    trends = {
        'months': [str(m) for m in monthly.index],
        'monthly_vms': monthly['vm_count'].tolist(),
        'monthly_vcpus': monthly['num_of_cpus'].tolist(),
        'monthly_memory': monthly['mem_size_GB'].tolist(),
        'cumulative_vms': monthly['cumulative_vms'].tolist(),
        'cumulative_vcpus': monthly['cumulative_vcpus'].tolist(),
        'cumulative_memory': monthly['cumulative_memory'].tolist()
    }
    
    return trends


def compute_complexity_by_os(df):
    """Compute complexity breakdown by OS type for stacked chart."""
    result = {}
    for os_type in df['os_consolidated'].unique():
        subset = df[df['os_consolidated'] == os_type]
        result[os_type] = {
            'Low': len(subset[subset['complexity'] == 'Low']),
            'Medium': len(subset[subset['complexity'] == 'Medium']),
            'High': len(subset[subset['complexity'] == 'High'])
        }
    return result


def prepare_vm_list(df):
    """Prepare VM list for inventory table (as list of dicts)."""
    vm_list = []
    for _, row in df.iterrows():
        vm_list.append({
            'vm_name': str(row['vm_name']),
            'cluster': str(row['cluster_name']),
            'guest_os': str(row['guest_os']),
            'host': str(row['vm_host']),
            'status': str(row['status']),
            'memory_gb': int(row['mem_size_GB']),
            'vcpus': int(row['num_of_cpus']),
            'storage_gb': round(row['storage_size_GB'], 2),
            'used_gb': round(row['used_size_GB'], 2),
            'utilization': round(row['storage_efficiency'], 1),
            'size_category': row['size_category'],
            'complexity': row['complexity'],
            'os_family': row['os_family'],
            'os_consolidated': row['os_consolidated'],
            'creation_date': row['creation_date'].strftime('%Y-%m-%d') if pd.notna(row['creation_date']) else ''
        })
    return vm_list


def process_excel(filepath):
    """
    Main entry point: Load and process Excel file.
    Returns a dictionary with all data needed by dashboard tabs.
    """
    # Load and clean
    df = load_excel(filepath)
    df = clean_data(df)
    df = add_derived_fields(df)
    
    # Build output data structure
    data = {
        'stats': compute_statistics(df),
        'distributions': compute_distributions(df),
        'size_details': compute_size_category_details(df),
        'migration_waves': compute_migration_waves(df),
        'growth_trends': compute_growth_trends(df),
        'complexity_by_os': compute_complexity_by_os(df),
        'vm_list': prepare_vm_list(df),
        'unique_clusters': sorted(df['cluster_name'].unique().tolist()),
        'unique_hosts': sorted(df['vm_host'].unique().tolist()),
        'unique_os': sorted(df['os_consolidated'].unique().tolist()),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return data


# For testing
if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python data_processor.py <excel_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    data = process_excel(filepath)
    
    # Print summary
    print(f"\n{'='*50}")
    print("DATA PROCESSING SUMMARY")
    print(f"{'='*50}")
    print(f"Total VMs: {data['stats']['total_vms']}")
    print(f"Total vCPUs: {data['stats']['total_vcpus']}")
    print(f"Total Memory: {data['stats']['total_memory_gb']} GB")
    print(f"Total Storage Provisioned: {data['stats']['total_storage_provisioned_gb']:.2f} GB")
    print(f"Total Storage Used: {data['stats']['total_storage_used_gb']:.2f} GB")
    print(f"\nClusters: {data['unique_clusters']}")
    print(f"Hosts: {data['unique_hosts']}")
    print(f"\nOS Family Distribution: {data['distributions']['os_family']}")
    print(f"Size Distribution: {data['distributions']['size_category']}")
    print(f"Complexity Distribution: {data['distributions']['complexity']}")
    print(f"\nMigration Waves:")
    for wave in data['migration_waves']:
        print(f"  Wave {wave['wave']}: {wave['name']} - {wave['vm_count']} VMs")
    print(f"\nGenerated at: {data['generated_at']}")
