# NTN Stack Test Results Visualization Tools

## 🎯 Overview

This comprehensive test visualization toolkit provides advanced analysis and visualization capabilities for the NTN Stack project test results. The toolkit includes data collection, multi-format charting, trend analysis, performance regression detection, and interactive dashboards.

## ✨ Features

### 📊 Data Collection & Processing
- **Multi-format support**: JUnit XML, JSON, CSV, LCOV coverage
- **Automatic data parsing** and normalization
- **SQLite database** for persistent storage
- **Data validation** and cleaning
- **Real-time data collection**

### 📈 Visualization Engine
- **7 Chart Types**: Line, Bar, Heatmap, Scatter, Pie, Box, Radar
- **Interactive charts** with Plotly
- **Export capabilities**: PNG, SVG, HTML, PDF
- **Responsive design** for all screen sizes
- **Custom themes** and styling

### 🔍 Advanced Analysis
- **Trend Analysis**: Statistical regression, R² analysis
- **Anomaly Detection**: Z-score and IQR methods
- **Change Point Detection**: Statistical breakpoint identification
- **Performance Regression**: Automated regression alerts
- **Root Cause Analysis**: Intelligent failure categorization

### 💻 Interactive Dashboard
- **Real-time updates** via WebSocket
- **Flask-based web interface**
- **Responsive design**
- **Time range filtering**
- **Test type filtering**
- **Export functionality**

### 📄 Report Generation
- **HTML/PDF reports** with custom templates
- **Executive summaries**
- **Trend analysis reports**
- **Failure analysis** with recommendations
- **Multi-language support**

### 📊 Coverage Analysis
- **Coverage visualization** with heatmaps
- **Uncovered code hotspots**
- **Module comparison**
- **Improvement recommendations**
- **Trend tracking**

## 🚀 Quick Start

### Installation

```bash
# Navigate to tools directory
cd /home/sat/ntn-stack/tests/tools

# Install dependencies
pip install -r visualization_requirements_clean.txt

# Verify installation
python check_installation.py
```

### Basic Usage

#### 1. Launch Interactive Dashboard
```bash
python visualization_main.py dashboard --port 8050
```
Open your browser to `http://localhost:8050`

#### 2. Generate Reports
```bash
# HTML report
python visualization_main.py generate-report --format html

# PDF report
python visualization_main.py generate-report --format pdf
```

#### 3. Analyze Trends
```bash
# Analyze last 30 days
python visualization_main.py analyze-trends --days 30

# Analyze specific test type
python visualization_main.py analyze-trends --test-type e2e
```

#### 4. Collect Test Data
```bash
# Auto-collect from default paths
python visualization_main.py collect-data

# Collect from specific path
python visualization_main.py collect-data --source /path/to/test/results
```

#### 5. Coverage Analysis
```bash
# Analyze test coverage
python visualization_main.py analyze-coverage

# Coverage for specific module
python visualization_main.py analyze-coverage --module netstack
```

## 📁 File Structure

```
tests/tools/
├── visualization_main.py              # 🚀 Main CLI entry point
├── visualization_config.py            # ⚙️ Configuration management
├── test_data_collector.py             # 📥 Data collection engine
├── visualization_engine.py            # 📊 Chart generation engine  
├── advanced_report_generator.py       # 📄 Report generation system
├── dashboard_server.py               # 💻 Interactive dashboard
├── test_analysis_engine.py           # 📈 Trend analysis engine
├── coverage_analyzer.py              # 📊 Coverage analysis engine
├── visualization_requirements_clean.txt # 📦 Dependencies
├── check_installation.py             # 🔍 Installation checker
├── test_visualization_tools.py       # 🧪 Test suite
└── README.md                         # 📖 This documentation
```

## ⚙️ Configuration

### Configuration File
The system uses YAML configuration stored in `visualization_config.yaml`:

