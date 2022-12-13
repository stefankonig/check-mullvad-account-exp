import argparse
import string
import pytest
import json
from datetime import datetime, timedelta
from check_mullvad_account_exp import MullvadAccount
from unittest.mock import patch
from requests.models import Response

API_URL = "https://localhost"


def mocked_requests_get(*args, **kwargs):
    response_content = None
    response_code = 500
    request_url = args[0]
    if request_url == f"{API_URL}/200/":
        response_code = 200
        response_content = get_api_response(response_code)
    elif request_url == f"{API_URL}/404/":
        response_code = 404
        response_content = get_api_response(response_code)
    elif request_url == f"{API_URL}/500/":
        response_content = "Internal Server Error"
    elif request_url == f"{API_URL}/5001/":
        response_code = 200
        response_content = get_api_response(5001)
    elif request_url == f"{API_URL}/5002/":
        response_code = 200
        response_content = get_api_response(5002)
    else:
        pytest.fail(f"URL[={request_url}] not implemented: ")
    response = Response()
    response.status_code = response_code
    response._content = str.encode(response_content)
    return response


def get_api_response(code: int) -> string:
    with open(f"tests/ApiResponses/{code}.json") as f:
        return f.read()


def get_expiration_datetime() -> datetime:
    data = json.loads(get_api_response(200))
    return datetime.fromtimestamp(int(data["account"]["expiry_unix"]))


@patch("sys.exit")
@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_ok(mock_get, mock_sys_exit, capsys):
    args = argparse.Namespace(account=200, warning=14, critical=7, verbose=False)
    expiration_datetime = get_expiration_datetime()
    expiration_string = expiration_datetime.strftime("%Y-%m-%d %H:%M:%S")
    mullvad = MullvadAccount(API_URL, args)
    mullvad.check_expiration_date(expiration_datetime - timedelta(days=15))
    captured = capsys.readouterr()
    assert (
        captured.out
        == f"OK - Mullvad VPN account expiration in 15 days ({expiration_string})\n"
    )
    mock_sys_exit.assert_called_once_with(0)


@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_warning(mock_get, capsys):
    args = argparse.Namespace(account=200, warning=16, critical=7, verbose=False)
    expiration_datetime = get_expiration_datetime()
    expiration_string = expiration_datetime.strftime("%Y-%m-%d %H:%M:%S")
    mullvad = MullvadAccount(API_URL, args)
    with pytest.raises(SystemExit) as system_exit:
        mullvad.check_expiration_date(expiration_datetime - timedelta(days=15))
    captured = capsys.readouterr()
    assert (
        captured.out
        == f"WARNING - Mullvad VPN account expiration in 15 days ({expiration_string})\n"
    )
    assert system_exit.value.args[0] == 1


@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_critical(mock_get, capsys):
    args = argparse.Namespace(account=200, warning=7, critical=16, verbose=False)
    expiration_datetime = get_expiration_datetime()
    expiration_string = expiration_datetime.strftime("%Y-%m-%d %H:%M:%S")
    mullvad = MullvadAccount(API_URL, args)
    with pytest.raises(SystemExit) as system_exit:
        mullvad.check_expiration_date(expiration_datetime - timedelta(days=15))
    captured = capsys.readouterr()
    assert (
        captured.out
        == f"CRITICAL - Mullvad VPN account expiration in 15 days ({expiration_string})\n"
    )
    assert system_exit.value.args[0] == 2


@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_account_not_found(mock_get, capsys):
    args = argparse.Namespace(account=404, warning=14, critical=7, verbose=False)
    mullvad = MullvadAccount(API_URL, args)
    with pytest.raises(SystemExit) as system_exit:
        mullvad.check_expiration_date(datetime.now())
    captured = capsys.readouterr()
    assert captured.out == "CRITICAL - Code 404: Mullvad account not found\n"
    assert system_exit.value.args[0] == 2


@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_error(mock_get, capsys):
    args = argparse.Namespace(account=500, warning=14, critical=7, verbose=False)
    mullvad = MullvadAccount(API_URL, args)
    with pytest.raises(SystemExit) as system_exit:
        mullvad.check_expiration_date(datetime.now())
    captured = capsys.readouterr()
    assert (
        captured.out
        == "UNKNOWN - Mullvad API did not respond with valid JSON (Returned code HTTP 500)\n"
    )
    assert system_exit.value.args[0] == 3


@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_invalid_json_account(mock_get, capsys):
    args = argparse.Namespace(account=5001, warning=14, critical=7, verbose=False)
    mullvad = MullvadAccount(API_URL, args)
    with pytest.raises(SystemExit) as system_exit:
        mullvad.check_expiration_date(datetime.now())
    captured = capsys.readouterr()
    assert (
        captured.out
        == "UNKNOWN - Error Occurred:  Account data missing in API return\n"
    )
    assert system_exit.value.args[0] == 3


@patch("requests.get", side_effect=mocked_requests_get)
def test_mullvad_invalid_json_account_exp(mock_get, capsys):
    args = argparse.Namespace(account=5002, warning=14, critical=7, verbose=False)
    mullvad = MullvadAccount(API_URL, args)
    with pytest.raises(SystemExit) as system_exit:
        mullvad.check_expiration_date(datetime.now())
    captured = capsys.readouterr()
    assert (
        captured.out == "UNKNOWN - Error Occurred:  Expiry date missing in API return\n"
    )
    assert system_exit.value.args[0] == 3
