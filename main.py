import pandas as pd
import re
import os
import json
import requests
import yaml
import ipaddress
import subprocess
from io import StringIO

# 映射字典
MAP_DICT = {'DOMAIN-SUFFIX': 'domain_suffix', 'HOST-SUFFIX': 'domain_suffix', 'host-suffix': 'domain_suffix', 'DOMAIN': 'domain', 'HOST': 'domain', 'host': 'domain',
            'DOMAIN-KEYWORD':'domain_keyword', 'HOST-KEYWORD': 'domain_keyword', 'host-keyword': 'domain_keyword', 'IP-CIDR': 'ip_cidr',
            'ip-cidr': 'ip_cidr', 'IP-CIDR6': 'ip_cidr', 
            'IP6-CIDR': 'ip_cidr','SRC-IP-CIDR': 'source_ip_cidr', 'GEOIP': 'geoip', 'DST-PORT': 'port',
            'SRC-PORT': 'source_port', "URL-REGEX": "domain_regex", "DOMAIN-REGEX": "domain_regex",
            'PROCESS-NAME': 'process_name', 'process-name': 'process_name'}

def is_remote(link):
    return link.startswith('http://') or link.startswith('https://')

def repo_path(link):
    if os.path.isabs(link):
        return link
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), link)

def read_text(link):
    # 远程链接保持原来的请求方式；仓库内相对路径按 main.py 所在目录解析
    if is_remote(link):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        return response.text
    with open(repo_path(link), 'r', encoding='utf-8') as handle:
        return handle.read()

def read_yaml_from_url(url):
    return yaml.safe_load(read_text(url))

def read_list_from_url(url):
    if is_remote(url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        text = response.text
    else:
        text = read_text(url)
    csv_data = StringIO(text)
    df = pd.read_csv(csv_data, header=None, names=['pattern', 'address', 'other', 'other2', 'other3'], on_bad_lines='skip')
    filtered_rows = []
    rules = []
    # 处理逻辑规则
    if 'AND' in df['pattern'].values:
        and_rows = df[df['pattern'].str.contains('AND', na=False)]
        for _, row in and_rows.iterrows():
            rule = {
                "type": "logical",
                "mode": "and",
                "rules": []
            }
            pattern = ",".join(row.values.astype(str))
            components = re.findall(r'\((.*?)\)', pattern)
            for component in components:
                for keyword in MAP_DICT.keys():
                    if keyword in component:
                        match = re.search(f'{keyword},(.*)', component)
                        if match:
                            value = match.group(1)
                            rule["rules"].append({
                                MAP_DICT[keyword]: value
                            })
            rules.append(rule)
    for index, row in df.iterrows():
        if 'AND' not in row['pattern']:
            filtered_rows.append(row)
    df_filtered = pd.DataFrame(filtered_rows, columns=['pattern', 'address', 'other', 'other2', 'other3'])
    return df_filtered, rules

def is_ipv4_or_ipv6(address):
    try:
        ipaddress.IPv4Network(address)
        return 'ipv4'
    except ValueError:
        try:
            ipaddress.IPv6Network(address)
            return 'ipv6'
        except ValueError:
            return None

def parse_and_convert_to_dataframe(link):
    rules = []
    # 根据链接扩展名分情况处理
    if link.endswith('.yaml') or link.endswith('.txt'):
        try:
            yaml_data = read_yaml_from_url(link)
            rows = []
            if not isinstance(yaml_data, str):
                items = yaml_data.get('payload', [])
            else:
                lines = yaml_data.splitlines()
                line_content = lines[0]
                items = line_content.split()
            for item in items:
                address = item.strip("'")
                if ',' not in item:
                    if is_ipv4_or_ipv6(item):
                        pattern = 'IP-CIDR'
                    else:
                        if address.startswith('+') or address.startswith('.'):
                            pattern = 'DOMAIN-SUFFIX'
                            address = address[1:]
                            if address.startswith('.'):
                                address = address[1:]
                        else:
                            pattern = 'DOMAIN'
                else:
                    pattern, address = item.split(',', 1)
                if ',' in address:
                    address = address.split(',', 1)[0]
                rows.append({'pattern': pattern.strip(), 'address': address.strip(), 'other': None})
            df = pd.DataFrame(rows, columns=['pattern', 'address', 'other'])
        except:
            df, rules = read_list_from_url(link)
    else:
        df, rules = read_list_from_url(link)
    return df, rules

# 对字典进行排序，含list of dict
def sort_dict(obj):
    if isinstance(obj, dict):
        return {k: sort_dict(obj[k]) for k in sorted(obj)}
    elif isinstance(obj, list) and all(isinstance(elem, dict) for elem in obj):
        return sorted([sort_dict(x) for x in obj], key=lambda d: sorted(d.keys())[0])
    elif isinstance(obj, list):
        return sorted(sort_dict(x) for x in obj)
    else:
        return obj

def output_stem(link):
    return os.path.basename(link).split('.')[0]

def parse_source_line(line):
    # `name=URL` 或 `name=仓库内路径`：同名行合并成一个规则集。
    # 普通 URL 仍按文件名分组，和以前一样（例如两个 Telegram.list）。
    stripped = line.strip()
    name, sep, location = stripped.partition('=')
    if (
        sep
        and name
        and location
        and '://' not in name
        and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name)
    ):
        return name, location
    return output_stem(line), line

