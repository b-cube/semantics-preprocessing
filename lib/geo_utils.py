from osgeo import ogr


def create_geometry(simple_poly_array):
    return None


def to_wkt(geom):
    # TODO: this is clearly wrong but don't care
    return geom.ExportAsWkt()
