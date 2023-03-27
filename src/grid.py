import folium
import numpy as np
from geopy import distance as gdistance


class Grid:
    def __init__(self, northwest_coords, southeast_coords, width_resolution, height_resolution) -> None:
        self.northwest_coords = northwest_coords
        self.southeast_coords = southeast_coords
        self.width_resolution = width_resolution
        self.height_resolution = height_resolution
        self.width_bins = int(gdistance.distance(
            northwest_coords, (northwest_coords[0], southeast_coords[1])).km / width_resolution)
        self.height_bins = int(gdistance.distance(
            northwest_coords, (southeast_coords[0], northwest_coords[1])).km / height_resolution)
        self.lat_resolution = (
            northwest_coords[0] - southeast_coords[0]) / self.height_bins
        self.lon_resolution = (
            southeast_coords[1] - northwest_coords[1]) / self.width_bins

    def __str__(self) -> str:
        return f'Grid(w:{self.width_bins}, h:{self.height_bins} = {self.width_bins * self.height_bins})'

    def __len__(self) -> int:
        return self.width_bins * self.height_bins

    def distance_mat(self):
        d_Q_mat = np.zeros((self.width_bins * self.height_bins,
                           self.width_bins * self.height_bins))
        for x in range(self.width_bins * self.height_bins):
            for y in range(self.width_bins * self.height_bins):
                d_Q_mat[x, y] = gdistance.distance(
                    self.locate(x), self.locate(y)).km
        return d_Q_mat

    def distance(self, xi, yi):
        return gdistance.distance(self.locate(xi), self.locate(yi)).km

    def index(self, coords):
        if hasattr(coords, 'lat') and hasattr(coords, 'lon'):
            coords = (coords.lat, coords.lon)
        w = (coords[1] - self.northwest_coords[1]) // self.lon_resolution
        h = (self.northwest_coords[0] - coords[0]) // self.lat_resolution
        return int(h * self.width_bins + w)

    def closed_polygon(self, index=None):
        if index is None:
            nw, se = self.northwest_coords, self.southeast_coords
            return [
                [nw[1], nw[0]],
                [nw[1], se[0]],
                [se[1], se[0]],
                [se[1], nw[0]],
                [nw[1], nw[0]]
            ]
        # GeoJson specified (lon, lat)
        nw = self.locate(index)
        return [
            [nw[1] - self.lon_resolution / 2, nw[0] + self.lat_resolution / 2],
            [nw[1] - self.lon_resolution / 2, nw[0] - self.lat_resolution / 2],
            [nw[1] + self.lon_resolution / 2, nw[0] - self.lat_resolution / 2],
            [nw[1] + self.lon_resolution / 2, nw[0] + self.lat_resolution / 2],
            [nw[1] - self.lon_resolution / 2, nw[0] + self.lat_resolution / 2]
        ]

    def geojson_feat(self, index: int):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    self.closed_polygon(index)
                ]
            }
        }
    
    def offset_index(self, xy: tuple):
        x, y = xy
        return int(x // self.width_resolution + (y // self.height_resolution) * self.width_bins)
        
    def offset(self, coords: tuple):
        x_offset = gdistance.distance((coords[0], self.northwest_coords[1]), coords).km
        y_offset = gdistance.distance((self.northwest_coords[0], coords[1]), coords).km
        return x_offset, y_offset

    def locate(self, index):
        w = index % self.width_bins
        h = index // self.width_bins
        return [self.northwest_coords[0] - h * self.lat_resolution, self.northwest_coords[1] + w * self.lon_resolution]

    def filter_nearby(self, df):
        return df.query(f'lat > {self.southeast_coords[0] - self.lat_resolution * 2} and lat < {self.northwest_coords[0] + self.lat_resolution * 2} and lon > {self.northwest_coords[1] - self.lon_resolution * 2} and lon < {self.southeast_coords[1] + self.lon_resolution * 2}')
    
    def filter(self, df):
        return df.query(f'lat > {self.southeast_coords[0]} and lat < {self.northwest_coords[0]} and lon > {self.northwest_coords[1]} and lon < {self.southeast_coords[1]}')
    
    def neighbors(self, index):
        # lat_i, lon_i
        xi, yi = index % self.width_bins, index // self.width_bins
        neighbors = []
        # seq: index of up, right, down, left
        neighbors.append((yi - 1) * self.width_bins + xi if yi > 0 else None)
        neighbors.append(yi * self.width_bins + xi + 1 if xi < self.width_bins - 1 else None)
        neighbors.append((yi + 1) * self.width_bins + xi if yi < self.height_bins - 1 else None)
        neighbors.append(yi * self.width_bins + xi - 1 if xi > 0 else None)
        return neighbors
        # return [n for n in neighbors if not n]

    def map(self, grid=False, **kwargs):
        # center_coords = ((self.northwest_coords[0] + self.southeast_coords[0]) / 2,
        #                  (self.northwest_coords[1] + self.southeast_coords[1]) / 2)
        mmap = folium.Map(**kwargs)
        if grid:
            style_ = {
                'fillColor': '#000000',
                'color': '#000000',
                'weight': 0.5,
                'fillOpacity': 0.1,
                'opacity': 0.2
            }
            for i in range(self.width_bins * self.height_bins):
                folium.GeoJson(self.geojson_feat(i), name=str(
                    i), style_function=lambda f, sty=style_: sty).add_to(mmap)
        return mmap


# https://lbs.qq.com/getPoint/
# 从海淀公园到北京北站
grid = Grid([39.987099, 116.295261], [39.945003,116.353967], 0.2, 0.2)
bj_grid = grid
# New York 
# Lat: 40.7513 Lon: -74.0088 Lat: 40.7115 Lon: -73.9799
paris_grid = Grid([40.7513, -74.0088], [40.7115, -73.9799], 0.2, 0.2)
ny_grid = paris_grid
# paris_grid = Grid([48.87578846428187, 2.3201355043919705], [48.85062647583342, 2.352407843278087], 0.1, 0.1)
# paris_grid = Grid([48.88837602853863, 2.308279519032965], [48.86030399726161, 2.342533319560829], 0.1, 0.1)