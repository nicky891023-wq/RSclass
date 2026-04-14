import geopandas as gpd
import pandas as pd

# Test loading shelter data with GeoPandas
df = pd.read_csv("data/shelters_cleaned.csv")
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["經度"], df["緯度"]),
    crs="EPSG:4326")

print(f"Shelters loaded: {len(gdf)} rows")
print(f"CRS: {gdf.crs}")
print(gdf.head())

# Test spatial operations
print(f"\nGeometry type: {gdf.geometry.geom_type.iloc[0]}")
print(f"Bounds of all shelters: {gdf.total_bounds}")

# Test reprojection to TWD97
gdf_twd97 = gdf.to_crs(epsg=3826)
print(f"\nReprojected to TWD97: {gdf_twd97.crs}")
print(f"Sample TWD97 coordinates (first shelter):")
print(f"  X: {gdf_twd97.geometry.iloc[0].x:.2f} m")
print(f"  Y: {gdf_twd97.geometry.iloc[0].y:.2f} m")
