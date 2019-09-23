def main():
    """This function add "id" feature to .json file. The id feature works as identifier (key) to access
     corresponding shape"""
    file = open("postinumeroalueet 2016.json", "r")
    file_write = open("idchanged.json", "w")
    wait_4_write = False
    number = 0
    for line in file.readlines():
        if '"posti_alue"' in line:
            number = line.split(": \"")[1].split("\",")[0]
            wait_4_write = True
            file_write.write(line)
        elif '"namn"' in line:
            continue
        elif '"kuntanro"' in line:
            continue
        elif '"description"' in line:
            continue
        elif '"vuosi"' in line:
            continue
        elif wait_4_write and ("}" in line):
            file_write.write(line.rstrip("\n") + "," + "\n")
            file_write.write('            "id": "' + number + '"\n')
            wait_4_write = False
        else:
            file_write.write(line)


main()
