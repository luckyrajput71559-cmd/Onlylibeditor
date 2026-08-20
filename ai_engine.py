#!/usr/bin/env python3
# AI OFFSET + HIDDEN PANEL DETECTOR
# Developer: @VICKYGAMING0

import os
import re
import subprocess
import base64
import random

class AIOffsetEngine:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.strings_with_offset = []
        self._load_data()
        self._extract_strings()
    
    def _load_data(self):
        with open(self.file_path, "rb") as f:
            self.data = f.read()
    
    def _extract_strings(self):
        try:
            result = subprocess.run(
                ["strings", "-t", "x", self.file_path],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        self.strings_with_offset.append({
                            "offset": parts[0],
                            "string": " ".join(parts[1:])
                        })
        except:
            pass
    
    def detect_offset(self, search_string):
        for item in self.strings_with_offset:
            if search_string in item["string"]:
                return int(item["offset"], 16)
        return None
    
    def detect_function_boundary(self, offset):
        try:
            result = subprocess.run(
                ["objdump", "-d", self.file_path],
                capture_output=True,
                text=True
            )
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if f"<" in line and ">:" in line:
                    func_start = int(line.split()[0], 16)
                    func_end = None
                    for j in range(i+1, len(lines)):
                        if "<" in lines[j] and ">:" in lines[j]:
                            func_end = int(lines[j].split()[0], 16)
                            break
                    if func_start <= offset < (func_end or offset + 100):
                        return {"start": func_start, "end": func_end}
        except:
            pass
        return {"start": offset - 50, "end": offset + 100}
    
    def is_hidden_panel(self, url):
        if re.search(r'[^\x00-\x7F]', url):
            return True
        try:
            base64.b64decode(url)
            return True
        except:
            pass
        return False
    
    def decrypt_hidden_panel(self, encrypted_url):
        methods = [
            self._xor_decrypt,
            self._base64_decrypt,
            self._reverse_decrypt,
            self._rot13_decrypt
        ]
        for method in methods:
            try:
                decrypted = method(encrypted_url)
                if "http" in decrypted:
                    return decrypted
            except:
                pass
        return encrypted_url
    
    def _xor_decrypt(self, data):
        key = 0x5A
        return ''.join(chr(ord(c) ^ key) for c in data)
    
    def _base64_decrypt(self, data):
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    
    def _reverse_decrypt(self, data):
        return data[::-1]
    
    def _rot13_decrypt(self, data):
        return ''.join(chr((ord(c) - 65 + 13) % 26 + 65) if c.isupper() else
                      chr((ord(c) - 97 + 13) % 26 + 97) if c.islower() else c for c in data)
    
    def deep_replace(self, old_url, new_url):
        offset = self.detect_offset(old_url)
        if offset is None:
            for item in self.strings_with_offset:
                if old_url[:10] in item["string"]:
                    offset = int(item["offset"], 16)
                    break
        if offset is None:
            return False, "URL not found"
        
        if self.is_hidden_panel(old_url):
            old_url = self.decrypt_hidden_panel(old_url)
        
        func = self.detect_function_boundary(offset)
        
        old_bytes = old_url.encode('utf-8')
        new_bytes = new_url.encode('utf-8')
        old_len = len(old_bytes)
        new_len = len(new_bytes)
        
        if new_len < old_len:
            new_bytes = new_bytes + b'\x00' * (old_len - new_len)
        elif new_len > old_len:
            new_bytes = new_bytes[:old_len]
        
        new_data = self.data[:offset] + new_bytes + self.data[offset + old_len:]
        
        with open(self.file_path, "wb") as f:
            f.write(new_data)
        
        return True, f"Offset: {hex(offset)}, Old Len: {old_len}, New Len: {len(new_bytes)}"