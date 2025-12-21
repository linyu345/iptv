import os
import re

# 输入输出文件
INPUT_FILE = "IPTV.txt"
OUTPUT_FILE = "IPTV.m3u"

# 台标和 EPG
LOGO_BASE = "https://gcore.jsdelivr.net/gh/taksssss/tv/icon/"
EPG_URL = "https://live.fanmingming.cn/e.xml"

# 完整频道分类（与 fofa_fetch.py 保持一致）
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
    ]
}

# 台标特殊映射
LOGO_SPECIAL_MAP = {
    "CCTV5+": "CCTV5+",
    "CHANNEL[V]": "Channel V",
    "凤凰卫视中文台": "凤凰中文",
    "凤凰卫视香港台": "凤凰香港",
    "凤凰卫视资讯台": "凤凰资讯",
    "凤凰卫视电影台": "凤凰电影",
}

def get_logo_url(ch_name):
    name = ch_name.strip()
    name = re.sub(r"[ -_]HD|高清|4K|超清|超高清|8K|plus|\+|Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ", "", name, flags=re.IGNORECASE)
    name = name.replace(" ", "").replace("&", "")
    filename = LOGO_SPECIAL_MAP.get(ch_name, name) + ".png"
    return LOGO_BASE + filename

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 未找到 {INPUT_FILE}，跳过生成 M3U")
        return

    # 收集所有有效行（保留更新时间、免责和符合分类的频道）
    valid_lines = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ",#genre#" in line:
                continue
            if "更新时间" in line or "Disclaimer" in line:
                valid_lines.append(line)
                continue
            if "," in line and "$" in line:
                ch_name = line.split(",", 1)[0].strip()
                if any(ch_name in chans for chans in CHANNEL_CATEGORIES.values()):
                    valid_lines.append(line)

    # 生成 M3U
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n\n')

        current_group = "未分类"
        for line in valid_lines:
            # 更新时间和免责视频
            if "更新时间" in line or "Disclaimer" in line:
                parts = line.split(",", 1)
                if len(parts) == 2:
                    title, url = parts
                    out.write(f'#EXTINF:-1 group-title="提示",{title.strip()}\n{url.strip()}\n\n')
                continue

            # 正常频道行：CCTV1,http://...$广东电信
            ch_name, rest = line.split(",", 1)
            ch_name = ch_name.strip()
            url_with_operator = rest.strip()  # 直接保留 http://...$广东电信

            # 确定分类
            for cat, chans in CHANNEL_CATEGORIES.items():
                if ch_name in chans:
                    current_group = cat
                    break

            # 标题只写纯频道名
            title = ch_name

            logo = get_logo_url(ch_name)

            out.write(f'#EXTINF:-1 tvg-name="{ch_name}" tvg-logo="{logo}" group-title="{current_group}",{title}\n')
            out.write(f"{url_with_operator}\n\n")  # 直接写带 $运营商 的完整字符串

    print(f"✅ {OUTPUT_FILE} 生成成功！")
    print(f"   - URL 行直接带 $运营商（如 http://...$广东电信）")
    print(f"   - 标题只显示纯频道名")
    print(f"   - 每个源独立一条目，严格标准兼容所有播放器")

if __name__ == "__main__":
    main()
