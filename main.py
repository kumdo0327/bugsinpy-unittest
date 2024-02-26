import unittest
import sys
import os
import subprocess
import shutil
import warnings
import threading


global_counter = 1


# Thread-local storage to keep track of the current test case
current_test = threading.local()
class WarningCaptureContext:
    def __init__(self, test):
        self.test = test

    def __enter__(self):
        # Set the current test case
        current_test.value = self.test

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clear the current test case when the test is done
        current_test.value = None



class CustomTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        self._warning_capture_context = WarningCaptureContext(test)
        self._warning_capture_context.__enter__()

    def stopTest(self, test):
        super().stopTest(test)
        if self._warning_capture_context:
            self._warning_capture_context.__exit__(None, None, None)

    def addWarning(self, tc_list: list):
        test_id = getattr(current_test, 'value', None)
        if test_id:
            tc_list.append(test_id.id())



class TestResultCollector(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.resultclass = CustomTestResult
        self.test_results = list()
        self.warning_tests = list()

    def run(self, test):
        # Setup the warnings filter to capture specific warnings
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            result = super().run(test)
        
        # Process captured warnings
        for warning in captured_warnings:
            if "HTTP Error" in str(warning.message):
                result.addWarning(self.warning_tests)
        return result

    def addSuccess(self, test):
        self.test_results.append((test.id(), 'passed'))

    def addSkip(self, test, reason):
        self.test_results.append((test.id(), 'skipped'))

    def addFailure(self, test, err):
        if self.detectUnsolvableError(self._exc_info_to_string(err, test)):
            self.test_results.append((test.id(), 'skipped'))
        else:
            self.test_results.append((test.id(), 'failed'))

    def addError(self, test, err):
        if self.detectUnsolvableError(self._exc_info_to_string(err, test)):
            self.test_results.append((test.id(), 'skipped'))
        else:
            self.test_results.append((test.id(), 'error'))

    def detectUnsolvableError(self, msg: str) -> bool:
        print('\n>\tBEGIN')
        print('===============================================')
        print(msg)
        print('===============================================')
        print('Unable to download' in msg or 'Unable to extract' in msg)
        print('>\tEND\n')
        
        return 'Unable to download' in msg or 'Unable to extract' in msg



def runUnittest() -> list:
    test_runner = unittest.TextTestRunner(resultclass=TestResultCollector).run(unittest.defaultTestLoader.discover('.'))
    results = test_runner.test_results
    warnings = test_runner.warning_tests

    dist = [0, 0, 0, 0] # failed | passed | skipped | error
    failed_tcs = list()
    error_tcs = list()
    for id, test_result in results:
        if id in warnings:
            test_result = 'skipped'

        dist[0] += 1 if test_result == 'failed' else 0
        dist[1] += 1 if test_result == 'passed' else 0
        dist[2] += 1 if test_result == 'skipped' else 0
        dist[3] += 1 if test_result == 'error' else 0
        if test_result == 'failed':
            failed_tcs.append(id)
        if test_result == 'error':
            error_tcs.append(id)

    print(f"\n=== {dist[0]} failed, {dist[1]} passed, {dist[2]} skipped, {dist[3]} error, {len(results)} total ===")
    for id in failed_tcs:
        print('FAILED', id)
    for id in error_tcs:
        print('E', id)
    return results



def commandCoverage(test_id, omission, text):
    global global_counter

    print(f'\n===> ExitCode is {text}')
    print(f'\n===> Run Coverage {global_counter} : "{test_id}"')
    subprocess.run(['coverage', 'run', '-m', 'unittest', '-q', test_id])
    print(f'\n===> Wrote Json {global_counter} : "{test_id}"')
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
