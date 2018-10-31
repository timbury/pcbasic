import sys
import os
from os import path
import shutil
from io import StringIO
from datetime import datetime
from io import open

from lxml import etree
import markdown
from markdown.extensions.toc import TocExtension
import markdown.extensions.headerid

# obtain metadata without importing the package (to avoid breaking setup)
with open(
        path.join(path.abspath(path.dirname(__file__)), '..', 'pcbasic', 'metadata.py'),
        encoding='utf-8') as f:
    exec(f.read())

basepath = os.path.dirname(os.path.realpath(__file__))


def mdtohtml(md_file, outf, prefix='', baselevel=1):
    with open(md_file, 'r', encoding='utf-8') as inf:
        md = inf.read()
        toc = TocExtension(baselevel=baselevel, slugify=lambda value, separator: prefix + markdown.extensions.headerid.slugify(value, separator))
        outf.write(markdown.markdown(md, extensions=['markdown.extensions.tables', toc], output_format='html5', lazy_ol=False))

def maketoc(html_doc, toc):
    parser = etree.HTMLParser()
    doc = etree.parse(html_doc, parser)
    last = -1
    toc.write(u'<nav class="toc">\n')
    toc.write(u'    <h2 id="toc">Table of Contents</h2>\n')
    for node in doc.xpath('//h2|//h3|//h4'):
        level = int(node.tag[1])
        node_id = node.get('id')
        if last == -1:
            last += level
            first = last
        node.tag = 'a'
        node.attrib.clear()
        if node_id:
            node.set('href', '#' + node_id)
        if level-last < 0:
            toc.write(u'</li>\n')
            for i in range((last-level), 0, -1):
                toc.write(u'    '*((level+i-1)*2+1) + '</ul>\n')
                toc.write(u'    '*(level+i-1)*2 + '</li>\n')
        elif level-last > 0:
            toc.write(u'\n')
            for i in range(level-last, 0, -1):
                toc.write(u'    '*((level-i)*2+1) + '<ul>\n')
        else:
            toc.write(u'</li>\n')
        toc.write(u'    '*(level*2) + u'<li>' + etree.tostring(node).strip().decode('utf-8'))
        last = level
    toc.write(u'</li>\n')
    while level > first:
        toc.write(u'    '*(level*2-1) + '</ul>\n')
        level -= 1
    toc.write(u'</nav>\n')

def embed_style(html_file):
    parser = etree.HTMLParser(encoding='utf-8')
    doc = etree.parse(html_file, parser)
    for node in doc.xpath('//link[@rel="stylesheet"]'):
        href = node.get('href')
        css = os.path.join(basepath, href)
        node.tag = 'style'
        node.text = '\n' + open(css, 'r').read() + '\n    '
        node.attrib.clear()
        node.set('id', href)
    with open(html_file, 'w') as f:
        f.write(etree.tostring(doc, method="html").decode('utf-8'))

def get_options(html_file):
    parser = etree.HTMLParser(encoding='utf-8')
    doc = etree.parse(html_file, parser)
    output = []
    for node in doc.xpath('//h3[@id="options"]/following-sibling::dl/dt/code'):
        node.tag = 'a'
        node.attrib.clear()
        link_id = node.getparent().get('id')
        if link_id:
            node.set('href', '#' + link_id)
            node.set('class', 'option-link')
            node.text = '[' + (node.text or '')
            try:
                last = node.getchildren()[-1]
                last.tail = (last.tail or '') + ']'
            except IndexError:
                node.text += ']'
            node.tail = '\n'
            output.append(node)
    return output

def embed_options(html_file):
    parser = etree.HTMLParser(encoding='utf-8')
    doc = etree.parse(html_file, parser)
    for node in doc.xpath('//span[@id="placeholder-options"]'):
        node.clear()
        for c in get_options(html_file):
            node.append(c)
    with open(html_file, 'w') as f:
        f.write(etree.tostring(doc, method="html").decode('utf-8'))

