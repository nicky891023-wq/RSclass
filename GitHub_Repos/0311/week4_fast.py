#!/usr/bin/env python
# coding: utf-8

"""
Week 4: Vector & Raster Integration - 火速執行版本
"""

import geopandas as gpd
import rioxarray as rxr
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

# 1. Vector Aggregation
print("\n📊 Step 1: Vector Aggregation")
print("-" * 30)

try:
    townships = gpd.read_file('TOWN_MOI_1120317.shp')
    print(f"✅ Loaded {len(townships)} townships")
    counties = townships.dissolve(by='COUNTYNAME', aggfunc='first')
    print(f"✅ Dissolved to {len(counties)} counties")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 2. Raster Data
print("\n🗺️ Step 2: Raster Data Fundamentals")
print("-" * 30)

# Create sample DEM
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

dem.rio.to_raster('week4_dem.tif')
print("✅ Created sample DEM: week4_dem.tif")

# Load DEM
dem = rxr.open_rasterio('week4_dem.tif')
print(f"✅ DEM shape: {dem.shape}")
print(f"✅ Elevation range: {dem.min().values:.1f} - {dem.max().values:.1f}m")

# 3. Compute Slope
print("\n⛰️ Step 3: Compute Terrain Slope")
print("-" * 30)

def compute_slope(dem_data, pixel_size_x, pixel_size_y):
    dy, dx = np.gradient(dem_data, pixel_size_y, pixel_size_x)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    return slope_deg

res_x, res_y = abs(dem.rio.resolution()[0]), abs(dem.rio.resolution()[1])
pixel_size_x_m = res_x * 111320
pixel_size_y_m = res_y * 111320

slope_deg = compute_slope(dem.values.squeeze(), pixel_size_x_m, pixel_size_y_m)
print(f"✅ Slope range: {np.nanmin(slope_deg):.2f} - {np.nanmax(slope_deg):.2f}°")

# 4. Zonal Statistics (rioxarray method)
print("\n📈 Step 4: Zonal Statistics")
print("-" * 30)

# Create sample zones
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

zones = gpd.GeoDataFrame({
    'zone_name': ['Full Area', 'West Zone', 'East Zone'],
    'geometry': sample_polys
}, crs=dem.rio.crs)

print(f"✅ Created {len(zones)} analysis zones")

def compute_zonal_stats(vector_gdf, raster_xr):
    """Compute zonal statistics using rioxarray clipping"""
    stats = []
    
    for idx, row in vector_gdf.iterrows():
        # Clip raster to polygon
        clipped = raster_xr.rio.clip([row.geometry], raster_xr.rio.crs, drop=True)
        
        # Remove nodata values
        valid_data = clipped.values[~np.isnan(clipped.values)]
        
        if len(valid_data) > 0:
            stats.append({
                'zone': row['zone_name'],
                'count': len(valid_data),
                'mean': np.mean(valid_data),
                'min': np.min(valid_data),
                'max': np.max(valid_data),
                'std': np.std(valid_data),
                'median': np.median(valid_data)
            })
        else:
            stats.append({
                'zone': row['zone_name'],
                'count': 0,
                'mean': np.nan,
                'min': np.nan,
                'max': np.nan,
                'std': np.nan,
                'median': np.nan
            })
    
    return pd.DataFrame(stats)

# Compute stats
elevation_stats = compute_zonal_stats(zones, dem)

# Create slope DataArray
slope_xr = xr.DataArray(
    slope_deg[np.newaxis, :, :],
    coords=dem.coords,
    dims=dem.dims,
    attrs={'crs': dem.rio.crs, 'units': 'degrees'}
)

slope_stats = compute_zonal_stats(zones, slope_xr)

print("✅ Zonal statistics computed")
print("\nElevation Statistics:")
print(elevation_stats.round(2))
print("\nSlope Statistics:")
print(slope_stats.round(2))

# 5. Visualization
print("\n🎨 Step 5: Creating Visualizations")
print("-" * 30)

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# DEM with boundaries
dem.plot(ax=ax1, cmap='terrain', robust=True, alpha=0.8)
zones.plot(ax=ax1, facecolor='none', edgecolor='red', linewidth=2)
ax1.set_title('DEM with Zone Boundaries')
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')

# Slope with boundaries
slope_xr.plot(ax=ax2, cmap='YlOrRd', robust=True, alpha=0.8, vmin=0, vmax=45)
zones.plot(ax=ax2, facecolor='none', edgecolor='black', linewidth=2)
ax2.set_title('Slope with Zone Boundaries')
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')

# Elevation statistics
elevation_stats.set_index('zone')['mean'].plot(kind='bar', ax=ax3, color='brown')
ax3.set_title('Mean Elevation by Zone')
ax3.set_ylabel('Elevation (m)')
ax3.tick_params(axis='x', rotation=45)

# Slope statistics
slope_stats.set_index('zone')['mean'].plot(kind='bar', ax=ax4, color='orange')
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
print(f"✅ Raster Analysis: DEM shape {dem.shape}, elevation {dem.min().values:.1f}-{dem.max().values:.1f}m")
print(f"✅ Slope Analysis: {np.nanmin(slope_deg):.2f}-{np.nanmax(slope_deg):.2f}°")
print(f"✅ Zonal Statistics: {len(zones)} zones analyzed")

print(f"\n🎓 Concepts Mastered:")
print("1. Vector Aggregation (dissolve & groupby)")
print("2. Raster as NumPy Arrays with spatial metadata")
print("3. Terrain slope computation from DEM")
print("4. Zonal statistics (rioxarray method)")

print(f"\n📁 Generated Files:")
print("- week4_dem.tif")
print("- week4_vector_raster_integration.png")
print("- week4_execute.py")

print(f"\n🚀 Week 4 Complete! Ready for GitHub upload.")
