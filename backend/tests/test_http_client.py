from app.services.http_client import ca_bundle_path, ssl_context


def test_ssl_context_uses_certifi_ca_bundle():
    context = ssl_context()

    assert ca_bundle_path().endswith("cacert.pem")
    assert context.get_ca_certs()
