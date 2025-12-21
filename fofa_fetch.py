import os
import re
import requests
import time
import concurrent.futures
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区
FOFA_URLS = {
    "https://fofa.info/result?qbase64=aXB0di9saXZlL3poX2NuLmpzIiAmJiBjb3VudHJ5PSJDTiI=": "hotel_zh_cn.txt",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
IPTV_FILE = "IPTV.txt"

# 酒店源固定频道数字映射（实测常见对应，CCTV从1开始，卫视从20+）
CHANNEL_NUM_MAP = {
    "央视频道": {
        "CCTV1": 1, "CCTV2": 2, "CCTV3": 3, "CCTV4": 4, "CCTV5": 5, "CCTV6": 6, "CCTV7": 7, "CCTV8": 8,
        "CCTV9": 9, "CCTV10": 10, "CCTV11": 11, "CCTV12": 12, "CCTV13": 13, "CCTV14": 14, "CCTV15": 15,
        "CCTV16": 16, "CCTV17": 17, "CCTV4K": 18, "CCTV8K": 19,
        # 其他央视专栏频道数字不固定，暂不生成或手动加
    },
    "卫视频道": {
        "湖南卫视": 23, "浙江卫视": 24, "江苏卫视": 25, "东方卫视": 26, "北京卫视": 21, "广东卫视": 27,
        "深圳卫视": 28, "山东卫视": 29, "安徽卫视": 30, "湖北卫视": 31, "河南卫视": 32, "江西卫视": 33,
        "四川卫视": 34, "重庆卫视": 35, "黑龙江卫视": 36, "辽宁卫视": 37,
        # 其他卫视数字可根据实际测试补充
    },
    # 数字频道和地方频道数字不固定，暂不生成（避免无效链接）
}

# ===============================
# 计数逻辑
def get_run_count():
    if os.path.exists(COUNTER_FILE):
        try:
            return int(open(COUNTER_FILE).read().strip())
        except:
            return 0
    return 0

def save_run_count(count):
    open(COUNTER_FILE, "w").write(str(count))

def check_and_clear_files_by_run_count():
    os.makedirs(IP_DIR, exist_ok=True)
    count = get_run_count() + 1
    if count >= 73:
        print(f"第 {count} 次运行，清空 IP 目录")
        for f in os.listdir(IP_DIR):
            if f.endswith(".txt"):
                os.remove(os.path.join(IP_DIR, f))
        save_run_count(1)
        return "w", 1
    else:
        save_run_count(count)
        return "a", count

# ===============================
# 第一阶段：爬取酒店IP
def first_stage():
    all_ips = set()
    for url, filename in FOFA_URLS.items():
        print(f"正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            matches = re.findall(r'<a href="http://([^"]+)"', r.text)
            all_ips.update(m.strip().rstrip("/") for m in matches if ":" in m)
        except Exception as e:
            print(f"爬取失败：{e}")
        time.sleep(3)

    mode, run_count = check_and_clear_files_by_run_count()
    alive_ips = []
    print("快速检测IP存活（HEAD请求）...")
    def head_check(ip_port):
        try:
            r = requests.head(f"http://{ip_port}", timeout=10)
            if r.status_code < 400:
                return ip_port
        except:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(head_check, all_ips)
        alive_ips = [ip for ip in results if ip]

    print(f"存活IP：{len(alive_ips)} 个")
    # 简单写入一个文件（可选，按省份分可加回原逻辑）
    with open(os.path.join(IP_DIR, "hotel_alive.txt"), "w", encoding="utf-8") as f:
        for ip in sorted(alive_ips):
            f.write(ip + "\n")

    print(f"第一阶段完成，当前轮次：{run_count}")
    return alive_ips

# ===============================
# 第二阶段：生成频道链接（固定 /hls/{num}/index.m3u8）
def second_stage(alive_ips):
    print("第二阶段：生成酒店频道链接")
    lines = []
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "https://kakaxi-1.asia/LOGO/Disclaimer.mp4"

    lines.append(f"更新时间: {beijing_now}（北京时间）")
    lines.append("")
    lines.append("更新时间,#genre#")
    lines.append(f"{beijing_now},{disclaimer_url}")
    lines.append("")

    for category, ch_map in CHANNEL_NUM_MAP.items():
        lines.append(f"{category},#genre#")
        for ch_name, num in ch_map.items():
            for ip_port in alive_ips:
                url = f"http://{ip_port}/hls/{num}/index.m3u8"
                lines.append(f"{ch_name},{url}")
        lines.append("")

    with open(IPTV_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"IPTV.txt 生成完成，共 {sum(len(ch_map) for ch_map in CHANNEL_NUM_MAP.values()) * len(alive_ips)} 条频道链接（每个源所有频道）")

# ===============================
# 文件推送（无emoji）
def push_all_files():
    print("推送更新到 GitHub...")
    os.system('git config --global user.name "github-actions"')
    os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    os.system("git add 计数.txt ip/ IPTV.txt")
    os.system('git commit -m "自动更新：酒店IPTV源频道链接" || echo "无变更"')
    os.system("git push origin main || echo '推送失败'")

# ===============================
# 主逻辑（每次都完整生成）
if __name__ == "__main__":
    ips = first_stage()
    if ips:
        second_stage(ips)
    push_all_files()
