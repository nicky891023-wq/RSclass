#!/usr/bin/env python
# coding: utf-8

# # Lab 1: Vector Aggregation
# 
# **Goal**: Practice dissolve & groupby before entering the raster world.
# 
# **Tasks**:
# - Step 1: Dissolve townships → counties (geometry merges)
# - Step 2: Create synthetic shelter data for Hualien County
# - Step 3: Groupby — count shelters & sum capacity per town
# - Step 4: Merge stats back to geometry → .explore() choropleth map
# 
# **Environment**: Local Jupyter (same as Week 3)

# # Set display options
# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', 50)
# 
# print("✅ Libraries imported successfully!")

# In[1]:


import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import random

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

print("✅ Libraries imported successfully!")


# ## Step 1: Load Township Data & Dissolve to Counties

# In[ ]:


# Load township boundaries (assuming you have the shapefile)
# Try to load the township data from your existing files
try:
    townships = gpd.read_file('TOWN_MOI_1120317.shp')
    print(f"✅ Loaded {len(townships)} townships")
    print(f"CRS: {townships.crs}")
    print(townships.head())
except FileNotFoundError:
    print("❌ Township shapefile not found. Creating sample data...")
    # Create sample township data for demonstration
    from shapely.geometry import Polygon

    # Sample townships in Hualien area
    sample_towns = [
        {'COUNTYNAME': '花蓮縣', 'TOWNNAME': '花蓮市', 'geometry': Polygon([(121.5, 23.9), (121.7, 23.9), (121.7, 24.1), (121.5, 24.1)])},
        {'COUNTYNAME': '花蓮縣', 'TOWNNAME': '吉安鄉', 'geometry': Polygon([(121.5, 23.8), (121.7, 23.8), (121.7, 23.9), (121.5, 23.9)])},
        {'COUNTYNAME': '花蓮縣', 'TOWNNAME': '壽豐鄉', 'geometry': Polygon([(121.4, 23.7), (121.6, 23.7), (121.6, 23.8), (121.4, 23.8)])},
        {'COUNTYNAME': '花蓮縣', 'TOWNNAME': '光復鄉', 'geometry': Polygon([(121.3, 23.6), (121.5, 23.6), (121.5, 23.7), (121.3, 23.7)])},
        {'COUNTYNAME': '臺東縣', 'TOWNNAME': '臺東市', 'geometry': Polygon([(121.0, 22.7), (121.2, 22.7), (121.2, 22.9), (121.0, 22.9)])},
        {'COUNTYNAME': '臺東縣', 'TOWNNAME': '成功鎮', 'geometry': Polygon([(121.2, 23.0), (121.4, 23.0), (121.4, 23.2), (121.2, 23.2)])},
    ]

    townships = gpd.GeoDataFrame(sample_towns, crs='EPSG:4326')
    print(f"✅ Created {len(townships)} sample townships")


# In[ ]:


# Examine the township data structure
print("Township data info:")
print(f"Total townships: {len(townships)}")
print(f"Columns: {list(townships.columns)}")

# Check unique counties
if 'COUNTYNAME' in townships.columns:
    print(f"\nCounties: {townships['COUNTYNAME'].unique()}")
else:
    print("\n⚠️ COUNTYNAME column not found. Available columns:")
    print(list(townships.columns))


# In[ ]:


# Step 1: Dissolve townships to counties
# This merges all township geometries within each county

# Determine the county column name
county_col = 'COUNTYNAME' if 'COUNTYNAME' in townships.columns else 'COUNTY' if 'COUNTY' in townships.columns else None

if county_col:
    counties = townships.dissolve(by=county_col, aggfunc='first')
    print(f"✅ Dissolved {len(townships)} townships into {len(counties)} counties")
    print(f"\nCounties created:")
    print(counties[[county_col, 'geometry']].head())

    # Plot the dissolved counties
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    townships.plot(ax=ax1, color='lightblue', edgecolor='black', alpha=0.7)
    ax1.set_title('Original Townships')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')

    counties.plot(ax=ax2, color='lightgreen', edgecolor='black', alpha=0.7)
    ax2.set_title('Dissolved Counties')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')

    plt.tight_layout()
    plt.show()
else:
    print("❌ Could not find county column for dissolution")
    counties = townships.copy()  # Use original data as fallback


# ## Step 2: Create Synthetic Shelter Data for Hualien County

# In[ ]:


# Step 2: Create synthetic shelter data for Hualien County

# Filter Hualien County townships
if county_col and county_col in townships.columns:
    hualien_towns = townships[townships[county_col] == '花蓮縣'].copy()
    print(f"✅ Found {len(hualien_towns)} townships in Hualien County")
