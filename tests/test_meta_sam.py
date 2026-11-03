"""MetaSamDetector without live calls: a fake HTTP session records the request
and returns constructed answers. Formats follow docs/meta-sam-api.md."""

import base64
import io
import json
from pathlib import Path

import pytest
import requests
from PIL import Image

from cutter.detectie.basis import DetectionError
from meta_sam_parser import SegmentationMask

from cutter.detectie.maskers import decode_raster
from cutter.detectie.meta_sam import (
    MetaSamDetector,
    SamRecord,
    build_request,
    decode_mask,
    extract_output_text,
    parse_output,
    point_prompt,
    prepare_image,
)


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def page(width=4000, height=5000):
    return Image.new("RGB", (width, height), "white")


def detector(response, parse=None, **kwargs):
    extra = {"parse": parse} if parse else {}
    return MetaSamDetector("test-key", session=FakeSession(response), **extra, **kwargs)


# Constructed from the documented grammar, with the 5x5 one_bit example mask
# from Meta's meta-sam-parser README.
SMALL_OUTPUT = (
    "<0f>0<|box;x1=1;y1=1;x2=5;y2=5;w=10;h=10;c=0.9|><|mask;x=0;y=0;c=0.9;data=5,5,!!!!!(QO(0lu8?|>"
)
SMALL_RASTER = [1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1]


def test_prepare_image_downscales_and_reports_scale():
    data_url, size, scale = prepare_image(page(4000, 5000), max_width=2000)
    assert size == (2000, 2500)
    assert scale == 2.0
    assert data_url.startswith("data:image/jpeg;base64,")
    sent = Image.open(io.BytesIO(base64.b64decode(data_url.split(",", 1)[1])))
    assert sent.size == (2000, 2500)


def test_small_image_is_not_upscaled():
    _, size, scale = prepare_image(page(800, 1000), max_width=2000)
    assert size == (800, 1000) and scale == 1.0


def test_request_body_follows_documentation():
    body = build_request("sam-3.1", "pistol", "data:image/jpeg;base64,AAA")
    assert body["model"] == "sam-3.1"
    content = body["input"][0]["content"]
    assert content[0] == {"type": "input_text", "text": "pistol"}
    assert content[1] == {"type": "input_image", "image_url": "data:image/jpeg;base64,AAA"}
    assert body["metadata"] == {"mask_encoding": "lossless", "include_confidence": "true"}
    assert body["stream"] is False


def test_point_prompt_syntax():
    assert point_prompt(20.4, 40.6, (640, 480)) == "<0f>1<|point;x=20;y=40;w=640;h=480|>"


@pytest.mark.parametrize(
    "body",
    [
        {"output_text": "<0f>0<|box;...|>"},
        {"output": [{"type": "message", "content": [{"type": "output_text", "text": "<0f>0<|box;...|>"}]}]},
    ],
)
def test_extract_output_text(body):
    assert extract_output_text(body) == "<0f>0<|box;...|>"


def test_detect_posts_to_responses_endpoint():
    d = detector(FakeResponse(200, {"output_text": ""}), base_url="https://api.meta.ai/v1/")
    assert d.detect(page(), "pistol") == []
    call = d.session.calls[0]
    assert call["url"] == "https://api.meta.ai/v1/responses"
    assert call["headers"]["Authorization"] == "Bearer test-key"
    assert call["json"]["input"][0]["content"][0]["text"] == "pistol"


def test_records_are_scaled_back_to_native_pixels():
    mask = SegmentationMask(encoding="one_bit", payload="!!!!!(QO(0lu8?", width=5, height=5)
    records = [
        SamRecord("0", 100, 200, 300, 260, 0.91, mask),
        SamRecord("2", 0, 0, 10, 10, None),
    ]
    d = detector(FakeResponse(200, {"output_text": "x"}), parse=lambda text: records)
    objects = d.detect(page(4000, 5000), "pistol")  # sent at 2000 px: scale 2
    assert objects[0].box == {"x": 200, "y": 400, "w": 400, "h": 120}
    assert objects[0].score == 0.91
    assert objects[0].mask_data["width"] == 5 and objects[0].mask_data["encoding"] == "one_bit"
    assert decode_raster(objects[0].mask_data).flatten().tolist() == SMALL_RASTER
    assert objects[0].herkomst["model"] == "sam-3.1"
    assert objects[0].herkomst["prompt"] == "pistol"
    assert objects[0].herkomst["verstuurde_afmetingen"] == [2000, 2500]
    assert objects[1].mask_data is None and objects[1].id == "sam-2"
    assert objects[0].to_dict()["masker"]["height"] == 5


def test_parse_small_output_with_official_parser():
    records = parse_output(SMALL_OUTPUT)
    assert len(records) == 1
    r = records[0]
    assert (r.object_id, r.left, r.top, r.right, r.bottom, r.confidence) == ("0", 1, 1, 6, 6, 0.9)  # x2/y2 inclusive
    assert list(decode_mask(r)) == SMALL_RASTER


def test_detect_end_to_end_with_small_output():
    d = detector(FakeResponse(200, {"output_text": SMALL_OUTPUT}))
    (obj,) = d.detect(page(20, 20), "pistol")  # not downscaled
    assert obj.box == {"x": 1, "y": 1, "w": 5, "h": 5}
    assert decode_raster(obj.mask_data).flatten().tolist() == SMALL_RASTER


def test_empty_output_means_no_objects():
    assert parse_output("  ") == []


