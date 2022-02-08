import os


# short script to extract all .mrb paths

def main():

    root_directory = "/Users/fryderykkogl/Dropbox (Partners HealthCare)/TCIA/TCIA cases ALL"

    x = []

    for path, subdirs, files in os.walk(root_directory):
        for name in files:
            if ".mrb" in name:
                print(os.path.join(path, name))
                x.append(os.path.join(path, name))

    print(len(x))


if __name__ == "__main__":
    main()