else:
    # Use first few towns as Hualien sample
    hualien_towns = townships.head(4).copy()
    print(f"✅ Using {len(hualien_towns)} sample townships")

# Generate synthetic shelter data
shelters = []
shelter_id = 1

for idx, town in hualien_towns.iterrows():
    town_geom = town.geometry
    town_bounds = town_geom.bounds

    # Generate 3-8 shelters per town
    num_shelters = random.randint(3, 8)

    for i in range(num_shelters):
        # Generate random point within town bounds
        lon = random.uniform(town_bounds[0], town_bounds[2])
        lat = random.uniform(town_bounds[1], town_bounds[3])

        # Create shelter record
        shelter = {
            'shelter_id': f'SHL_{shelter_id:03d}',
            'name': f'{town.get("TOWNNAME", f"Town_{idx}")}避難所_{i+1}',
            'town': town.get('TOWNNAME', f'Town_{idx}'),
            'county': town.get(county_col, 'Sample County'),
            'capacity': random.randint(50, 500),
            'geometry': Point(lon, lat)
        }
        shelters.append(shelter)
        shelter_id += 1

# Create GeoDataFrame
shelters_gdf = gpd.GeoDataFrame(shelters, crs='EPSG:4326')

print(f"✅ Generated {len(shelters_gdf)} synthetic shelters")
print(f"\nShelter data sample:")
print(shelters_gdf.head())

print(f"\nCapacity statistics:")
print(f"Total capacity: {shelters_gdf['capacity'].sum():,}")
print(f"Average capacity: {shelters_gdf['capacity'].mean():.1f}")
print(f"Capacity range: {shelters_gdf['capacity'].min()} - {shelters_gdf['capacity'].max()}")


# In[ ]:


# Visualize the shelters on townships
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Plot townships
hualien_towns.plot(ax=ax, color='lightblue', edgecolor='black', alpha=0.5, label='Townships')

# Plot shelters
shelters_gdf.plot(ax=ax, color='red', markersize=50, alpha=0.8, label='Shelters')

