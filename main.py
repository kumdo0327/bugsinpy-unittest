import unittest
import sys
import os
import subprocess


global_counter = 1


class TestResultCollector(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = list()

    def addSuccess(self, test):
        self.test_results.append((test.id(), 'passed'))

    def addSkip(self, test, reason):
        self.test_results.append((test.id(), 'skipped'))

    def addFailure(self, test, err):
        self.test_results.append((test.id(), 'failed'))

    def addError(self, test, err):
        self.test_results.append((test.id(), 'error'))



def runUnittest() -> list:
    return unittest.TextTestRunner(resultclass=TestResultCollector).run(unittest.defaultTestLoader.discover('.')).test_results



def commandCoverage(test_id, omission, text):
    global global_counter

    print(f'\n>> >> ExitCode is {text}')
    print(f'\n>> >> Run Coverage {global_counter} : "{test_id}"')
    subprocess.run(['coverage', 'run', '-m', 'unittest', '-q', test_id])
    print(f'\n>> >> Wrote Json {global_counter} : "{test_id}"')
    subprocess.run(['coverage', 'json', '-o', f'coverage/{global_counter}/summary.json', '--omit', omission])
    
    if os.path.exists(f'coverage/{global_counter}/summary.json'):
        with open(f'coverage/{global_counter}/{global_counter}.test', 'w') as f:
            f.write(text)
        global_counter += 1



def runCoverage(test_id, report, omission):
    if report == 'skipped' or report == 'error':
        return
    if report == 'passed':
        commandCoverage(test_id, omission, 'passed')
    elif report == 'failed':
        commandCoverage(test_id, omission, 'failed')



def main():
    omission = "/usr/local/lib/*,"
    for arg in sys.argv[1:]:
        omission = omission + os.path.join(arg, '*,')
    if omission.endswith(','):
        omission = omission[:-1]

    for test_id, report in runUnittest():
        runCoverage(test_id, report, omission)



if __name__ == '__main__':
    main()
