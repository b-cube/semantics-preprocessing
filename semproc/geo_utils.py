from osgeo import ogr
from osgeo import osr
from lxml import etree


def parse_gml_envelope(envelope, namespaces):
    '''
    from a wcs lonLatEnvelope node, extract a bbox as
    [min, miny, maxx, maxy] with crs understanding

    note: no reprojection here so if not epsg:4326? and what to
    do about invalid srsName values/versions?
    '''
    # srs = envelope.attrib['srsName'] if 'srsName' in envelope.attrib
    # if srs != 'EPSG:4326':
    # if srs != 'urn:ogc:def:crs:OGC:1.3:CRS84'
    #   return []

    # two nodes required, first as lower left, second as upper right
    lower_left = envelope.xpath('gml:pos[1]', namespaces=namespaces)
    assert lower_left
    mins = map(float, lower_left[0].text.split(' '))

    upper_right = envelope.xpath('gml:pos[2]', namespaces=namespaces)
    assert upper_right
    maxes = map(float, upper_right[0].text.split(' '))

    return mins + maxes


def identify_epsg(srs_name):
    # TODO: finish this for the ogc & crs
    if srs_name.lower().startswith('epsg:'):
        return srs_name
    elif srs_name.startswith('urn:ogc:def:crs:EPSG'):
        return convert_urn_to_epsg(srs_name)
    elif srs_name.lower() in ['crs:84', 'urn:ogc:def:crs:ogc:1.3:crs84']:
        return 'EPSG:4326'
    elif srs_name.lower() in ['crs:83']:
        return ''
    elif srs_name.lower() in ['crs:27']:
        return ''

    return ''


def convert_urn_to_epsg(urn):
    parts = urn.split(':')
    return 'EPSG:' + parts[-1]


def define_spref(epsg_code):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(epsg_code.split(':')[-1]))
    return srs


def reproject(geom, in_srs_name, out_srs_name):
    in_srs = define_spref(identify_epsg(in_srs_name))
    out_srs = define_spref(identify_epsg(out_srs_name))
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
    if not isinstance(gml, basestring):
        gml = etree.tostring(gml)
    return ogr.CreateGeometryFromGML(gml)


def to_wkt(geom):
    # wkt = 'SRID=%s;%s' % (srid, wkt) if srid else wkt
    return geom.ExportToWkt()
