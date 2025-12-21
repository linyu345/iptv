import os
import re
import requests
import time
import concurrent.futures
import subprocess
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区（酒店源专用）
FOFA_URLS = {
    # 主关键词：酒店系统经典路径，命中率最高
    "https://fofa.info/result?qbase64=aXB0di9saXZlL3poX2NuLmpzIiAmJiBjb3VudHJ5PSJDTiI=": "hotel_zh_cn.txt",
    # 备选关键词（可选，增加覆盖）
    # "https://fofa.info/result?qbase64=dGl0bGU9ImhvdGVsIOa0qOiouSIgJiYgY291bnRyeT0iQ04i": "hotel_title.txt",
    # "https://fofa.info/result?qbase64=IkpIR1hUViIgJiYgY291bnRyeT0iQ04i": "hotel_zhgxtv.txt",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
ZUBO_FILE = "zubo.txt"
IPTV_FILE = "IPTV.txt"

# 酒店源常用播放路径模板（实测有效）
HOTEL_PATHS = [
    "",                                      # 根路径，很多直接出播放器或列表
    "iptv/live/zh_cn.js",                    # 频道列表JS
    "playlist.m3u8",                         # 直接M3U8
    "iptv/live/playlist.m3u8",
    "live.m3u8",
    "channellist.m3u8",
    "iptv/live/1000.json",                   # 部分酒店JSON列表
    "iptv/live/100.ts",                      # 示例TS流（用于检测是否活）
]

# 频道分类（保持你原来的，酒店源通常包含这些）
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV4欧洲", "CCTV4美洲", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17", "CCTV4K", "CCTV8K",
        "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场", "女性时尚", "世界地理", "央视台球", "高尔夫网球",
        "央视文化精品", "卫生健康", "电视指南", "中学生", "发现之旅", "书法频道", "国学频道", "环球奇观"
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视", "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视", "农林卫视", "山东教育卫视",
        "中国教育1台", "中国教育2台", "中国教育3台", "中国教育4台", "早期教育"
    ],
    "数字频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "淘电影", "淘精彩", "淘剧场", "淘4K", "淘娱乐", "淘BABY", "淘萌宠", "重温经典",
        "星空卫视", "CHANNEL[V]", "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视香港台", "凤凰卫视电影台", "求索纪录", "求索科学",
        "求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", "睛彩青少", "睛彩竞技", "睛彩篮球", "睛彩广场舞", "魅力足球", "五星体育",
        "劲爆体育", "快乐垂钓", "茶频道", "先锋乒羽", "天元围棋", "汽摩", "梨园频道", "文物宝库", "武术世界", "哒啵赛事", "哒啵电竞", "黑莓电影", "黑莓动画",
        "乐游", "生活时尚", "都市剧场", "欢笑剧场", "游戏风云", "金色学堂", "动漫秀场", "新动漫", "卡酷少儿", "金鹰卡通", "优漫卡通", "哈哈炫动", "嘉佳卡通",
        "中国交通", "中国天气", "华数4K", "华数星影", "华数动作影院", "华数喜剧影院", "华数家庭影院", "华数经典电影", "华数热播剧场", "华数碟战剧场",
        "华数军旅剧场", "华数城市剧场", "华数武侠剧场", "华数古装剧场", "华数魅力时尚", "华数少儿动画", "华数动画"
    ],
    "湖北": [
        "湖北公共新闻", "湖北经视频道", "湖北综合频道", "湖北垄上频道", "湖北影视频道", "湖北生活频道", "湖北教育频道", "武汉新闻综合", "武汉电视剧", "武汉科技生活",
        "武汉文体频道", "武汉教育频道", "阳新综合", "房县综合", "蔡甸综合",
    ],
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
    if count >= 73:  # 每73次清空一次，避免积累太多失效IP
        print(f"🧹 第 {count} 次运行，清空 {IP_DIR} 下所有 .txt 文件")
        for f in os.listdir(IP_DIR):
            if f.endswith(".txt"):
                os.remove(os.path.join(IP_DIR, f))
        save_run_count(1)
        return "w", 1
    else:
        save_run_count(count)
        return "a", count