def makedoc(header=None, output=None, embedded_style=True):
    header = header or basepath + '/header.html'
    output = output or basepath + '/../doc/PC-BASIC_documentation.html'
    try:
        os.mkdir(basepath + '/../doc')
    except OSError:
        # already there, ignore
        pass
    basic_license_stream = StringIO()
    doc_license_stream = StringIO()
    readme_stream = StringIO()
    ack_stream = StringIO()
    mdtohtml(basepath + '/../LICENSE.md', basic_license_stream)
    mdtohtml(basepath + '/LICENSE.md', doc_license_stream)
    mdtohtml(basepath + '/../README.md', readme_stream, baselevel=0)
    mdtohtml(basepath + '/../THANKS.md', ack_stream, 'acks_')

    # get the quick-start guide out of README
    quickstart = u''.join(readme_stream.getvalue().split(u'<hr>')[1:])
    quickstart = quickstart.replace(u'http://pc-basic.org/doc/2.0#', u'#')

    quickstart_html = ('<article>\n' + quickstart + '</article>\n')
    licenses_html = '<footer>\n<h2 id="licence">Licences</h2>\n' + basic_license_stream.getvalue() + '<hr />\n' + doc_license_stream.getvalue() + '\n</footer>\n'
    major_version = '.'.join(VERSION.split('.')[:2])
    settings_html = (
            '<article>\n' + open(basepath + '/settings.html', 'r').read().replace('0.0', major_version)
            + '<hr />\n' + open(basepath + '/options.html', 'r').read()
            + open(basepath + '/examples.html', 'r').read() + '</article>\n')
    predoc = StringIO()
    predoc.write(quickstart_html)
    predoc.write(open(basepath + '/documentation.html', 'r').read())
    predoc.write(settings_html)
    predoc.write(open(basepath + '/guide.html', 'r').read())
    predoc.write(open(basepath + '/reference.html', 'r').read())
    predoc.write(open(basepath + '/techref.html', 'r').read())
    predoc.write(open(basepath + '/devguide.html', 'r').read())
    predoc.write('<article>\n' + ack_stream.getvalue()  + '</article>\n')
    predoc.write(licenses_html)
    predoc.write(open(basepath + '/footer.html', 'r').read())
    predoc.seek(0)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if embedded_style:
        subheader_html = u"""
<header>
    <h1>PC-BASIC documentation</h1>
    <small>Version {0}</small>
</header>
""".format(VERSION, now, DESCRIPTION, LONG_DESCRIPTION)
    else:
        subheader_html = u''
    subheader_html += u"""
<article>
    <h2 id="top">PC-BASIC {0}</h2>
    <p>
        <em>{2}</em>
    </p>
    <p>
        {3}
    </p>
    <p>
        This is the documentation for <strong>PC-BASIC {0}</strong>, last updated <em>{1}</em>.<br />
        It consists of the following documents:
    </p>
    <ul>
        <li><strong><a href="#quick-start-guide">Quick Start Guide</a></strong>, the essentials needed to get started</li>
        <li><strong><a href="#using">User's Guide</a></strong>, in-depth guide to using the emulator</li>
        <li><strong><a href="#settings">Configuration Guide</a></strong>, settings and options</li>
        <li><strong><a href="#guide">Language Guide</a></a></strong>, overview of the BASIC language by topic</li>
        <li><strong><a href="#reference">Language Reference</a></strong>, comprehensive reference to BASIC</li>
        <li><strong><a href="#technical">Technical Reference</a></strong>, file formats and internals</li>
        <li><strong><a href="#dev">Developer's Guide</a></strong>, using PC-BASIC as a Python module</li>
    </ul>

""".format(VERSION, now, DESCRIPTION, LONG_DESCRIPTION)
    if not embedded_style:
        subheader_html += u"""
    <p>
        Offline versions of this documentation are available in the following formats:
    </p>
    <ul>
        <li><a href="PC-BASIC_documentation.html">Single-file HTML</a></li>
        <li><a href="PC-BASIC_documentation.pdf">PDF</a></li>
    </ul>
    <p>
        Documentation for other versions of PC-BASIC:
    </p>
    <ul>
        <li><a href="http://pc-basic.org/doc/">PC-BASIC 1.2</a></li>
    </ul>
</article>
"""
    else:
        subheader_html += u'</article>\n'
    tocdoc = StringIO()
    tocdoc.write(subheader_html)
    tocdoc.write(predoc.getvalue())
    tocdoc.seek(0)
    toc = StringIO()
    maketoc(tocdoc, toc)
    header_html = open(header, 'r').read()
    with open(output, 'w') as outf:
        outf.write(header_html)
        outf.write(subheader_html)
        outf.write(toc.getvalue())
        outf.write(predoc.getvalue())
    embed_options(output)
    if embedded_style:
        embed_style(output)
