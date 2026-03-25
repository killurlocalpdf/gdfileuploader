"""
Basically, I tried to make File Uploader to Geometry Dash
Made the compression 1 MB ≈ 10k objects (still, its impossible to upload files, bigger than 5-6 MB, because of RobTop's server setting)

Special thanks to SweepSweep2 for the idea and for the "bytes into objects" compression method (with keys and other stuff). Lav u twin, mwah :>

Information that I used:
https://wyliemaster.github.io/gddocs/#/
https://www.youtube.com/watch?v=oENqzFJ3TgI

crack0holic was here
"""

import base64
import gzip
import os
import requests
import random
import zlib
import string
import hashlib

used_keys = [1, 6, 7, 8, 9, 10, 12, 20, 21, 23, 24, 25, 28, 29, 33, 34, 45, 46, 47, 50, 51, 54, 61, 63, 68, 69, 71, 72, 73, 75, 76, 77, 80, 84, 85, 90, 91, 92, 95, 97, 105, 107, 108, 113, 114, 115]
MIDDLE_KEYS = used_keys[1:]

def make_level(file_bytes: bytearray):
    start_of_level = "kS38,1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1000_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1001_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1009_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1002_5_1_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1013_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1014_7_1_15_1_18_0_8_1|1_125_2_255_3_0_11_255_12_255_13_255_4_-1_6_1005_5_1_7_1_15_1_18_0_8_1|1_0_2_255_3_255_11_255_12_255_13_255_4_-1_6_1006_5_1_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1004_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1012_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1007_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1011_7_1_15_1_18_0_8_1|,kA13,0,kA15,0,kA16,0,kA14,,kA6,0,kA7,0,kA25,0,kA17,0,kA18,0,kS39,0,kA2,0,kA3,0,kA8,0,kA4,0,kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,kA40,1,kA48,1,kA41,5,kA42,1,kA28,0,kA29,0,kA31,5,kA32,1,kA36,0,kA43,0,kA44,0,kA45,1,kA46,0,kA47,0,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,kA19,0,kA26,0,kA20,0,kA21,0,kA11,0;"
    current_x = 0
    current_y = 500
    i = 0
    level_string = ""
    object_count = 0
    def next_byte():
        nonlocal i
        if i < len(file_bytes):
            val = file_bytes[i]; i += 1; return val
        return 0xFF
    while i < len(file_bytes):
        id_byte = next_byte()
        parts = f"1,{id_byte + 1},2,{current_x},3,{current_y},"
        for key in MIDDLE_KEYS:
            a = next_byte()
            b = next_byte()
            parts += f"{key},{a * 256 + b},"
        b0 = next_byte()
        b1 = next_byte()
        b2 = next_byte()
        parts += f"22,{b0},{b1},{b2},0,0"
        level_string += parts + ";"
        object_count += 1
        current_y -= 30
        if current_y < 0:
            current_y = 500
            current_x += 30
    print(f"Packed {len(file_bytes)} bytes into {object_count} objects")
    return start_of_level + level_string, object_count

def parse_level(level_string: str):
    file_bytes = bytearray()
    objects = level_string.split(";")[1:]
    for obj in objects:
        if not obj.strip():
            continue
        parts = obj.split(",")
        kv = {}
        j = 0
        while j < len(parts) - 1:
            key = parts[j]
            if key == "22":
                kv["22"] = (parts[j+1], parts[j+2], parts[j+3])
                j += 6
            else:
                kv[key] = parts[j+1]
                j += 2
        if "1" not in kv:
            continue
        file_bytes.append((int(kv["1"]) - 1) & 0xFF)
        for key in MIDDLE_KEYS:
            packed = int(kv.get(str(key), 0xFFFF))
            packed = max(0, min(65535, packed))
            file_bytes.append((packed >> 8) & 0xFF)
            file_bytes.append(packed & 0xFF)
        if "22" in kv:
            file_bytes.append(int(kv["22"][0]) & 0xFF)
            file_bytes.append(int(kv["22"][1]) & 0xFF)
            file_bytes.append(int(kv["22"][2]) & 0xFF)
        else:
            file_bytes += bytearray([0xFF, 0xFF, 0xFF])
    while len(file_bytes) > 1 and file_bytes[-1] == 0xFF:
        file_bytes.pop()
    return file_bytes

