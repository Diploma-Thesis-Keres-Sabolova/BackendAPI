from DataGathering.Utils.AuthBase import QueryAuth, HeaderAuth, AuthorizationAuth


def test_query_auth():
    auth = QueryAuth(param_name="api_key", api_key="12345")
    params = {"q": "search"}
    headers = {}

    auth.apply(params, headers)

    assert params["api_key"] == "12345"
    assert params["q"] == "search"
    assert headers == {}


def test_header_auth():
    auth = HeaderAuth(header_name="X-Auth-Token", prefix="Key", api_key="secret")
    params = {}
    headers = {"Content-Type": "application/json"}

    auth.apply(params, headers)

    assert headers["X-Auth-Token"] == "Key secret"
    assert params == {}


def test_bearer_auth():
    auth = AuthorizationAuth(prefix="Bearer", api_key="token_xy")
    params = {}
    headers = {}

    auth.apply(params, headers)

    assert headers["Authorization"] == "Bearer token_xy"