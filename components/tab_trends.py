"""
tab_trends.py
-------------
Tab 4: Growth Trends
Displays historical VM creation and resource growth over time.
"""


def generate_stat_cards(stats):
    """Generate the trends stat cards HTML."""
    first_date = stats.get('first_vm_date', 'N/A')
    last_date = stats.get('last_vm_date', 'N/A')
    avg_per_month = stats.get('avg_vms_per_month', 0)
    peak_month = stats.get('peak_month', 'N/A')
    peak_count = stats.get('peak_month_count', 0)
    
    return f'''            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">First VM Created</div>
                    <div class="stat-value" style="font-size: 24px;">{first_date}</div>
                    <div class="stat-detail">Earliest VM in inventory</div>
                </div>
                <div class="stat-card blue">
                    <div class="stat-label">Last VM Created</div>
                    <div class="stat-value" style="font-size: 24px;">{last_date}</div>
                    <div class="stat-detail">Most recent VM provisioned</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-label">Avg VMs/Month</div>
                    <div class="stat-value">{avg_per_month}</div>
                    <div class="stat-detail">Average monthly provisioning rate</div>
                </div>
                <div class="stat-card orange">
                    <div class="stat-label">Peak Month</div>
                    <div class="stat-value" style="font-size: 24px;">{peak_month}</div>
                    <div class="stat-detail">{peak_count} VMs provisioned</div>
                </div>
            </div>
'''


def generate_charts_section():
    """Generate the chart containers for the trends tab."""
    return '''            <div class="charts-grid">
                <div class="chart-card full-width">
                    <div class="chart-title">VM Count Growth Over Time (Cumulative)</div>
                    <div class="chart-container">
                        <canvas id="chart-vm-growth"></canvas>
                    </div>
                </div>
                <div class="chart-card full-width">
                    <div class="chart-title">CPU & Memory Growth Over Time (Cumulative)</div>
                    <div class="chart-container">
                        <canvas id="chart-resource-growth"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">VMs Provisioned Per Month</div>
                    <div class="chart-container">
                        <canvas id="chart-vms-per-month"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Resources Added Per Month</div>
                    <div class="chart-container">
                        <canvas id="chart-resources-per-month"></canvas>
                    </div>
                </div>
            </div>
'''


def generate_tab_trends(data):
    """
    Generate complete HTML for the Growth Trends tab.
    
    Args:
        data: Processed data dictionary from data_processor
        
    Returns:
        HTML string for the trends tab content
    """
    stats = data.get('stats', {})
    
    html = generate_stat_cards(stats)
    html += generate_charts_section()
    
    return html


def get_trends_chart_configs(data):
    """
    Generate JavaScript chart configuration objects for Trends tab.
    """
    trends = data.get('growth_trends', {})
    
    if not trends:
        return {
            'vm_growth': {'labels': [], 'values': []},
            'resource_growth': {'labels': [], 'vcpus': [], 'memory': []},
            'vms_per_month': {'labels': [], 'values': []},
            'resources_per_month': {'labels': [], 'vcpus': [], 'memory': []}
        }
    
    return {
        'vm_growth': {
            'labels': trends.get('months', []),
            'values': trends.get('cumulative_vms', [])
        },
        'resource_growth': {
            'labels': trends.get('months', []),
            'vcpus': trends.get('cumulative_vcpus', []),
            'memory': trends.get('cumulative_memory', [])
        },
        'vms_per_month': {
            'labels': trends.get('months', []),
            'values': trends.get('monthly_vms', [])
        },
        'resources_per_month': {
            'labels': trends.get('months', []),
            'vcpus': trends.get('monthly_vcpus', []),
            'memory': trends.get('monthly_memory', [])
        }
    }


# For testing
if __name__ == '__main__':
    mock_data = {
        'stats': {
            'first_vm_date': '2023-08-20',
            'last_vm_date': '2025-11-04',
            'avg_vms_per_month': 4.5,
            'peak_month': '2023-09',
            'peak_month_count': 35
        },
        'growth_trends': {
            'months': ['2023-08', '2023-09', '2023-10'],
            'monthly_vms': [2, 35, 10],
            'cumulative_vms': [2, 37, 47],
            'monthly_vcpus': [20, 300, 100],
            'cumulative_vcpus': [20, 320, 420],
            'monthly_memory': [50, 800, 200],
            'cumulative_memory': [50, 850, 1050]
        }
    }
    
    html = generate_tab_trends(mock_data)
    print(f"Trends tab HTML generated: {len(html)} characters")