if __name__ == "__main__":
    choice = int(input("1. Upload level\n2. Download level\n"))

    if choice == 1:
        username = input("Username: ")
        password = input("Password: ")
        file_path = input("File path to convert (use double-left-slash for paths): ")
        file_name = file_path.split("\\")[-1]
        with open(file_path, 'rb') as f:
            decimal_data = [b for b in f.read()]
        level_string, object_count = make_level(decimal_data)
        level_string = base64.urlsafe_b64encode(gzip.compress(level_string.encode(), compresslevel=1)).decode()
        try:
            r = requests.post("http://www.boomlings.com/database/getGJUsers20.php", data={"secret": "Wmfd2893gb7", "str": username, "gdw": "0", "page": "0", "total": "0"}, headers={"User-Agent": ""})
            if ":" not in r.text:
                acc_id, player_id = None, None
            else:
                parts = r.text.split(":")
                data = {parts[i]: parts[i+1] for i in range(0, len(parts)-1, 2)}
                acc_id, player_id = data.get("16"), data.get("2")
        except:
            acc_id, player_id = None, None
        gjp2 = hashlib.sha1((password + "mI29fmAnxgTs").encode()).hexdigest()
        chars = 50
        seed_data = level_string
        upload_seed = seed_data if len(seed_data) < chars else seed_data[::len(seed_data) // chars][:chars]
        chk_values = [upload_seed, "xI25fpAapCQg"]
        chk_string = "".join(map(str, chk_values))
        chk_hashed = hashlib.sha1(chk_string.encode()).hexdigest()
        chk_xored = "".join(chr(ord(c) ^ ord("41274"[i % len("41274")])) for i, c in enumerate(chk_hashed))
        seed2 = base64.urlsafe_b64encode(chk_xored.encode()).decode()
        level_params = {
            "userName": username,
            "accountID": acc_id,
            "uuid": player_id,
            "gjp2": gjp2,
            "gameVersion": "22",
            "binaryVersion": "45",
            "levelID": 0,
            "levelName": "".join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=12)),
            "levelDesc": base64.b64encode(file_name.encode()).decode(),
            "levelVersion": 1,
            "levelLength": 0,
            "audioTrack": 0,
            "auto": 0,
            "password": 0,
            "original": 0,
            "twoPlayer": 0,
            "songID": 0,
            "objects": object_count,
            "coins": 0,
            "requestedStars": 0,
            "unlisted": 0,
            "ldm": 0,
            "seed2": seed2,
            "levelString": level_string,
            "secret": "Wmfd2893gb7"
        }
        try:
            res = requests.post("http://www.boomlings.com/database/uploadGJLevel21.php", data=level_params, headers={"User-Agent": ""})
            if res.text.isdigit() or (len(res.text) > 1 and res.text[0] != '-'):
                print(f"Uploaded and got level as ID - {res.text}")
            else:
                print(f"Fail: {res.text} (the error could be because of a file that weights more than 5 MB, or because of rate-limit)")
        except Exception as e:
            print(f"[x] Error: {e}")

    elif choice == 2:
        level_id = int(input("Enter level ID: "))
        print("Downloading...")
        res = requests.post("http://www.boomlings.com/database/downloadGJLevel22.php", data={"levelID": level_id, "secret": "Wmfd2893gb7"}, headers={"User-Agent": ""})
        parts = res.text.split(":")
        level_string = None
        output_path = None
        for i, thing in enumerate(parts):
            if thing == "4":
                level_string = parts[i+1]
                break
            elif thing == "3":
                output_path = f"{level_id}_{base64.b64decode(str(parts[i+1])).decode()}"
        level_string = zlib.decompress(base64.urlsafe_b64decode(level_string.encode()), 15 | 32).decode()
        dec_list = parse_level(level_string)
        try:
            with open(output_path, "wb") as f:
                f.write(bytes(dec_list))
            print(f"Downloaded level as - {output_path}")
        except:
            print("Wrong level format")
    else:
        print("Invalid choice")
