

def generate_localname_xpath(tags):
    unchangeds = ['*', '..', '.', '//*']
    return '/'.join(
        ['%s*[local-name()="%s"]' % ('@' if '@' in t else '', t.replace('@', ''))
         if t not in unchangeds else t for t in tags])


def extract_attrib(elem, tags):
    e = extract_elem(elem, tags)
    return e.strip() if e else ''


def extract_attribs(elem, tags):
    e = extract_elem(elem, tags)
    return [m.strip() for m in e]


def extract_item(elem, tags):
    e = extract_elem(elem, tags)
    return e.text.strip() if e is not None and e.text else ''


def extract_items(elem, tags):
    es = extract_elems(elem, tags)
    return [e.text.strip() for e in es if e is not None and e.text]


def extract_elems(elem, tags):
    xp = generate_localname_xpath(tags)
    return elem.xpath(xp)


def extract_elem(elem, tags):
    xp = generate_localname_xpath(tags)
    return next(iter(elem.xpath(xp)), None)
