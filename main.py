import unittest
import sys
import os
import subprocess
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr


global_counter = 1


class TestResultCollector(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = list()
        self.excludes = list()

    def startTest(self, test):
        # Initialize buffers for capturing output
        self.output_buffer = io.StringIO()
        self.error_buffer = io.StringIO()
        # Redirect stdout and stderr to the buffers
        self._original_stdout = redirect_stdout(self.output_buffer)
        self._original_stderr = redirect_stderr(self.error_buffer)
        self._original_stdout.__enter__()
        self._original_stderr.__enter__()
        super().startTest(test)

    def stopTest(self, test):
        # Stop redirecting stdout and stderr
        self._original_stdout.__exit__(None, None, None)
        self._original_stderr.__exit__(None, None, None)
        # Check the buffers for the specific message
        if 'http error' in self.output_buffer.getvalue().lower() or 'http error' in self.error_buffer.getvalue().lower():
            self.excludes.append(test.id())
        super().stopTest(test)

    def addSuccess(self, test):
        self.test_results.append((test.id(), 'passed'))

    def addSkip(self, test, reason):
        self.test_results.append((test.id(), 'skipped'))

    def addFailure(self, test, err):
        if self.detectUnsolvableError(self._exc_info_to_string(err, test).lower()):
            self.test_results.append((test.id(), 'skipped'))
        else:
            self.test_results.append((test.id(), 'failed'))

    def addError(self, test, err):
        if self.detectUnsolvableError(self._exc_info_to_string(err, test).lower()):
            self.test_results.append((test.id(), 'skipped'))
        else:
            self.test_results.append((test.id(), 'error'))

    def detectUnsolvableError(self, msg: str) -> bool:
        return 'unable to download' in msg or\
                'unable to extract' in msg



def runUnittest() -> list:
    runner = unittest.TextTestRunner(resultclass=TestResultCollector).run(unittest.defaultTestLoader.discover('.'))
    results = runner.test_results
    excludes = runner.excludes
    failed_tcs = list()
    error_tcs = list()
    passed_tcs = list()

    dist = [0, 0, 0, 0] # failed | passed | skipped | error
    for id, test_result in results:
        if id in excludes:
            test_result = 'skipped'
        dist[0] += 1 if test_result == 'failed' else 0
        dist[1] += 1 if test_result == 'passed' else 0
        dist[2] += 1 if test_result == 'skipped' else 0
        dist[3] += 1 if test_result == 'error' else 0
        if test_result == 'failed':
            failed_tcs.append(i(d, test_result))
        if test_result == 'error':
            error_tcs.append(i(d, test_result))
        if test_result == 'passed':
            passed_tcs.append(i(d, test_result))

    print(f"\n=== {dist[0]} failed, {dist[1]} passed, {dist[2]} skipped, {dist[3]} error, {len(results)} total ===")
    for id, _ in failed_tcs:
        print('FAILED', id)
    for id, _ in error_tcs:
        print('E', id)
    print(len(excludes))
    return failed_tcs + error_tcs + passed_tcs



def commandCoverage(test_id, omission, text):
    global global_counter

    print('\n=============================================')
    print(f'=> {text} -Exitcode')
    print(f'=> [ {global_counter} ] : "{test_id}" -Run')
    subprocess.run(['coverage', 'run', '-m', 'unittest', '-q', test_id])
    print(f'=> [ {global_counter} ] : "{test_id}" -Write')
    print('=============================================\n')
    subprocess.run(['coverage', 'json', '-o', f'coverage/{global_counter}/summary.json', '--omit', omission])
    
    if os.path.exists(f'coverage/{global_counter}/summary.json'):
        with open(f'coverage/{global_counter}/{global_counter}.test', 'w') as f:
            f.write(text)
        global_counter += 1
    else:
        shutil.rmtree(f'coverage/{global_counter}')



def runCoverage(test_id, report, omission):
    if report == 'skipped':
        return
    if report == 'passed':
        commandCoverage(test_id, omission, 'passed')
    elif report == 'failed' or report == 'error':
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
