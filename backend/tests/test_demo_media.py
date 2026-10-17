from fastapi.testclient import TestClient
from releaseguard.api import create_app
from releaseguard.config import ROOT, Settings


def test_real_demo_media_range_and_caption_delivery():
    client = TestClient(create_app(Settings()))
    result = client.get('/demo-media/ReleaseGuard-demo.mp4', headers={'Range': 'bytes=0-31'})
    assert result.status_code == 206
    assert result.headers['content-type'] == 'video/mp4'
    assert result.content == (ROOT / 'demo/ReleaseGuard-demo.mp4').read_bytes()[:32]
    captions = client.get('/demo-media/captions.vtt')
    assert captions.status_code == 200 and captions.text.startswith('WEBVTT')
    assert client.get('/demo-media/.env').status_code == 404
    assert client.get('/demo-media/narration.txt').status_code == 404
