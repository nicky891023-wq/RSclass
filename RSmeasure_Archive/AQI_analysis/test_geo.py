import geopandas as gpd
from shapely.geometry import Point
import folium

# Create a simple GeoDataFrame with two points
points = gpd.GeoDataFrame(
    {"name": ["NCDR", "NTU Civil Eng."], 
     "geometry": [Point(121.5654, 25.0330), Point(121.5413, 25.0174)]},
    crs="EPSG:4326")

print("GeoDataFrame created successfully!")
print(f"CRS: {points.crs}")
print(f"Rows: {len(points)}")
print(f"Geometry type: {points.geometry.geom_type.values}")

# Test CRS reprojection
points_twd97 = points.to_crs(epsg=3826)
print(f"\nReprojected to TWD97: {points_twd97.crs}")
print(f"TWD97 coordinates (first point):")
print(f"  X: {points_twd97.geometry.iloc[0].x:.2f} m")
print(f"  Y: {points_twd97.geometry.iloc[0].y:.2f} m")

# Test buffer
buffer_500m = points_twd97.buffer(500)
print(f"\n500m buffer area: {buffer_500m.iloc[0].area:.0f} sq meters")
print(f"Expected: ~785,398 sq meters (pi * 500^2)")

print("\n✅ All checks passed! You are ready for Week 3.")
