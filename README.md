# RHV to OpenShift Virtualization Migration Dashboard

A comprehensive Python tool for analyzing Red Hat Virtualization (RHV) environments and generating interactive HTML dashboards to plan migration to OpenShift Virtualization.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/anatsheh84/rhv-migration.git
cd rhv-migration

# Install dependencies
pip install pandas openpyxl
```

### Basic Usage

```bash
# Generate dashboard from RHV Excel export
python generate_dashboard.py RHV-Cluster-Export.xlsx

# Specify custom output filename
python generate_dashboard.py RHV-Export.xlsx migration_analysis.html

# Open the generated dashboard in your browser
open RHV-Cluster-Export_dashboard.html  # macOS
xdg-open RHV-Cluster-Export_dashboard.html  # Linux
start RHV-Cluster-Export_dashboard.html  # Windows
```

## Features

### 6 Interactive Dashboard Tabs

1. **Overview** - Executive summary with key metrics and OS distribution
2. **Sizing** - VM sizing analysis and categorization (Small/Medium/Large/X-Large)
3. **Migration** - Migration complexity assessment and 4-wave migration planning
4. **Trends** - Historical growth analysis and creation patterns
5. **Forecast** - Capacity forecasting with 3/6/12-month projections
6. **Inventory** - Searchable VM inventory with all attributes

### Analytics & Insights

- **Complexity Scoring:** Automatically categorizes VMs as Low/Medium/High migration complexity
- **Migration Waves:** Proposes phased migration approach (pilot → extended → standard → high-complexity)
- **Growth Analysis:** Historical trends and monthly creation patterns
- **Resource Planning:** Total vCPUs, memory, and storage requirements
- **OS Consolidation:** Simplifies OS versions (RHEL 8.6 → RHEL 8, Windows Server 2019 → Windows 2019)
- **Storage Efficiency:** Calculates actual usage vs. provisioned capacity

## Input Requirements

### Excel File Format

Your RHV export Excel file should contain columns with these data:

| Column | Required | Description |
|--------|----------|-------------|
| vm_name | ✓ | VM identifier |
| cluster_name | ✓ | Cluster name |
| guest_os | ✓ | Operating system |
| vm_host | ✓ | Physical hypervisor host |
| status | ✓ | Power state (On/Off) |
| mem_size_GB | ✓ | Memory in GB |
| num_of_cpus | ✓ | vCPU count |
| storage_size_GB | ✓ | Provisioned storage in GB |
| used_size_GB | ✓ | Used storage in GB |
| creation_date | | VM creation date (optional) |
| storage_pool_name | | Storage pool (optional) |

**Note:** The tool is flexible with column naming. It will automatically detect common variations like "memory" vs "mem_size_GB", "vcpus" vs "num_of_cpus", etc.

## How It Works

### Data Processing Pipeline

```
1. Load Excel → Normalize columns → Clean data → Add derived fields
                                                    ↓
                        Calculate statistics & distributions
                                    ↓
                            Generate HTML tabs
                                    ↓
                            Embed interactive charts
                                    ↓
                        Output single-file HTML dashboard
```

### Complexity Classification

The tool automatically scores migration complexity:

**Low Complexity**
- Linux VMs with RHEL 8 or RHEL 9
- Standard sizing (≤8 GB RAM, ≤4 vCPU)

**Medium Complexity**
- Windows VMs with standard sizing
- RHEL 7 Linux VMs
- Large Linux VMs (>64 GB RAM or >16 vCPU)

**High Complexity**
- Large Windows VMs (>64 GB RAM or >16 vCPU)
- Requires special attention during migration

### VM Size Categories

- **Small:** ≤4 vCPU and ≤8 GB RAM
- **Medium:** ≤8 vCPU and ≤32 GB RAM
- **Large:** ≤16 vCPU and ≤64 GB RAM
- **X-Large:** >16 vCPU or >64 GB RAM

## Output

The tool generates a **single self-contained HTML file** with:

- Embedded CSS styling
- Chart.js visualization library
- JavaScript interactivity
- No external dependencies (works offline)
- Responsive design (desktop/tablet)
- Search and filtering capabilities
- Export-ready data tables

### File Size

Typical dashboard HTML: 200-500 KB (depending on VM count)

## Performance

| Environment Size | Processing Time |
|-----------------|-----------------|
| <500 VMs | <1 second |
| 500-2000 VMs | 1-3 seconds |
| 2000+ VMs | 3-10 seconds |

## Project Structure

```
rhv-migration/
├── generate_dashboard.py          # Main CLI entry point
├── data_processor.py              # Core data processing engine
├── README.md                      # This file
├── REPOSITORY_INSPECTION.md       # Detailed technical documentation
└── components/                    # UI generation modules
    ├── __init__.py               # Component exports
    ├── base.py                   # HTML structure
    ├── styles.py                 # CSS styling
    ├── scripts.py                # JavaScript logic
    ├── tab_overview.py           # Overview tab
    ├── tab_sizing.py             # Sizing tab
    ├── tab_migration.py          # Migration tab
    ├── tab_trends.py             # Trends tab
    ├── tab_forecast.py           # Forecast tab
    └── tab_inventory.py          # Inventory tab
```

## Dependencies

- **pandas** - Data manipulation and aggregation
- **openpyxl** - Excel file reading (installed via pandas)
- Python 3.6+

## Use Cases

### For Solution Architects
- Assess RHV environment complexity
- Identify suitable migration waves
- Plan target OpenShift Virtualization sizing

### For Infrastructure Teams
- Analyze current virtualization capacity
- Identify large or complex VMs requiring attention
- Plan infrastructure investments

### For Migration Project Managers
- Create phased migration schedules
- Identify low-risk pilot candidates
- Plan resource allocation

### For Capacity Planners
- Forecast growth trends
- Plan future infrastructure needs
- Identify utilization patterns

## Known Limitations

- **No Unit Tests:** Production-ready but lacking automated test coverage
- **No Logging:** Uses print statements for progress
- **No Configuration File:** All settings are hardcoded
- **Limited Validation:** Assumes well-formed input Excel files
- **Single Environment:** Designed for analyzing one RHV environment at a time

## Future Enhancements

Potential additions to the project:

- Unit test suite
- Requirements.txt file
- Logging framework
- Configuration file support
- REST API for programmatic access
- Multi-environment comparison
- Cost analysis modeling
- Performance data integration
- Pre-migration validation checks
- Post-migration success tracking

## Troubleshooting

### "No module named 'pandas'"
```bash
pip install pandas openpyxl
```

### "File not found" error
Ensure the Excel file path is correct and the file exists.

### Dashboard displays but no data
Check that the Excel file contains the required columns. The tool expects at least:
- vm_name
- cluster_name
- guest_os
- mem_size_GB
- num_of_cpus

### Charts not rendering
Ensure JavaScript is enabled in your browser. The dashboard uses Chart.js for visualizations.

## Contributing

This project is actively maintained. Contributions are welcome for:
- Bug fixes
- Feature enhancements
- Documentation improvements
- Test suite development

## License

This project is open source. Use, modify, and distribute as needed.

## Support

For detailed technical documentation, see [REPOSITORY_INSPECTION.md](REPOSITORY_INSPECTION.md)

For issues or questions, please create a GitHub issue.

## About

Created as a practical solution for Red Hat Virtualization to OpenShift Virtualization migration planning. The tool combines data analysis, migration best practices, and interactive visualization to provide actionable insights for infrastructure teams.

---

**Current Version:** 1.0  
**Last Updated:** December 25, 2025
