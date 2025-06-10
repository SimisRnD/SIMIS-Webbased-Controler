import pyproj

# Create a projection for lat/lon to UTM
wgs84 = pyproj.CRS("EPSG:4326")  # WGS84 GPS coordinates

# UTM projection (zone 33N as an example)
utm = pyproj.CRS("EPSG:32633")  # UTM Zone 33N

# Create transformers
transformerll2utm = pyproj.Transformer.from_crs(wgs84, utm)  # Lat/Lon -> UTM
transformerutm2ll = pyproj.Transformer.from_crs(utm, wgs84)  # UTM -> Lat/Lon

def latLong2UTM(lat, lon):
    return transformerll2utm.transform(lat, lon)  # lat, lon order for Pyproj

def UTM2LonLat(utm_e, utm_n):
    return transformerutm2ll.transform(utm_e, utm_n)

# # Example usage
# lon, lat = 12.4924, 41.8902  # Example: Rome, Italy
# utm_e, utm_n = latLong2UTM(lon, lat)


# lat_new, lon_new = UTM2LonLat(utm_e, utm_n)
