"""
Parsers for parsing wanikani api to my notes system

this is also a hella lot of post-processing that is involved here to allow this
"""

def rad_get_uniq_name(subject: dict) -> str:
    return subject["data"]["meanings"][0]["meaning"]

def rad_get_required_media_from_wk(subject: dict) -> dict | None:
    if subject["data"]["characters"] is not None:
        return None

    # the svg element must always exist
    svg_elem = [
        s for s in subject["data"]["character_images"] if
        s["content_type"] == "image/svg+xml"
    ]

    return dict(
        filename=f"{rad_get_uniq_name(subject)}.svg",
        url=svg_elem[0]["url"],
    )

def rad_parse_from_wk(subject: dict) -> dict:
    data = dict()
    data["radical_name"] = subject["data"]["meanings"][0]["meaning"]

    # sometimes the character radical can be None,
    # in that case insert an svg with the unique name
    char = subject["data"]["characters"]
    if char is None:
        char = f'<img src="{rad_get_uniq_name(subject)}.svg">'
    data["radical"] = char

    data["radical_meaning"] = subject["data"]["meaning_mnemonic"]

    data["lesson_pos"] = subject["data"]["lesson_position"]
    data["sub_id"] = subject["id"]
    data["url"] = subject["object"] + "/" + subject["data"]["slug"]

    data["follow_up_ids"] = subject["data"]["amalgamation_subject_ids"]

    return data
