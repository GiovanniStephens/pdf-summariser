from pdfminer.high_level import extract_text

text = extract_text("JPMorgan-A-Portfolio-Approach-to-Impact-Investment.pdf")
 
print(text[0:100])