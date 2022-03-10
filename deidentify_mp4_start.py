# command to compile everything into one executable
# pyinstaller deidentify_mp4_start.py --name=deidentify_mp4 --onefile

from deidentify_mp4.main_func import main

if __name__ == "__main__":
    main()
