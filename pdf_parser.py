from unstructured.partition.pdf import partition_pdf

def parse_pdf(file_path):
    elements = partition_pdf(filename=file_path)
    text = "\n".join([el.text for el in elements if el.text])
    return text