def test_point_prompt_uses_sent_pixels_and_one_bit():
    d = detector(FakeResponse(200, {"output_text": ""}))
    d.detect_point(page(4000, 5000), 1000, 1500)
    body = d.session.calls[0]["json"]
    assert body["input"][0]["content"][0]["text"] == "<0f>1<|point;x=500;y=750;w=2000;h=2500|>"
    assert body["metadata"]["mask_encoding"] == "one_bit"


def test_missing_key_never_calls_the_api():
    d = MetaSamDetector(None, session=FakeSession(FakeResponse(200, {})))
    with pytest.raises(DetectionError, match="MODEL_API_KEY"):
        d.detect(page(), "pistol")
    assert d.session.calls == []


@pytest.mark.parametrize(
    "response, status, retry, text",
    [
        (FakeResponse(400, {"error": {"code": "invalid", "message": "more than 16 objects"}}), 400, False, "more than 16 objects"),
        (FakeResponse(401, {"error": {}}), 503, False, "API-sleutel"),
        (FakeResponse(404, {"error": {"code": "model_not_found"}}), 503, False, "niet gevonden"),
        (FakeResponse(429, ValueError()), 429, True, "Te veel verzoeken"),
        (FakeResponse(500, ValueError()), 502, True, "HTTP 500"),
        (requests.ConnectionError(), 502, True, "niet bereikbaar"),
    ],
)
def test_errors(response, status, retry, text):
    with pytest.raises(DetectionError) as exc:
        detector(response).detect(page(), "pistol")
    assert exc.value.status == status
    assert exc.value.retry is retry
    assert text in exc.value.message


# Real response recorded once on 2026-11-01 (approved live call): Algemeen
# Handelsblad 19-02-1869, page 1, prompt "illustration". The page is all
# text, so SAM found nothing.
REAL_EMPTY = Path(__file__).parent / "fixtures" / "meta_sam" / "ah1869_p001_illustration.json"


def test_real_response_without_matches():
    recorded = json.loads(REAL_EMPTY.read_text(encoding="utf-8"))
    body = recorded["antwoord"]
    assert recorded["status"] == 200 and body["status"] == "completed"
    assert body["usage"]["images_processed"] == 1
    assert extract_output_text(body) == ""
    d = detector(FakeResponse(200, body))
    assert d.detect(page(), "illustration") == []


# Second real response (approved live call, 2026-11-01): NRC Handelsblad
# 02-01-1990, page 1 (native 4947 x 6903), prompt "photograph", sent at 2000 px.
REAL_PHOTO = Path(__file__).parent / "fixtures" / "meta_sam" / "nrc1990_p001_photograph.json"


def test_real_response_with_one_photograph():
    body = json.loads(REAL_PHOTO.read_text(encoding="utf-8"))["antwoord"]
    (record,) = parse_output(extract_output_text(body))
    assert (record.left, record.top, record.right, record.bottom) == (747, 562, 1915, 1374)
    assert 0.5 < record.confidence < 0.51
    assert record.mask.encoding == "lossless"
    # The mask raster covers the box at a lower resolution, same aspect ratio.
    assert (record.mask.width, record.mask.height) == (1024, 712)
    box_ratio = (record.right - record.left) / (record.bottom - record.top)
    assert abs(record.mask.width / record.mask.height - box_ratio) < 0.01
    raster = decode_mask(record)
    assert len(raster) == 1024 * 712 and set(raster) == {0, 1}
    assert 0.9 < sum(raster) / len(raster) < 0.97  # a rectangular photo, nearly filled


def test_real_response_scaled_to_native_page():
    body = json.loads(REAL_PHOTO.read_text(encoding="utf-8"))["antwoord"]
    d = detector(FakeResponse(200, body))
    (obj,) = d.detect(page(4947, 6903), "photograph")
    assert d.session.calls[0]["json"]["input"][0]["content"][0]["text"] == "photograph"
    assert obj.herkomst["verstuurde_afmetingen"] == [2000, 2791]
    scale = 4947 / 2000
    assert obj.box == {"x": round(747 * scale), "y": round(562 * scale), "w": round(1168 * scale), "h": round(812 * scale)}
    assert (obj.mask_data["width"], obj.mask_data["height"]) == (1024, 712)


def test_native_size_overrides_scale():
    """The service sends a 2000 px image and passes the native page size."""
    records = [SamRecord("0", 100, 100, 200, 200, 0.8)]
    d = detector(FakeResponse(200, {"output_text": "x"}), parse=lambda text: records)
    (obj,) = d.detect(page(2000, 2500), "pistol", native_size=(5000, 6250))
    assert obj.box == {"x": 250, "y": 250, "w": 250, "h": 250}


def test_box_prompt_wire_syntax():
    from cutter.detectie.meta_sam import box_prompt

    assert box_prompt({"x": 10, "y": 20, "w": 30.4, "h": 40}, (2000, 1500)) == "<0f>1<|box;x1=10;y1=20;x2=40;y2=60;w=2000;h=1500|>"


def test_detect_box_scales_to_sent_pixels():
    session = FakeSession(FakeResponse(200, {"output_text": ""}))
    sam = MetaSamDetector("test-key", session=session, max_width=1000)
    assert sam.detect_box(page(4000, 5000), {"x": 400, "y": 800, "w": 400, "h": 400}, native_size=(4000, 5000)) == []
    sent = session.calls[0]["json"]
    assert sent["input"][0]["content"][0]["text"] == "<0f>1<|box;x1=100;y1=200;x2=200;y2=300;w=1000;h=1250|>"
    assert sent["metadata"]["mask_encoding"] == "one_bit"
