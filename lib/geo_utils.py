from osgeo import ogr
from osgeo import osr
from lxml import etree


def identify_epsg(srs_name):
    if srs_name.lower().startswith('epsg:'):
        return srs_name
    elif srs_name.startswith('urn:ogc:def:crs:EPSG'):
        return convert_urn_to_epsg(srs_name)
    # TODO: add the WxS CRS: options
    # and this one: urn:ogc:def:crs:OGC:1.3:CRS84

    return ''


def convert_urn_to_epsg(urn):
    parts = urn.split(':')
    return 'EPSG:' + parts[-1]


def define_spref(srs_str):
    # TODO: something to get at the urn vs code vs whatever
    #       to get the epsg code
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srs_str)
    return srs


def reproject(geom, in_srs, out_srs):
    if in_srs == out_srs:
        return geom

    transform = osr.CoordinateTransformation(in_srs, out_srs)
    geom.Transform(transform)
    return geom


def bbox_to_geom(bbox):
    wkt = 'POLYGON((%(minx)s %(miny)s, %(minx)s %(maxy)s, %(maxx)s %(maxy)s, %(maxx)s %(miny)s, %(minx)s %(miny)s))' \
        % {'minx': bbox[0], 'miny': bbox[1], 'maxx': bbox[2], 'maxy': bbox[3]}
    return ogr.CreateGeometryFromWkt(wkt)


def gml_to_geom(gml):
    '''
    for some gml block (from iso, likely),
    try to convert to gml
    '''
    return ogr.CreateGeometryFromGML(etree.tostring(gml))


def to_wkt(geom):
    # TODO: this is clearly wrong but don't care
    # wkt = 'SRID=%s;%s' % (srid, wkt) if srid else wkt
    return geom.ExportAsWkt()
