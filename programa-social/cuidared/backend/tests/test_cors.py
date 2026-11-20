def test_cors_permite_origen_web(client):
    r = client.options(
        "/auth/login",
        headers={
            "Origin": "https://cuidared.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] in ("*", "https://cuidared.example")
