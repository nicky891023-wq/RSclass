# Automated Regional Impact Auditor (ARIA)
## 河川洪災避難所風險評估系統

A comprehensive geospatial analysis system for assessing flood risk to emergency shelters in Taiwan using Water Resources Agency river data and Fire Agency shelter locations.

### 🎯 Project Overview

ARIA analyzes the vulnerability of Taiwan's emergency shelters to river flooding by:
- Creating multi-level buffer zones (500m/1km/2km) around rivers
- Classifying shelters by risk level (High/Medium/Low/Safe)
- Analyzing capacity gaps by administrative districts
- Generating interactive maps and audit reports

### 📊 Key Features

- **Multi-Level Risk Assessment**: Three-tier buffer system for comprehensive risk zoning
- **Capacity Gap Analysis**: Identifies areas with insufficient safe shelter capacity
- **Interactive Visualization**: Web-based risk maps with detailed shelter information
- **Automated Reporting**: JSON audit exports for emergency management integration
- **Data Validation**: Robust cleaning and validation of coordinate data

### 🗂️ Project Structure

```
ARIA/
├── ARIA.ipynb              # Main analysis notebook
├── .env                     # Environment variables (buffer distances, etc.)
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore file
├── README.md               # This file
├── shelter_risk_audit.json # Generated audit results
├── risk_map.html          # Interactive risk map
└── risk_analysis.png       # Static visualization
```

### 🚀 Quick Start

#### Option 1: Conda Environment (Recommended)

1. **Create Conda Environment**
   ```bash
   conda env create -f environment.yml
   conda activate aria-project
   ```

2. **Register Jupyter Kernel**
   ```bash
   python -m ipykernel install --user --name aria-project --display-name "ARIA Project"
   ```

