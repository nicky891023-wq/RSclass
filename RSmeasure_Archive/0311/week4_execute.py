#!/usr/bin/env python
# coding: utf-8

"""
Week 4: Vector & Raster Integration
火速執行版本 - 完整實驗
"""

import geopandas as gpd
import rioxarray as rxr
from rasterstats import zonal_stats
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point, Polygon
import warnings
import xarray as xr
from glob import glob
import os

warnings.filterwarnings('ignore')

print("🚀 Week 4: Vector & Raster Integration - 火速執行")
print("=" * 60)

# 1. Vector Aggregation (Review)
print("\n📊 Step 1: Vector Aggregation")
print("-" * 30)

try:
    townships = gpd.read_file('TOWN_MOI_1120317.shp')
    print(f"✅ Loaded {len(townships)} townships")
    print(f"CRS: {townships.crs}")
    
    counties = townships.dissolve(by='COUNTYNAME', aggfunc='first')
    print(f"✅ Dissolved to {len(counties)} counties")
except Exception as e:
    print(f"❌ Error loading townships: {e}")
    exit(1)

# 2. Raster Data Fundamentals
print("\n🗺️ Step 2: Raster Data Fundamentals")
print("-" * 30)

# Search for DEM files
dem_files = glob('**/*.tif', recursive=True) + glob('**/*.tiff', recursive=True)
dem_files.extend(glob('**/*dem*', recursive=True))
dem_files.extend(glob('**/*DEM*', recursive=True))

if dem_files:
    print(f"Found DEM files: {dem_files[:3]}...")  # Show first 3
    dem_file = dem_files[0]
else:
    print("❌ No DEM files found. Creating sample DEM...")
    
    # Create sample DEM for Hualien area
    x = np.linspace(120.8, 121.8, 100)
    y = np.linspace(23.0, 24.0, 100)
    
    xx, yy = np.meshgrid(x, y)
    elevation = 100 + 2000 * np.exp(-((xx-121.3)**2 + (yy-23.6)**2) / 0.1) + \
                500 * np.sin(xx*10) * np.cos(yy*10) + \
                np.random.normal(0, 50, xx.shape)
    
    dem = xr.DataArray(
        elevation,
        coords={'x': x, 'y': y},
        dims=['y', 'x'],
        attrs={'crs': 'EPSG:4326'}
    )
    
    dem.rio.to_raster('hualien_sample_dem.tif')
    print("✅ Created sample DEM: hualien_sample_dem.tif")
    dem_file = 'hualien_sample_dem.tif'

# Load DEM
try:
    dem = rxr.open_rasterio(dem_file)
    print(f"✅ Loaded DEM: {dem.shape}")
    print(f"CRS: {dem.rio.crs}")
    print(f"Elevation range: {dem.min().values:.1f} - {dem.max().values:.1f}m")
except Exception as e:
    print(f"❌ Error loading DEM: {e}")
    exit(1)

# 3. Compute Terrain Slope
print("\n⛰️ Step 3: Compute Terrain Slope")
print("-" * 30)

def compute_slope(dem_data, pixel_size_x, pixel_size_y):
    dy, dx = np.gradient(dem_data, pixel_size_y, pixel_size_x)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    return slope_deg

# Get pixel size
res_x, res_y = abs(dem.rio.resolution()[0]), abs(dem.rio.resolution()[1])
pixel_size_x_m = res_x * 111320  # Convert to meters
pixel_size_y_m = res_y * 111320

# Compute slope
slope_deg = compute_slope(dem.values.squeeze(), pixel_size_x_m, pixel_size_y_m)
print(f"✅ Slope computed: {np.nanmin(slope_deg):.2f} - {np.nanmax(slope_deg):.2f}°")

# Create slope xarray
slope_xr = xr.DataArray(
    slope_deg[np.newaxis, :, :],  # Add band dimension to match DEM
    coords=dem.coords,
    dims=dem.dims,
    attrs={'crs': dem.rio.crs, 'units': 'degrees'}
)

# 4. Zonal Statistics
print("\n📈 Step 4: Zonal Statistics")
print("-" * 30)

# Prepare zones for analysis
try:
    hualien_towns = townships[townships['COUNTYNAME'].str.contains('花蓮', na=False)].copy()
    if len(hualien_towns) == 0:
        raise ValueError("No Hualien found")
