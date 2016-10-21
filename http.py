"""For fetching API results."""
import urllib2
import sys
from warnings import warn
from time import sleep
import socket

NUM_HTTP_RETRIES = 3
NUM_SEC_TIMEOUT = 120
NUM_SEC_SLEEP_DEFAULT = 5

class MaxTriesExceededError(Exception):
    """Max tries for HTTP request exceeeded."""
    pass

def _handle_http_429():
    """Respond to an HTTP 429 response."""
    print(("Reached maximum number of requests for API  -- waiting for %d "
           "seconds before trying again.") % NUM_SEC_SLEEP_DEFAULT)
    sleep(NUM_SEC_SLEEP_DEFAULT)


def _handle_generic_http_err():
    #print(("Encountered a problem requesting data from the API -- waiting %d "
    #       "seconds before trying agin.") % NUM_SEC_SLEEP_DEFAULT)
    sleep(NUM_SEC_SLEEP_DEFAULT)


def fetch_request(url):
    """Fetch urllib2 request and handle errors.

    Returns: str if page results can be fetched, otherwise None
    Raises:
        MaxTriesExceededError: Raised if max # of tries after failure is
            exceeded.
    """
    req = urllib2.Request(url)
    response = None
    for _ in range(0, NUM_HTTP_RETRIES + 1):
        try:
            response = urllib2.urlopen(req, timeout=NUM_SEC_TIMEOUT)
            if response is None:
                sys.exit("Could not open requested resource.")
            else:
                try:
                    if response.msg != 'OK':
                        warn("Server message in response: %s" % response.msg)
                except AttributeError:
                    pass
                return response.read()

        except urllib2.HTTPError as err:
            if err.code == 422:
                return None
            elif err.code == 429:
                _handle_http_429()
            else:
                _handle_generic_http_err()

        except urllib2.URLError as err:
            if err.reason == 'Unprocessable Entity':
                return None
            elif err.reason == 'Too Many Requests':
                _handle_http_429()
            else:
                _handle_generic_http_err()

        except (socket.timeout, socket.error) as err:
            _handle_generic_http_err()

    raise MaxTriesExceededError
