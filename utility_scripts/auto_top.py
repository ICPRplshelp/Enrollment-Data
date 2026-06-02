from generate_autocomplete import main as gen_auto
from generate_top_courses import main as gen_top
import sys


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Pass in the session name!")
        exit(1)
    ses = sys.argv[1]
    gen_auto(ses)
    gen_top(ses)




