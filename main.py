import unittest
import subprocess
import sys

global_counter = 1

def format_testcase(input_string):
    parts = input_string.split(" (")
    test_method = parts[0]
    test_class = parts[1].rstrip(")")
    arg = sys.argv[1]

    if test_class.startswith('unittest.'):
        return f"{test_class}.{test_method}"
    return f"{arg}.{test_class}.{test_method}"

def subcall(suite):
    if hasattr(suite, '__iter__'):
        for x in suite:
            subcall(x)
    else:
        global global_counter

        print(suite)
        result = suite.run()

        testcase = format_testcase(str(suite))
        subprocess.call(['coverage', 'run', '-m', 'unittest', '-q', testcase])
        subprocess.call(['coverage', 'json', '-o', f'coverage/{global_counter}/summary.json', f'--omit={sys.argv[1]}/*.py'])
        #with open(f'coverage/{global_counter}/{global_counter}.output', 'w') as f:
        #    for _, traceback in result.errors:
        #        f.write(traceback)
        with open(f'coverage/{global_counter}/{global_counter}.test', 'w') as f:
            f.write('passed' if result.wasSuccessful() else 'failed')

        global_counter += 1



if __name__ == '__main__':
    subcall(unittest.defaultTestLoader.discover(sys.argv[1]))
