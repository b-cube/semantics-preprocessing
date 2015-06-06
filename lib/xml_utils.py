

def generate_localname_xpath(tags):
    unchangeds = ['*', '..', '.', '//*']
    return '/'.join(
        ['%s*[local-name()="%s"]' % ('@' if '@' in t else '', t.replace('@', ''))
         if t not in unchangeds else t for t in tags])


def extract_attrib(elem, tags):
    xp = generate_localname_xpath(tags)
    e = next(iter(elem.xpath(xp)), '')
    return e.strip() if e else ''


def extract_item(elem, tags):
    xp = generate_localname_xpath(tags)
    e = next(iter(elem.xpath(xp)), None)
    return e.text.strip() if e is not None else ''


def extract_items(elem, tags):
    xp = generate_localname_xpath(tags)
    es = elem.xpath(xp)
    return [e.text.strip() for e in es if e is not None and e.text]
