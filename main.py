import unittest
import subprocess
import sys
import os

global_counter = 1

def format_testcase(input_string):
    parts = input_string.split(" (")
    test_method = parts[0]
    test_class = parts[1].rstrip(")")
    arg = sys.argv[1]

    if test_class.startswith('unittest.'):
        return f"{test_class}.{test_method}"
    return f"{arg.replace('/', '.')}.{test_class}.{test_method}"

def subcall(suite, omission):
    if hasattr(suite, '__iter__'):
        for x in suite:
            subcall(x, omission)
    else:
        global global_counter

        testcase = format_testcase(str(suite))
        print('coverage', 'run', '-m', 'unittest', '-q', testcase)
        subprocess.run(['coverage', 'run', '-m', 'unittest', '-q', testcase])
        print('coverage', 'json', '-o', f"coverage/{global_counter}/summary.json", f'--omit="{omission}"')
        subprocess.run(['coverage', 'json', '-o', f"coverage/{global_counter}/summary.json", f'--omit="{omission}"'])
        
        if os.path.exists(f'coverage/{global_counter}/summary.json'):
            result = suite.run()
            with open(f'coverage/{global_counter}/{global_counter}.test', 'w') as f:
                f.write('passed' if result.wasSuccessful() else 'failed')

            #with open(f'coverage/{global_counter}/{global_counter}.output', 'w') as f:
            #    for _, traceback in result.errors:
            #        f.write(traceback)

            global_counter += 1



if __name__ == '__main__':
    omission = "/usr/local/lib/*,"
    for arg in sys.argv[1:]:
        omission = omission + os.path.join(arg, '*,')
    if omission.endswith(','):
        omission = omission[:-1]

    subcall(unittest.defaultTestLoader.discover(sys.argv[1]), omission)