```yaml
dashboard:
  title: "NTN Stack Test Results Dashboard"
  theme: "light"
  auto_refresh: true
  refresh_interval: 30

data:
  source_paths:
    - "/home/sat/ntn-stack/tests/reports"
  formats: ["json", "xml", "csv"]
  retention_days: 30

charts:
  test_results_trend:
    chart_type: "line"
    title: "Test Results Trend"
    x_axis: "timestamp"
    y_axis: "success_rate"

analysis:
  trend_analysis:
    enabled: true
    window_size: 10
    detect_anomalies: true
```

### Environment Variables
- `VIZ_CONFIG_PATH`: Custom config file path
- `VIZ_DATA_PATH`: Custom data directory
- `VIZ_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 📊 Chart Types

### 1. Line Charts
Perfect for trend analysis and time series data
```python
from visualization_engine import VisualizationEngine
viz = VisualizationEngine()
viz.create_line_chart(data, x='timestamp', y='success_rate')
```

### 2. Bar Charts
Great for categorical comparisons
```python
viz.create_bar_chart(data, x='test_suite', y='duration')
```

### 3. Heatmaps
Ideal for coverage and correlation analysis
```python
viz.create_heatmap(coverage_data, title='Test Coverage Heatmap')
```

### 4. Scatter Plots
Useful for correlation analysis
```python
viz.create_scatter_plot(data, x='duration', y='success_rate')
```

### 5. Pie Charts
Perfect for proportion analysis
```python
viz.create_pie_chart(data, values='count', names='test_type')
```

### 6. Box Plots
Great for statistical distribution analysis
```python
viz.create_box_plot(data, y='response_time', x='test_type')
```

### 7. Radar Charts
Excellent for multi-dimensional comparisons
```python
viz.create_radar_chart(metrics_data, categories=['Performance', 'Quality', 'Coverage'])
```

## 🔍 Analysis Features

### Trend Analysis
- **Linear Regression**: Statistical trend calculation
- **R² Analysis**: Trend strength measurement
- **P-value Testing**: Statistical significance
- **Confidence Intervals**: Uncertainty quantification

### Anomaly Detection
- **Z-score Method**: Statistical outlier detection
- **IQR Method**: Interquartile range analysis
- **Seasonal Decomposition**: Pattern-based detection
- **Change Point Detection**: Breakpoint identification

### Performance Regression
- **Automated Detection**: Smart regression alerts
- **Multi-level Alerts**: Critical, High, Medium, Low
- **Root Cause Analysis**: Intelligent failure categorization
- **Recommendation Engine**: Actionable improvement suggestions

## 🌐 Dashboard Features

### Real-time Updates
- **WebSocket Connection**: Live data streaming
- **Auto-refresh**: Configurable refresh intervals
- **Push Notifications**: Instant alert delivery

### Interactive Features
- **Zoom & Pan**: Chart interaction capabilities
- **Filter Controls**: Dynamic data filtering
- **Export Options**: Multiple format support
- **Responsive Design**: Mobile-friendly interface

### Customization
- **Theme Selection**: Light/dark themes
- **Chart Configuration**: Customizable chart types
- **Layout Options**: Flexible dashboard layouts
- **Color Schemes**: Multiple color palettes

## 📄 Report Generation

### HTML Reports
- **Interactive Charts**: Embedded Plotly visualizations
- **Responsive Design**: Mobile-friendly layouts
- **Custom Styling**: Professional appearance
- **Navigation**: Easy section navigation

### PDF Reports
- **Professional Layout**: Publication-ready format
- **Chart Integration**: High-quality chart embedding
- **Custom Branding**: Logo and styling support
- **Multiple Sections**: Organized content structure

### Report Sections
1. **Executive Summary**: High-level overview
2. **Trend Analysis**: Statistical insights
3. **Performance Metrics**: KPI tracking
4. **Failure Analysis**: Root cause investigation
5. **Coverage Analysis**: Test coverage insights
6. **Recommendations**: Actionable improvements

## 🧪 Testing

### Run Tests
```bash
# Full test suite
python test_visualization_tools.py

