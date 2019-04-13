import os
import boto3
import json
from re import findall
from collections import defaultdict
from io import StringIO
from os.path import isdir, join

CPU_MEASURE = {
    'filepath': '/proc/cpuinfo',
    'patterns': [
        ['processor', r'^processor\s*:\s*(\d+)$'],
        ['model_name', r'^model\sname\s*:\s*(.*)'],
        ['vendor_id', r'^vendor_id\s*:\s*(.*)'],
        ['cpu_family', r'^cpu\sfamily\s*:\s*(.*)'],
        ['model', r'^model\s*:\s*(.*)'],
        ['cpu_mhz', r'^cpu\sMHz\s*:\s*(.*)'],
        ['cpu_cores', r'cpu\scores\s*:\s*(.*)'],
    ],
}
MEM_MEASURE = {
    'filepath': '/proc/meminfo',
    'patterns': [
        ['mem_total', r'MemTotal:\s*(.*)'],
        ['mem_free', r'MemFree:\s*(.*)'],
        ['mem_available', r'MemAvailable:\s*(.*)'],
    ],
}
s3 = boto3.client('s3')


def _regex_get(pattern, string, default):
    res = findall(pattern, string)
    return res[0] if res else default


def _parse_cpu(filepath, patterns):
    with open(filepath, 'r') as f:
        info = list()
        curr = -1
        for line in f:
            line = line.strip()
            for i, pair in enumerate(patterns):
                res = _regex_get(pair[1], line, None)
                # if line is "processor: <id>", switch to record info of this <id>
                if i == 0 and res:
                    info.append({})
                    curr += 1
                # if line has other wanted info, record it
                elif res:
                    info[curr][pair[0]] = res
        return info


def _parse_mem(filepath, patterns):
    with open(filepath, 'r') as f:
        info = dict()
        for line in f:
            line = line.strip()
            for i, pair in enumerate(patterns):
                res = _regex_get(pair[1], line, None)
                if res:
                    info[pair[0]] = res
        return info


def get_sys_info():
    with open('/proc/self/cgroup', 'r') as f:
        return {
            'instance_root_id': _regex_get(r'(sandbox-root-.{6})', f.read(), 'UNKNOWN'),
            'cpuinfo': _parse_cpu(CPU_MEASURE['filepath'], CPU_MEASURE['patterns']),
            'meminfo': _parse_mem(MEM_MEASURE['filepath'], MEM_MEASURE['patterns']),
        }


def upload(bucket, key, data, tmp_dir):
    os.system('mkdir ' + tmp_dir)
    tmp_filepath = join(tmp_dir, 'data.json')
    with open(tmp_filepath, 'w') as f:
        json.dump(data, f)
    s3.upload_file(tmp_filepath, bucket, key)
    os.remove(tmp_filepath)
