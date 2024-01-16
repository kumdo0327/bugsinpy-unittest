import unittest
import sys
import os
import subprocess


global_counter = 1


class TestResultCollector(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []

    def addSuccess(self, test):
        self.test_results.append((test, 'Passed'))

    def addSkip(self, test, reason):
        self.test_results.append((test, 'Skipped'))

    def addFailure(self, test, err):
        self.test_results.append((test, 'Failed'))

    def addError(self, test, err):
        self.test_results.append((test, 'Error'))



def discover_and_run_tests():
    suite = unittest.defaultTestLoader.discover('.')
    result = unittest.TextTestRunner(resultclass=TestResultCollector).run(suite)

    for test, status in result.test_results:
        print(f"{test.id()}: {status}")



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
        print(f'\n>> >> Run Coverage {global_counter} : "{testcase}"')
        subprocess.run(['coverage', 'run', '-m', 'unittest', '-q', testcase]).returncode

        print(f'\n>> >> Wrote Json {global_counter} : "{testcase}"')
        subprocess.run(['coverage', 'json', '-o', f'coverage/{global_counter}/summary.json', '--omit', omission])
        
        if os.path.exists(f'coverage/{global_counter}/summary.json'):
            result = suite.run()
            with open(f'coverage/{global_counter}/{global_counter}.test', 'w') as f:
                f.write('passed' if result.wasSuccessful() else 'failed')

            #with open(f'coverage/{global_counter}/{global_counter}.output', 'w') as f:
            #    for _, traceback in result.errors:
            #        f.write(traceback)

            global_counter += 1



def main():
    discover_and_run_tests()
    return

    omission = "/usr/local/lib/*,"
    for arg in sys.argv[1:]:
        omission = omission + os.path.join(arg, '*,')
    if omission.endswith(','):
        omission = omission[:-1]

    subcall(unittest.defaultTestLoader.discover(), omission)



if __name__ == '__main__':
    main()