# ===============================
# IP 运营商判断（保留，用于标注）
def get_isp(ip):
    if re.match(r"^(1[0-9]{2}|2[0-3]{2}|42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "电信"
    elif re.match(r"^(42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "联通"
    elif re.match(r"^(223|36|37|38|39|100|101|102|103|104|105|106|107|108|109|134|135|136|137|138|139|150|151|152|157|158|159|170|178|182|183|184|187|188|189)\.", ip):
        return "移动"
    else:
        return "未知"

# ===============================
# 第一阶段：爬取酒店源IP
def first_stage():
    all_ips = set()
    for url, filename in FOFA_URLS.items():
        print(f"📡 正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            # FOFA结果页中的IP:PORT链接
            urls_all = re.findall(r'<a href="http://([^"]+)"', r.text)
            all_ips.update(u.strip().rstrip("/") for u in urls_all if ":" in u)  # 去掉末尾斜杠
        except Exception as e:
            print(f"❌ 爬取失败：{e}")
        time.sleep(3)

    province_isp_dict = {}
    for ip_port in all_ips:
        try:
            ip = ip_port.split(":")[0]
            res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            data = res.json()
            province = data.get("regionName", "未知")
            isp = get_isp(ip)
            if isp == "未知":
                continue
            fname = f"{province}{isp}.txt"
            province_isp_dict.setdefault(fname, set()).add(ip_port)
        except Exception:
            continue

    mode, run_count = check_and_clear_files_by_run_count()
    for filename, ip_set in province_isp_dict.items():
        path = os.path.join(IP_DIR, filename)
        with open(path, mode, encoding="utf-8") as f:
            for ip_port in sorted(ip_set):
                f.write(ip_port + "\n")
        print(f"{path} 已{'覆盖' if mode=='w' else '追加'}写入 {len(ip_set)} 个 IP")
    print(f"✅ 第一阶段完成，当前轮次：{run_count}")
    return run_count

# ===============================
# 第二阶段：生成酒店源URL（不再依赖rtp文件夹）
def second_stage():
    print("🔔 第二阶段触发：生成酒店源 zubo.txt")
    combined_lines = []
    for ip_file in os.listdir(IP_DIR):
        if not ip_file.endswith(".txt"):
            continue
        ip_path = os.path.join(IP_DIR, ip_file)
        with open(ip_path, encoding="utf-8") as f:
            ip_ports = [line.strip() for line in f if line.strip()]

        province_operator = ip_file.replace(".txt", "")
        for ip_port in ip_ports:
            base_url = f"http://{ip_port}"
            for path in HOTEL_PATHS:
                full_url = base_url if not path else f"{base_url}/{path.lstrip('/')}"
                combined_lines.append(f"酒店直播源,{full_url}${province_operator}")

    # 去重
    unique = {}
    for line in combined_lines:
        url_part = line.split(",", 1)[1]
        if url_part not in unique:
            unique[url_part] = line

    with open(ZUBO_FILE, "w", encoding="utf-8") as f:
        for line in unique.values():
            f.write(line + "\n")
    print(f"🎯 第二阶段完成，共 {len(unique)} 条酒店源 URL")

# ===============================
# 第三阶段：检测存活源（代表路径检测）
def third_stage():
    print("🧩 第三阶段：检测酒店源存活，生成 IPTV.txt")
    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt 不存在，跳过")
        return

    def check_hotel_url(url_with_operator):
        url = url_with_operator.split("$")[0].strip()
        try:
            # 宽松检测：只要HTTP头返回200或有数据就通过
            r = requests.get(url, timeout=15, stream=True, headers=HEADERS)
            if r.status_code == 200 and len(r.content) > 100:  # 有内容
                return True
            return False
        except:
            return False

    ip_info = {}
    for fname in os.listdir(IP_DIR):
        if not fname.endswith(".txt"):
            continue
        province_operator = fname.replace(".txt", "")
        path = os.path.join(IP_DIR, fname)
        with open(path, encoding="utf-8") as f:
            for line in f:
                ip_port = line.strip()
                ip_info[ip_port] = province_operator

    valid_lines = []
    with open(ZUBO_FILE, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and "," in line and "$" in line]

    print(f"🚀 启动多线程检测（共 {len(lines)} 个酒店源）...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_hotel_url, line.split(",", 1)[1]) for line in lines]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if future.result():
                valid_lines.append(lines[i])

    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "https://kakaxi-1.asia/LOGO/Disclaimer.mp4"

    with open(IPTV_FILE, "w", encoding="utf-8") as f:
        f.write(f"更新时间: {beijing_now}（北京时间）\n\n")
        f.write("更新时间,#genre#\n")
        f.write(f"{beijing_now},{disclaimer_url}\n\n")
        for category in CHANNEL_CATEGORIES:
            f.write(f"{category},#genre#\n")
        f.write("\n")
        # 酒店源不按频道分类，直接全部列出
        for line in valid_lines:
            f.write(line + "\n")

    print(f"🎯 IPTV.txt 生成完成，共 {len(valid_lines)} 条存活酒店源")

# ===============================
# 文件推送
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    os.system('git config --global user.name "github-actions"')
    os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    os.system("git add 计数.txt")
    os.system("git add ip/*.txt || true")
    os.system("git add zubo.txt || true")
    os.system("git add IPTV.txt || true")
    os.system('git commit -m "自动更新：酒店IPTV源 IP + IPTV.txt" || echo "⚠️ 无需提交"')
    os.system("git push origin main || echo "⚠️ 推送失败"')

# ===============================
# 主执行逻辑
if __name__ == "__main__":
    run_count = first_stage()
    if run_count in [12, 24, 36, 48, 60, 72]:
        second_stage()
        third_stage()
    push_all_files()