def parse_list_file(links, output_directory, output_name=None):
    # 同一输出文件名的多个来源先合并再编译，避免后一个覆盖前一个（Telegram）
    if isinstance(links, str):
        links = [links]
    if not output_name:
        output_name = output_stem(links[0])
    frames = []
    for link in links:
        try:
            df, rules = parse_and_convert_to_dataframe(link)
            if df is None:
                raise ValueError('empty response')
            frames.append(df)
        except Exception as e:
            # 仓库内手工列表缺失应让构建失败；远程源失败仍跳过，避免单个上游拖垮全部规则集
            if not is_remote(link):
                raise
            print(f'获取链接出错，已跳过：{link}，原因：{str(e)}')
    if not frames:
        return None
    try:
        df = pd.concat(frames, ignore_index=True)  # 拼接为一个DataFrame
        df = df[~df['pattern'].str.contains('#', na=False)].reset_index(drop=True)  # 删除pattern中包含#号的行
        df = df[df['pattern'].isin(MAP_DICT.keys())].reset_index(drop=True)  # 删除不在字典中的pattern
        df['pattern'] = df['pattern'].replace(MAP_DICT)  # 替换pattern为字典中的值
        # 不同来源可能用 DOMAIN-SUFFIX / HOST-SUFFIX 表示同一规则，映射后再去重
        df['address'] = df['address'].astype(str).str.strip()
        df = df.drop_duplicates(subset=['pattern', 'address']).reset_index(drop=True)
        os.makedirs(output_directory, exist_ok=True)  # 创建自定义文件夹

        result_rules = {"version": 2, "rules": []}
        domain_entries = []
        for pattern, addresses in df.groupby('pattern')['address'].apply(list).to_dict().items():
            if pattern == 'domain_suffix':
                rule_entry = {pattern: [address.strip() for address in addresses]}
                result_rules["rules"].append(rule_entry)
                # domain_entries.extend([address.strip() for address in addresses])  # 1.9以下的版本需要额外处理 domain_suffix
            elif pattern == 'domain':
                domain_entries.extend([address.strip() for address in addresses])
            else:
                rule_entry = {pattern: [address.strip() for address in addresses]}
                result_rules["rules"].append(rule_entry)
        # 删除 'domain_entries' 中的重复值
        domain_entries = list(set(domain_entries))
        if domain_entries:
            result_rules["rules"].insert(0, {'domain': domain_entries})

        # 使用 output_directory 拼接完整路径
        file_name = os.path.join(output_directory, f"{output_name}.json")
        with open(file_name, 'w', encoding='utf-8') as output_file:
            result_rules_str = json.dumps(sort_dict(result_rules), ensure_ascii=False, indent=2)
            result_rules_str = result_rules_str.replace('\\\\', '\\')
            output_file.write(result_rules_str)

        srs_path = file_name.replace(".json", ".srs")
        completed = subprocess.run(
            ["sing-box", "rule-set", "compile", "--output", srs_path, file_name],
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f'sing-box rule-set compile failed for {file_name}')
        return file_name
    except RuntimeError:
        raise
    except Exception as e:
        print(f'生成规则集出错，已跳过：{", ".join(links)}，原因：{str(e)}')
        return None

# 读取 links.txt 中的每个链接并生成对应的 JSON 文件
with open("../links.txt", 'r') as links_file:
    links = links_file.read().splitlines()

links = [l for l in links if l.strip() and not l.strip().startswith("#")]

output_dir = "./"
result_file_names = []

grouped_links = {}
group_order = []
for line in links:
    name, location = parse_source_line(line)
    if name not in grouped_links:
        grouped_links[name] = []
        group_order.append(name)
    grouped_links[name].append(location)

for name in group_order:
    result_file_name = parse_list_file(grouped_links[name], output_directory=output_dir, output_name=name)
    result_file_names.append(result_file_name)

# 打印生成的文件名
# for file_name in result_file_names:
    # print(file_name)
