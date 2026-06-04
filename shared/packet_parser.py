import json
import logging

def encode_packet(data_dict):
    return json.dumps(data_dict) + "\n"

def decode_stream(buffer):
    packets = []
    while '\n' in buffer:
        message_str, buffer = buffer.split('\n', 1)
        message_str = message_str.strip()
        if not message_str:
            continue
        try:
            packets.append(json.loads(message_str))
        except json.JSONDecodeError:
            logging.warning("Menerima data korup dari stream, membuang packet.")
    return packets, buffer