from lxml import etree, html
import re
from io import StringIO
from io import open
import textwrap
import os

basepath = os.path.dirname(os.path.realpath(__file__))


if str != bytes:
    unicode = str


class TextBlock(object):

    def __init__(self, indent, content, break_after=0):
        self.indent = indent
        self.content = content
        self.break_after = break_after

    def __str__(self):
        content = re.sub(' +', ' ', self.content.replace('\n', ' ')).strip()
        block = ('\t'*self.indent + '') + ('\n'+'\t'*self.indent + '').join(textwrap.wrap(content, replace_whitespace=False))
        return block + '\n' * self.break_after


def html_to_text(html):
    indent_tags = u'DD',
    block_tags = u'P', u'H1', u'H2', u'H3', u'DT'
    break_after_tags = u'DD', u'P', u'H1', u'H2', u'H3'
    upper_tags = u'H1', u'H2', u'H3'

    def parse_element(e, blocklist):
        last_indent = blocklist[-1].indent
        tag = e.tag.upper()
        inner = e.text if e.text else ''
        tail = e.tail if e.tail else ''
        if tag in upper_tags:
            inner = inner.upper()
        break_after = (tag in break_after_tags or e.get('class') == 'block')
        if tag in block_tags or e.get('class') == 'block':
            blocklist.append(TextBlock(last_indent, '', break_after))
        elif tag in indent_tags:
            blocklist.append(TextBlock(last_indent+1, '', break_after))
        blocklist[-1].content += inner
        for c in e.iterchildren(tag=etree.Element):
            parse_element(c, blocklist)
        if (tag in indent_tags + block_tags or blocklist[-1].indent != last_indent):
            break_after = blocklist[-1].break_after
            blocklist.append(TextBlock(last_indent, tail, break_after))
        else:
            blocklist[-1].content += tail

    parser = etree.HTMLParser(encoding='utf-8')
    doc = etree.parse(StringIO(html), parser)
    docroot = doc.getroot()
    blocklist = [TextBlock(0, '')]
    parse_element(docroot, blocklist)
    return u'\n'.join(unicode(block) for block in blocklist[1:] if unicode(block).strip())


def makeusage():
    usage_html = open(basepath + '/options.html', mode='r').read()
    # output usage
    with open(basepath + '/../pcbasic/data/USAGE.txt', 'w') as textfile:
        textfile.write(html_to_text(usage_html))
