
# coding: utf-8

# Or, how to generate likely endpoints from a piece of XML somewhere along the opendap/thredds ftp-like tree.
# 
# Or, there is no crying in metadata but we have six examples and six structures. 
# 
# Deep breaths. Let's make some URLs.
# 
# But first, defining the problem space.
# 
# ### From the 1.0.2 namespaces
# 
# Our example: http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.project.ARCSS.thredds.xml
# 
# ```
# <catalog xmlns="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
#     xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#     xsi:schemaLocation="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0 http://www.unidata.ucar.edu/schemas/thredds/InvCatalog.1.0.2.xsd"
#     version="1.0.2" name="ARCSS: NSF Arctic System Science">
#     <dataset authority="edu.ucar.eol.codiac" ID="ucar.ncar.eol.project.ARCSS"
#         name="ARCSS: NSF Arctic System Science" harvest="true">
#         <metadata
#             xlink:href="http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.project.ARCSS.metadata.xml"
#             metadataType="THREDDS" inherited="false"/>
#         <catalogRef
#             xlink:href="http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.dataset.106_352.thredds.xml"
#             xlink:title="14C Measurements in Large-Volume Ice Samples from Pakitsoq, West Greenland"/>
#         <catalogRef
#             xlink:href="http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.dataset.106_ARCSS130.thredds.xml"
#             xlink:title="A Half-Century of Change in Arctic Alaskan Shrubs: A Photographic-Based Assessment"
#         />
#     </dataset>
# </catalog>
# ```
# 
# No service endpoints. All internal endpoints are full defined.
# 
# Traversing the tree - it is not clear from those endpoints how to do that.
# 
# If this is all datasets in the project ARCSS:
# 
# http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.project.ARCSS.thredds.xml
# 
# and this is the catalog of EOL projects:
# 
# http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.thredds.xml
# 
# the traversal is based on educated guessing based on reading the URL and not any meaningful element in the XML. You could, I suppose, run the intersect and move up to thredds.xml by junking the bits **not** found in the source URL or rely on the ID (this seems like an EOL implementation choice? These do not match 100% across even our small example set.)
# 
# <font color="red">Rule 1: If fully defined, do nothing.</font>
# 
# ### The Idaho data 
# 
# For reference.
# 
# Base URL: http://thredds.northwestknowledge.net:8080/thredds/catalog.xml
# 
# And where we immediately demonstrate the unreliability of THREDDS IDs as URL-friendly:
# 
# ```
# <catalogRef name="" harvest="true" ID="NKN_DATA_ALL_SCAN" xlink:href="/thredds/catalog/NKN_PUBLISHED_DATA/catalog.xml" xlink:title="NKN Published Data">
# ```
# 
# and from this catalog:
# 
# http://thredds.northwestknowledge.net:8080/thredds/catalog/NKN_PUBLISHED_DATA/A62BEE88-8F92-4649-BC8D-BC56CE96AE2B/FB0C2302-2384-4B7E-8657-20E9AEB4D972/catalog.xml
# 
# ```
# <dataset name="FB0C2302-2384-4B7E-8657-20E9AEB4D972" ID="NKN_DATA_ALL_SCAN/A62BEE88-8F92-4649-BC8D-BC56CE96AE2B/FB0C2302-2384-4B7E-8657-20E9AEB4D972">
# ```
# 
# It has the sort of standard list of services (dap, iso, fileServer, etc). I have not found a combination of those (dataset ID, service option, catalog option) that returns anything but 404s. 
# 
# Because that was an empty dataset bucket. 
# 
# This one is better:
# 
# http://thredds.northwestknowledge.net:8080/thredds/catalog/NKN_PUBLISHED_DATA/CD537FC2-00AB-4B1D-B97E-82AB217E2FCA/FD49B736-CD74-4E2D-9294-DFBA1DDD7568/catalog.xml
# 
# And **then**! you can use the service routes:
# 
# http://thredds.northwestknowledge.net:8080/thredds/iso/NKN_PUBLISHED_DATA/CD537FC2-00AB-4B1D-B97E-82AB217E2FCA/FD49B736-CD74-4E2D-9294-DFBA1DDD7568/dcsmaca_GFDL_CM20_A1B_20462065_bi_run1_westus_epscor.nc
# 
# for what is generously "wonky" ISO. As in UUIDs all the way down but you failed to add it to the fileIdentifier element. 
# 
# <font color="red">Rule 2: If there's a dataset bucket **with** datasets **and** a service bucket **with** services, generate URL from host + service base + dataset.urlPath (for each service and each child dataset).</font>
# 
# 
# And for a catalogRef:
# 
# ```
# <catalogRef name="" harvest="true" ID="NKN_DATA_ALL_SCAN" xlink:href="/thredds/catalog/NKN_PUBLISHED_DATA/catalog.xml" xlink:title="NKN Published Data">
# ```
# 
# <font color="red">Rule 3: If there's a catalogRef **with** an href that does not match Rule 1, generate URL from host + catalogRef.href (possible test - the harvest url INTERSECT the href relative path and UNION).</font>
# 
# #### Note: really not sure if we can make solid guesses about moving up the catalog chain (ie. get the catalog.xml for the parent object where the parent is not in the response but in the harvest url minus the last route element).
# 
# 
# ### A NOAA service
# 
# http://www.esrl.noaa.gov/psd/thredds/catalog.xml
# 
# http://www.esrl.noaa.gov/psd/thredds/catalog/Datasets/catalog.xml
# 
# ```
# <dataset name="Datasets" ID="Datasets">
# <metadata inherited="true">
# <serviceName>all</serviceName>
# <dataType>GRID</dataType>
# </metadata>
# <catalogRef xlink:href="20thC_ReanV2/catalog.xml" xlink:title="20thC_ReanV2" ID="Datasets/20thC_ReanV2" name=""/>
# <catalogRef xlink:href="COBE/catalog.xml" xlink:title="COBE" ID="Datasets/COBE" name=""/>
# <catalogRef xlink:href="COBE2/catalog.xml" xlink:title="COBE2" ID="Datasets/COBE2" name=""/>
# <catalogRef xlink:href="CarbonTracker/catalog.xml" xlink:title="CarbonTracker" ID="Datasets/CarbonTracker" name=""/>
# ```
# 
# <font color="red">Rule 4: If there's a catalogRef **with** an href that does not match Rule 1 **and** the first route element of the relative path **does not** intersect with the harvest URL, strip off the last element of the harvest URL and append the catalogRef.href. </font>

