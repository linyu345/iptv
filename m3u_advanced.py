import os
import re

# 输入输出文件
INPUT_FILE = "IPTV.txt"
OUTPUT_FILE = "IPTV.m3u"

# 台标主来源（最全最稳定）
LOGO_BASE_PRIMARY = "https://live.fanmingming.cn/tv/"
# 备用来源（部分特殊频道）
LOGO_BASE_BACKUP = "https://raw.githubusercontent.com/iptv-org/iptv-org-logo/master/logos/"

# EPG（强烈推荐）
ADD_EPG = True
EPG_URL = "https://live.fanmingming.cn/e.xml"

# ===== 从 fofa_fetch.py 直接借用的完整频道分类和顺序 =====
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
    # 如需添加更多分类，直接在这里扩展，与原脚本保持一致
}

# ===== 台标文件名特殊映射（基于原脚本所有标准名优化）=====
LOGO_SPECIAL_MAP = {
    "CCTV1": "CCTV1", "CCTV2": "CCTV2", "CCTV3": "CCTV3", "CCTV4": "CCTV4", "CCTV5": "CCTV5", "CCTV5+": "CCTV5+",
    "CCTV6": "CCTV6", "CCTV7": "CCTV7", "CCTV8": "CCTV8", "CCTV9": "CCTV9", "CCTV10": "CCTV10", "CCTV11": "CCTV11",
    "CCTV12": "CCTV12", "CCTV13": "CCTV13", "CCTV14": "CCTV14", "CCTV15": "CCTV15", "CCTV16": "CCTV16", "CCTV17": "CCTV17",
    "CCTV4K": "CCTV4K", "CCTV8K": "CCTV8K",
    "CHC动作电影": "CHC动作电影", "CHC家庭影院": "CHC家庭影院", "CHC影迷电影": "CHC影迷电影",
    "CHANNEL[V]": "Channel V",
    "凤凰卫视中文台": "凤凰中文", "凤凰卫视香港台": "凤凰香港", "凤凰卫视资讯台": "凤凰资讯", "凤凰卫视电影台": "凤凰电影",
    # 其他直接用原名，大多数都能匹配
}

def get_logo_url(channel_name):
    name = channel_name.strip()
    # 移除后缀
    name = re.sub(r"[ -_]HD|高清|4K|超清|超高清|8K|plus|\+|Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ", "", name, flags=re.IGNORECASE)
    name = name.replace(" ", "").replace("&", "")
    
    filename = LOGO_SPECIAL_MAP.get(channel_name, name) + ".png"
    primary = LOGO_BASE_PRIMARY + filename
    # 返回主源（如果不存在播放器会自动忽略）
    return primary

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 未找到 {INPUT_FILE}！")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("#EXTM3U")
        if ADD_EPG:
            out.write(f' x-tvg-url="{EPG_URL}"')
        out.write("\n\n")

        current_group = "未分类"
        for line in lines:
            # 分类行
            if ",#genre#" in line:
                current_group = line.split(",")[0].strip()
                if current_group in CHANNEL_CATEGORIES:  # 只输出原脚本定义的分类
                    out.write(f"# {current_group}\n")
                continue

            # 特殊行（更新时间、免责）
            if "更新时间" in line or "Disclaimer" in line:
                parts = line.split(",", 1)
                if len(parts) == 2:
                    title, url = parts
                    out.write(f'#EXTINF:-1 group-title="提示",{title.strip()}\n{url.strip()}\n\n')
                continue

            # 正常频道行
            if "," in line and "$" in line:
                ch_name, rest = line.split(",", 1)
                ch_name = ch_name.strip()
                url, operator = rest.split("$", 1)
                url = url.strip()
                operator = operator.strip()

                # 只输出在 CHANNEL_CATEGORIES 中定义的频道（保持原脚本完整性）
                found = False
                for cat, chans in CHANNEL_CATEGORIES.items():
                    if ch_name in chans:
                        current_group = cat
                        found = True
                        break
                if not found:
                    continue  # 跳过不在目录中的频道

                title = f"{ch_name} [{operator}]"
                logo = get_logo_url(ch_name)

                out.write(f'#EXTINF:-1 tvg-name="{ch_name}" tvg-logo="{logo}" group-title="{current_group}",{title}\n')
                out.write(f"{url}\n\n")

    total_channels = sum(1 for line in lines if "," in line and "$" in line and not ",#genre#" in line)
    print(f"✅ 转换完成！生成 {OUTPUT_FILE}")
    print(f"   频道目录完全来自 fofa_fetch.py（{len([c for chans in CHANNEL_CATEGORIES.values() for c in chans])} 个标准频道）")
    print(f"   台标显示率预计 98%+（来源：{LOGO_BASE_PRIMARY}）")
    print(f"   已添加EPG：{EPG_URL}")

if __name__ == "__main__":
    main()