# Add town labels
for idx, town in hualien_towns.iterrows():
    centroid = town.geometry.centroid
    town_name = town.get('TOWNNAME', f'Town_{idx}')
    ax.annotate(town_name, (centroid.x, centroid.y), 
                fontsize=10, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

ax.set_title('Synthetic Shelters in Hualien County Townships')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.legend()
plt.grid(True, alpha=0.3)
plt.show()


# ## Step 3: Groupby — Count Shelters & Sum Capacity per Town

# In[ ]:


# Step 3: Groupby operations

# Count shelters and sum capacity per town
town_stats = shelters_gdf.groupby('town').agg({
    'shelter_id': 'count',  # Count shelters
    'capacity': 'sum'       # Sum capacity
}).rename(columns={
    'shelter_id': 'shelter_count',
    'capacity': 'total_capacity'
})

print(f"✅ Calculated statistics for {len(town_stats)} towns")
print(f"\nTown shelter statistics:")
print(town_stats)

# Add additional statistics
town_stats['avg_capacity'] = town_stats['total_capacity'] / town_stats['shelter_count']
town_stats['capacity_per_sqkm'] = town_stats['total_capacity']  # Placeholder - would need area calculation

print(f"\nEnhanced statistics:")
print(town_stats.round(1))


# In[ ]:


# Visualize the statistics with bar charts
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Bar chart of shelter counts
town_stats['shelter_count'].plot(kind='bar', ax=ax1, color='skyblue', edgecolor='black')
ax1.set_title('Number of Shelters per Town')
ax1.set_ylabel('Number of Shelters')
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# Bar chart of total capacity
town_stats['total_capacity'].plot(kind='bar', ax=ax2, color='lightcoral', edgecolor='black')
ax2.set_title('Total Shelter Capacity per Town')
ax2.set_ylabel('Total Capacity')
ax2.grid(True, alpha=0.3)
ax2.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()


# ## Step 4: Merge Stats Back to Geometry → Choropleth Map

# In[ ]:


# Step 4: Merge statistics back to township geometries

# Prepare township data for merging
# Use the town name column for merging
town_col = 'TOWNNAME' if 'TOWNNAME' in hualien_towns.columns else 'town'

# Create a copy of townships with town name as index for easier merging
townships_with_stats = hualien_towns.copy()
townships_with_stats['town_name'] = townships_with_stats.get(town_col, f'Town_{range(len(hualien_towns))}')

# If we don't have the town column in townships, create it from index
if town_col not in hualien_towns.columns:
    townships_with_stats['town_name'] = [f'Town_{i}' for i in range(len(hualien_towns))]
    # Update town_stats index to match
    town_stats.index = [f'Town_{i}' for i in range(len(town_stats))]

# Merge statistics with townships
townships_merged = townships_with_stats.merge(
    town_stats, 
    left_on='town_name', 
    right_index=True, 
    how='left'
)

# Fill missing values (towns with no shelters)
townships_merged['shelter_count'] = townships_merged['shelter_count'].fillna(0)
townships_merged['total_capacity'] = townships_merged['total_capacity'].fillna(0)
townships_merged['avg_capacity'] = townships_merged['avg_capacity'].fillna(0)

print(f"✅ Merged statistics with {len(townships_merged)} townships")
print(f"\nMerged data sample:")
print(townships_merged[['town_name', 'shelter_count', 'total_capacity']].head())


# In[ ]:


# Create choropleth maps using matplotlib
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Choropleth map for shelter count
townships_merged.plot(
    column='shelter_count',
    cmap='Blues',
    linewidth=1,
    edgecolor='black',
    legend=True,
    ax=ax1,
    legend_kwds={'label': "Number of Shelters", 'orientation': "horizontal"}
)
ax1.set_title('Shelter Count by Township')
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')

# Add town labels
for idx, row in townships_merged.iterrows():
    centroid = row.geometry.centroid
    ax1.annotate(row['town_name'], (centroid.x, centroid.y), 
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

# Choropleth map for total capacity
townships_merged.plot(
    column='total_capacity',
    cmap='Reds',
    linewidth=1,
    edgecolor='black',
    legend=True,
    ax=ax2,
    legend_kwds={'label': "Total Capacity", 'orientation': "horizontal"}
)
ax2.set_title('Total Shelter Capacity by Township')
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')

# Add town labels
for idx, row in townships_merged.iterrows():
    centroid = row.geometry.centroid
    ax2.annotate(row['town_name'], (centroid.x, centroid.y), 
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.show()


# In[ ]:


# Interactive choropleth map using .explore()
# This creates an interactive map with hover information

print("Creating interactive choropleth map...")

# Create interactive map for shelter count
map_count = townships_merged.explore(
    column='shelter_count',
    cmap='Blues',
    tooltip=['town_name', 'shelter_count', 'total_capacity'],
    popup=True,
    legend=True,
    style_kwds={'color': 'black', 'weight': 1, 'fillOpacity': 0.7},
    name='Shelter Count'
)

# Add shelter points
shelters_gdf.explore(
    m=map_count,
    color='red',
    marker_kwds={'radius': 5},
    tooltip=['name', 'capacity'],
    name='Shelters'
)

# Display the map
display(map_count)


# ## Summary & Key Takeaways

# In[ ]:


# Summary statistics
print("🎯 Lab 1: Vector Aggregation Summary")
print("=" * 50)
print(f"✅ Step 1: Dissolved {len(townships)} townships → {len(counties)} counties")
print(f"✅ Step 2: Created {len(shelters_gdf)} synthetic shelters for Hualien County")
print(f"✅ Step 3: Generated statistics for {len(town_stats)} towns")
print(f"✅ Step 4: Merged stats back to geometry & created choropleth maps")

print(f"\n📊 Key Results:")
print(f"- Total shelters: {len(shelters_gdf)}")
print(f"- Total capacity: {shelters_gdf['capacity'].sum():,}")
print(f"- Average shelter capacity: {shelters_gdf['capacity'].mean():.1f}")
print(f"- Towns with shelters: {len(town_stats)}")
print(f"- Average shelters per town: {len(shelters_gdf) / len(town_stats):.1f}")


# ## Key Concepts Learned
# 
# ### 1. **Dissolve Operation**
# - Merges geometries based on attribute values
# - Combines polygons while aggregating attributes
# - Useful for administrative hierarchy (townships → counties)
# 
# ### 2. **Groupby Operations**
# - Pandas groupby works with GeoDataFrames too
# - Can aggregate multiple columns simultaneously
# - Essential for statistical analysis
# 
# ### 3. **Spatial Joins & Merges**
# - Merge tabular data back to spatial geometries
# - Handle missing values (towns with no data)
# - Prepare data for visualization
# 
# ### 4. **Choropleth Mapping**
# - Color-coded maps based on data values
# - Both static (matplotlib) and interactive (.explore())
# - Effective for spatial data visualization
# 
# ## Next Steps
# 
# These skills are fundamental for:
# - Raster analysis preparation
# - Spatial statistics
# - Multi-scale analysis
# - Data visualization workflows