# In[35]:

import urlparse

def intersect_url(url, path, bases=[]):
    parts = urlparse.urlparse(path)
    if parts.scheme and parts.netloc:
        # it's a valid url, do nothing
        return path

    parts = urlparse.urlparse(url)
    url_paths = parts.path.split('/')
    paths = path.split('/')
    
    if bases:
        return [urlparse.urlunparse((
            parts.scheme,
            parts.netloc,
            '/'.join([b, path]),
            parts.params,
            parts.query,
            parts.fragment
        )) for b in bases]
    
    match_index = url_paths.index(paths[0]) if paths[0] in url_paths else -1
    if match_index < 0:
        return urlparse.urljoin(url.replace('catalog.xml', ''), path)
    else:
        return urlparse.urljoin(
            urlparse.urlunparse(
                (
                    parts.scheme, 
                    parts.netloc, 
                    '/'.join(url_paths[0:match_index+1]), 
                     parts.params, 
                     parts.query, 
                     parts.fragment)
                ),
            path
        ) 
    
url = 'http://stellwagen.org/thredds/catalog/TSdata/PV_SHELF/catalog.xml'
path = 'PV_SHELF/my-dataset.nc'

# print intersect_url(url, path)
paths = [intersect_url(url, path)]

url = 'http://stellwagen.org/thredds/catalog/TSdata/PV_SHELF/catalog.xml'
path = 'my-dataset.nc'

# print intersect_url(url, path)
paths += [intersect_url(url, path)]

url = 'http://stellwagen.org/thredds/catalog/TSdata/PV_SHELF/catalog.xml'
path = 'TSdata/PV_SHELF/my-dataset.nc'

# print intersect_url(url, path)
paths += [intersect_url(url, path)]

url = 'http://stellwagen.org/thredds/catalog/TSdata/PV_SHELF/catalog.xml'
path = 'http://stellwagen.org/thredds/catalog/TSdata/PV_SHELF/my-dataset.nc'

# print intersect_url(url, path)
paths += [intersect_url(url, path)]

url = 'http://stellwagen.org/thredds/catalog/TSdata/PV_SHELF/catalog.xml'
path = 'TSdata/PV_SHELF/my-dataset.nc'
bases = ['thredds/catalog', 'thredds/iso',]

# print intersect_url(url, path, bases)
paths += intersect_url(url, path, bases)

set(paths)


# Process: generate siblings (if services), generate children (nested urls), generate parent catalog (one level up).

# In[36]:

# get the parent
intersect_url(url, '../catalog.xml')


# In[ ]:



