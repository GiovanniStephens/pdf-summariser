from operator import contains, itemgetter
import fitz
import re

def fonts(doc, granularity=False):
    """Extracts fonts and their usage in PDF documents.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool
    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.getText("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(s['size'], s['flags'], s['font'], s['color'])
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = "{0}".format(s['size'])
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles


def font_tags(font_counts, styles):
    """Returns dictionary with font sizes as keys and tags as value.
    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict
    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size

    # sorting the font sizes high to low, so that we can append the right integer to each tag 
    font_sizes = []
    for (font_size, count) in font_counts:
        font_sizes.append(float(font_size))
    font_sizes.sort(reverse=True)

    # aggregating the tags for each font size
    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = '<h{0}>'.format(idx)
        elif size < p_size:
            size_tag[size] = '<s{0}>'.format(idx)

    return size_tag


def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict
    :rtype: list
    :return: texts with pre-prended element tags
    """
    header_para = []  # list with headers and paragraphs
    first = True  # boolean operator for first header
    previous_s = {}  # previous span

    for page in doc:
        blocks = page.getText("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # this block contains text

                # REMEMBER: multiple fonts and sizes are possible IN one block

                block_string = ""  # text found in block
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if s['text'].strip():  # removing whitespaces:
                            if first:
                                previous_s = s
                                first = False
                                block_string = size_tag[s['size']] + s['text']
                            else:
                                if s['size'] == previous_s['size']:

                                    if block_string and all((c == "\n") for c in block_string):
                                        # block_string only contains pipes
                                        block_string = size_tag[s['size']] + s['text']
                                    if block_string == "":
                                        # new block has started, so append size tag
                                        block_string = size_tag[s['size']] + s['text'] 
                                    else:  # in the same block, so concatenate strings
                                        block_string += "" + s['text']

                                else:
                                    if block_string and not all((c == "\n") for c in block_string):
                                        closing_tag = '</' + size_tag[previous_s['size']][1:]
                                        header_para.append(block_string.strip() + closing_tag)
                                        block_string = size_tag[s['size']] + s['text']
                                    else:
                                        header_para.append(block_string)
                                        block_string = size_tag[s['size']] + s['text']

                                previous_s = s
                    # new block started, indicating with a newline (was pipe)
                    block_string += "\n"
                if all((c == "\n") for c in block_string):
                    header_para.append(block_string)
                else:
                    closing_tag = '</' + size_tag[previous_s['size']][1:]
                    header_para.append(block_string.strip() + closing_tag)

    return header_para


def extract_headers_paragraphs(pdf_filename, remove_s_tags=False):
    doc = fitz.open(pdf_filename)

    font_counts, styles = fonts(doc, granularity=False)

    size_tag = font_tags(font_counts, styles)

    elements = headers_para(doc, size_tag)

    filtered_elements = [element for element in elements if len(element)>0]
    filtered_elements = [element for element in filtered_elements if element[0]=='<']
    
    if remove_s_tags:
        filtered_elements = [element for element in filtered_elements if element[1]=='h' or element[1]=='p']

    return filtered_elements


def format_headers_paragraphs(headers_paragraphs):
    # Removes newlines
    headers_paragraphs = [element.replace('\n', '') for element in headers_paragraphs]
    # Strips whitespace 
    headers_paragraphs = [element.strip() for element in headers_paragraphs]
    # Joins elements into one string
    headers_paragraphs = ''.join(headers_paragraphs)
    return headers_paragraphs


def get_plain_text(text):
    # uses regex to replace closing tags
    text = re.sub(r'</[a-z]([0-9]+)?>', '. ', text)
    # removes all tags
    text = re.sub(r'<[a-z]([0-9]+)?>', '', text)
    return text.encode("ascii", "ignore")


if __name__ == "__main__":
    pdf_filename = "JPMorgan-A-Portfolio-Approach-to-Impact-Investment.pdf"
    elements = extract_headers_paragraphs(pdf_filename, remove_s_tags=True)
    formatted_elements = format_headers_paragraphs(elements)
    plain_text = get_plain_text(formatted_elements)
    print(plain_text)