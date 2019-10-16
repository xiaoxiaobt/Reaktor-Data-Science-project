def main():
    FILE_NAME = "industry_2008.csv"
    OUTPUT_NAME = "industry_2008_u.csv"
    file = open(FILE_NAME, encoding='iso-8859-1')
    file_write = open(OUTPUT_NAME, "w", encoding='utf-8')
    [file_write.write(_) for _ in file.readlines()]


main()
