def main():
    """Find names of all types of industries"""
    storage = open("modified_type.tsv", 'w+', encoding='utf-8')
    docx = open("modified_type_docx.tsv", 'w+', encoding='utf-8')
    file = open('industry_2008.csv', 'r', encoding='iso-8859-1')
    file.readline()
    for line in file.readlines():
        line = line.rstrip('\n').split('\t')[1:]
        line[0] = " ".join(line[0].split()[1:]).rstrip("\"")
        storage.write(line[0] + "\t" + line[1] + '\n')
        docx.write(line[0] + '\n')
    storage.close()
    file.close()
    docx.close()


main()