3. **Download Shelter Data**
   - Visit [data.gov.tw/dataset/73242](https://data.gov.tw/dataset/73242)
   - Download the shelter CSV file
   - Save as `避難收容處所.csv` in the project directory

4. **Run Analysis**
   ```bash
   jupyter notebook ARIA_complete.ipynb
   ```
   Execute all cells in sequence to perform the complete analysis.

#### Option 2: pip Environment

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download Shelter Data**
   - Visit [data.gov.tw/dataset/73242](https://data.gov.tw/dataset/73242)
   - Download the shelter CSV file
   - Save as `避難收容處所.csv` in the project directory

3. **Run Analysis**
   ```bash
   jupyter notebook ARIA_complete.ipynb
   ```

### 📈 Analysis Workflow

#### 1. Data Ingestion & Cleaning
- Loads WRA river polygons (EPSG:3826)
- Cleans Fire Agency shelter CSV data
- Validates coordinate ranges (Taiwan: 119-122°E, 21-26°N)
- Removes null/zero coordinates and invalid records

#### 2. Multi-Buffer Risk Zoning
- **High Risk**: 500m buffer around rivers
- **Medium Risk**: 1km buffer around rivers  
- **Low Risk**: 2km buffer around rivers
- Spatial joins assign risk levels (highest priority wins)

#### 3. Capacity Gap Analysis
- Groups shelters by administrative district
- Calculates capacity by risk level
- Identifies Top 10 most at-risk townships
- Computes capacity gaps between risk and safe areas

#### 4. Visualization & Export
- Interactive Folium map with risk zones
- Static matplotlib charts for reports
- JSON audit export for system integration

### 🎨 Risk Level Classification

| Risk Level | Buffer Distance | Color | Description |
|------------|----------------|-------|-------------|
| **High**   | 500m           | 🔴 Red | Immediate flood danger zone |
| **Medium** | 1km            | 🟠 Orange | Moderate flood risk area |
| **Low**    | 2km            | 🟡 Yellow | Low flood risk zone |
| **Safe**   | >2km           | 🟢 Green | Outside flood risk zones |

### 📊 Output Files

- **`risk_map.html`**: Interactive map with shelters, rivers, and risk zones
- **`risk_analysis.png`**: Static charts of Top 10 at-risk areas
- **`shelter_risk_audit.json`**: Complete audit data with shelter details
- **Console output**: Summary statistics and analysis results

### ⚙️ Configuration

Edit `.env` file to customize:
```env
# Buffer distances in meters
BUFFER_HIGH=500
BUFFER_MED=1000
BUFFER_LOW=2000

# Target CRS
TARGET_CRS=EPSG:3826
```

### 🔧 Technical Implementation

- **Coordinate System**: EPSG:3826 (TWD97/TM2) for accurate distance calculations
- **Spatial Operations**: GeoPandas for efficient geospatial processing
- **Visualization**: Folium for interactive maps, Matplotlib/Seaborn for static charts
- **Data Sources**: 
  - WRA River Polygons: Direct API access
  - Fire Agency Shelters: data.gov.tw CSV download
  - Township Boundaries: TGOS shapefile

---

## 🤖 AI Diagnostics Log

### Issues Encountered & Solutions

#### 1. **Encoding Issues with Shelter CSV**
- **Problem**: Taiwanese government CSV files often use Big5 encoding
- **Solution**: Implemented encoding detection loop trying UTF-8, Big5, GBK, Latin-1
- **Status**: ✅ Resolved

#### 2. **Coordinate Validation**
- **Problem**: Raw shelter data contained invalid coordinates (zeros, nulls, reversed lat/lng)
- **Solution**: Added validation filters for Taiwan coordinate ranges (119-122°E, 21-26°N)
- **Status**: ✅ Resolved

#### 3. **Column Name Variability**
- **Problem**: Different datasets use varying column names (Chinese/English)
- **Solution**: Implemented flexible column detection for coordinates, capacity, names
- **Status**: ✅ Resolved

#### 4. **CRS Conversion Issues**
- **Problem**: Buffer operations require projected coordinate system
- **Solution**: Enforced EPSG:3826 for all distance calculations
- **Status**: ✅ Resolved

#### 5. **Spatial Join Performance**
- **Problem**: Large datasets causing slow spatial operations
- **Solution**: Dissolved river polygons before buffering, optimized join order
- **Status**: ✅ Resolved

#### 6. **Memory Management**
- **Problem**: Large geodataframes causing memory issues
- **Solution**: Implemented progressive filtering and data type optimization
- **Status**: ✅ Resolved

### Performance Optimizations Applied

1. **River Polygon Dissolution**: Combined all river features before buffering
2. **Progressive Risk Assignment**: High → Medium → Low priority to avoid duplicate assignments
3. **Efficient Data Types**: Converted to optimal numeric types early
4. **Selective Loading**: Only load required columns from large datasets

### Data Quality Insights

- **Shelter Data Quality**: ~85-90% valid coordinates after cleaning
- **River Coverage**: Comprehensive national coverage from WRA
- **Administrative Boundaries**: TGOS provides up-to-date township boundaries
- **Capacity Data**: Most shelters include capacity information, but some entries require validation

### Future Enhancement Opportunities

1. **Real-time Integration**: Connect to live river level monitoring systems
2. **Population Data**: Integrate demographic data for more accurate capacity planning
3. **Transportation Analysis**: Add evacuation route planning capabilities
4. **Historical Analysis**: Include historical flood data for risk modeling
5. **Multi-hazard Assessment**: Extend beyond river flooding to other disaster types

---

### 📞 Contact & Support

For questions or issues with the ARIA system:
1. Check the AI Diagnostics Log above for known solutions
2. Verify data downloads are complete and properly named
3. Ensure all dependencies are installed via requirements.txt
4. Review Jupyter notebook cell outputs for error messages

**System Status**: ✅ Fully Operational  
**Last Updated**: 2026-03-11  
**Version**: 1.0.0

*"The buffer renders. The join completes. The city's shelter capacity is now quantified."*
