import re
import extract_headers_and_paragraphs as extractor

def main():
    document_filename = "JPMorgan-A-Portfolio-Approach-to-Impact-Investment.pdf"
    doc = extractor.extract_headers_paragraphs(document_filename)
    tagger = lambda x: x + '</' + re.findall('^<.*>',x)[0][1:]
    tagged_doc = [tagger(element) for element in doc]
    print(tagged_doc[0:2]) 

if __name__ == '__main__':
    main()