# Specific test
python test_visualization_tools.py --test data_collection

# With coverage
python -m pytest test_visualization_tools.py --cov=.
```

### Test Coverage
- **Data Collection**: Import/export functionality
- **Chart Generation**: All chart types
- **Analysis Engine**: Statistical calculations
- **Dashboard**: API endpoints
- **Report Generation**: Format outputs

## 🔧 Troubleshooting

### Common Issues

#### 1. Installation Problems
```bash
# Check Python version (3.7+ required)
python --version

# Reinstall dependencies
pip install -r visualization_requirements_clean.txt --force-reinstall

# Verify installation
python check_installation.py
```

#### 2. Data Collection Issues
```bash
# Check data paths
python visualization_main.py status

# Manual data collection
python visualization_main.py collect-data --verbose
```

#### 3. Dashboard Not Loading
```bash
# Check port availability
netstat -tlnp | grep 8050

# Try different port
python visualization_main.py dashboard --port 8080
```

#### 4. Chart Generation Errors
```bash
# Check data format
python visualization_main.py validate-data

# Test with sample data
python test_visualization_tools.py --test charts
```

### Debugging
```bash
# Enable debug logging
export VIZ_LOG_LEVEL=DEBUG
python visualization_main.py dashboard

# Check logs
tail -f /tmp/visualization_debug.log
```

## 🚀 Advanced Usage

### Custom Data Sources
```python
from test_data_collector import TestDataCollector

collector = TestDataCollector()
collector.add_custom_parser('myformat', my_parser_function)
collector.collect_from_source('/custom/path')
```

### Custom Charts
```python
from visualization_engine import VisualizationEngine

viz = VisualizationEngine()
viz.register_chart_type('custom_chart', CustomChartClass)
chart = viz.create_chart('custom_chart', data, **options)
```

### Custom Analysis
```python
from test_analysis_engine import TestAnalysisEngine

analyzer = TestAnalysisEngine()
analyzer.add_analyzer('custom_metric', custom_analyzer_function)
results = analyzer.analyze_trends(data, analyzers=['custom_metric'])
```

## 📊 Performance Optimization

### Large Datasets
- **Streaming Processing**: Handle large files efficiently
- **Data Sampling**: Intelligent data reduction
- **Caching**: Smart result caching
- **Parallel Processing**: Multi-threaded operations

### Memory Management
- **Lazy Loading**: Load data on demand
- **Memory Monitoring**: Track memory usage
- **Garbage Collection**: Efficient cleanup
- **Data Compression**: Optimize storage

## 🔐 Security

### Data Protection
- **Input Validation**: Secure data parsing
- **Path Traversal Protection**: Safe file operations
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Safe HTML generation

### Best Practices
- Regular dependency updates
- Secure configuration management
- Access control for sensitive data
- Regular security audits

## 📈 Roadmap

### Short-term Goals
- [ ] Additional chart types (Sankey, Treemap)
- [ ] Enhanced statistical analysis
- [ ] Performance optimizations
- [ ] Mobile app interface

### Long-term Vision
- [ ] AI-powered insights
- [ ] Cloud deployment support
- [ ] Real-time streaming analytics
- [ ] Predictive analysis capabilities

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <repository>
cd tests/tools

# Install development dependencies
pip install -r visualization_requirements_clean.txt
pip install -e .

# Run tests
python test_visualization_tools.py
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Include unit tests for new features

## 📞 Support

### Getting Help
- Check the troubleshooting section
- Run diagnostic tools
- Review log files
- Test with sample data

### Reporting Issues
When reporting issues, include:
- Python version and OS
- Error messages and stack traces
- Data format and sample files
- Configuration settings
- Steps to reproduce

## 📜 License

This project is part of the NTN Stack system and follows the project's licensing terms.

---

**Last Updated**: June 7, 2025  
**Version**: 1.0.0  
**Compatibility**: Python 3.7+