except:
    print("Creating sample zones...")
    bounds = dem.rio.bounds()
    sample_polys = [
        Polygon([(bounds[0], bounds[1]), (bounds[2], bounds[1]), 
                (bounds[2], bounds[3]), (bounds[0], bounds[3])]),
        Polygon([(bounds[0], bounds[1]), (bounds[0]+(bounds[2]-bounds[0])/2, bounds[1]),
                (bounds[0]+(bounds[2]-bounds[0])/2, bounds[1]+(bounds[3]-bounds[1])/2),
                (bounds[0], bounds[1]+(bounds[3]-bounds[1])/2)]),
        Polygon([(bounds[0]+(bounds[2]-bounds[0])/2, bounds[1]+(bounds[3]-bounds[1])/2), 
                (bounds[2], bounds[1]+(bounds[3]-bounds[1])/2),
                (bounds[2], bounds[3]), (bounds[0]+(bounds[2]-bounds[0])/2, bounds[3])])
    ]
    
    hualien_towns = gpd.GeoDataFrame({
        'TOWNNAME': ['Full Area', 'West Zone', 'East Zone'],
        'COUNTYNAME': ['Sample', 'Sample', 'Sample'],
        'geometry': sample_polys
    }, crs=dem.rio.crs)

print(f"✅ Using {len(hualien_towns)} zones for analysis")

# Zonal statistics with rasterstats
slope_xr.rio.to_raster('temp_slope.tif')

# Ensure CRS matches
hualien_towns = hualien_towns.to_crs(dem.rio.crs)

elevation_stats = zonal_stats(
    hualien_towns, 
    dem_file, 
    stats=['count', 'mean', 'min', 'max', 'std', 'median'],
    geojson_out=True
)

slope_stats = zonal_stats(
    hualien_towns,
    'temp_slope.tif',
    stats=['count', 'mean', 'min', 'max', 'std', 'median'],
    geojson_out=True
)

elevation_gdf = gpd.GeoDataFrame.from_features(elevation_stats)
slope_gdf = gpd.GeoDataFrame.from_features(slope_stats)

print("✅ Zonal statistics computed")

# 5. Visualization
print("\n🎨 Step 5: Creating Visualizations")
print("-" * 30)

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# DEM with boundaries
dem.plot(ax=ax1, cmap='terrain', robust=True, alpha=0.8)
hualien_towns.plot(ax=ax1, facecolor='none', edgecolor='red', linewidth=2)
ax1.set_title('DEM with Zone Boundaries')

# Slope with boundaries
slope_xr.plot(ax=ax2, cmap='YlOrRd', robust=True, alpha=0.8, vmin=0, vmax=45)
hualien_towns.plot(ax=ax2, facecolor='none', edgecolor='black', linewidth=2)
ax2.set_title('Slope with Zone Boundaries')

# Elevation statistics
elevation_df = pd.DataFrame([{
    'town': hualien_towns.iloc[i]['TOWNNAME'],
    'mean_elevation': feat['properties']['mean']
} for i, feat in enumerate(elevation_stats)])

elevation_df.set_index('town')['mean_elevation'].plot(kind='bar', ax=ax3, color='brown')
ax3.set_title('Mean Elevation by Zone')
ax3.set_ylabel('Elevation (m)')
ax3.tick_params(axis='x', rotation=45)

# Slope statistics
slope_df = pd.DataFrame([{
    'town': hualien_towns.iloc[i]['TOWNNAME'],
    'mean_slope': feat['properties']['mean']
} for i, feat in enumerate(slope_stats)])

slope_df.set_index('town')['mean_slope'].plot(kind='bar', ax=ax4, color='orange')
ax4.set_title('Mean Slope by Zone')
ax4.set_ylabel('Slope (degrees)')
ax4.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('week4_vector_raster_integration.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Saved visualization: week4_vector_raster_integration.png")

# 6. Summary
print("\n📊 Summary & Results")
print("=" * 60)
print(f"✅ Vector Aggregation: {len(townships)} townships → {len(counties)} counties")
print(f"✅ Raster Analysis: DEM shape {dem.shape}, elevation range {dem.min().values:.1f}-{dem.max().values:.1f}m")
print(f"✅ Slope Analysis: {np.nanmin(slope_deg):.2f}-{np.nanmax(slope_deg):.2f}°")
print(f"✅ Zonal Statistics: {len(hualien_towns)} zones analyzed")

print(f"\n📈 Key Results:")
print(f"- Elevation stats computed for {len(elevation_df)} zones")
print(f"- Slope stats computed for {len(slope_df)} zones")
print(f"- Visualization saved as PNG")

print(f"\n🎓 Concepts Mastered:")
print("1. Vector Aggregation (dissolve & groupby)")
print("2. Raster as NumPy Arrays with spatial metadata")
print("3. Terrain slope computation from DEM")
print("4. Zonal statistics (raster → vector)")

print(f"\n🚀 Week 4 Complete! Ready for GitHub upload.")

# Clean up temporary files
if os.path.exists('temp_slope.tif'):
    os.remove('temp_slope.tif')
    print("✅ Cleaned up temporary files")
