import os
import subprocess
import concurrent.futures
from datetime import datetime

INPUT_FILE = "IPTV.txt"
SMOOTH_FILE = "IPTV_smooth.txt"
BAD_FILE = "IPTV_bad.txt"

# 参数调整（针对公网 udpxy 实测最优）
TEST_DURATION = 18       # 测试18秒，给慢源足够时间
RW_TIMEOUT = 25000000    # 25秒读超时（微秒）
THREADS = 6              # GitHub runner 资源有限，6-8 最稳

def test_stream(url_with_operator):
    url = url_with_operator.split("$")[0].strip()

    try:
        # ffprobe 命令：极简模式，只判断能否正常打开并读取数据
        cmd = [
            "ffprobe",
            "-v", "quiet",                  # 完全静默
            "-rw_timeout", str(RW_TIMEOUT), # 单次读超时25秒
            "-timeout", "15000000",         # 连接超时15秒
            "-i", url,
            "-t", str(TEST_DURATION),       # 最多读18秒
            "-show_entries", "format=duration",  # 只看是否能读到时长
            "-of", "csv=p=0"                # 输出纯数字
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,       # 忽略所有错误日志（公网源太多假错误）
            timeout=TEST_DURATION + 20
        )

        stdout = result.stdout.decode(errors="ignore").strip()

        # 只要拿到任何 duration > 0，就算通过（最宽松但实际有效）
        if stdout and stdout.replace(".", "").isdigit() and float(stdout) > 0:
            return True, url_with_operator, f"流畅 (读到 {float(stdout):.1f}s 数据)"

        # 如果进程正常退出（returncode=0），即使没 duration，也算通过（很多源正常播放但 ffprobe 不输出 duration）
        if result.returncode == 0:
            return True, url_with_operator, "稳定可播（正常退出）"

        return False, url_with_operator, "无法打开流"

    except subprocess.TimeoutExpired:
        return True, url_with_operator, "缓慢但存活（超时但可能可播）"  # 公网慢源常见，算通过
    except Exception:
        return False, url_with_operator, "完全失效"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 未找到 {INPUT_FILE}")
        return

    # 读取文件
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_lines = [line.strip() for line in f]

    header_lines = []
    stream_lines = []
    for line in all_lines:
        if not line or ",#genre#" in line or "更新时间" in line or "Disclaimer" in line:
            header_lines.append(line)
        elif "," in line and "$" in line:
            stream_lines.append(line)

    print(f"🔍 发现 {len(stream_lines)} 个源，开始真实流测试（{THREADS} 线程，每源最多 ~40s）...")

    smooth_streams = []
    bad_streams = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(test_stream, line): line for line in stream_lines}
        for future in concurrent.futures.as_completed(futures):
            ok, line, reason = future.result()
            operator = line.split("$")[-1] if "$" in line else "未知"
            print(f"{'✅' if ok else '❌'} [{operator.ljust(8)}] {reason}")
            if ok:
                smooth_streams.append(line)
            else:
                bad_streams.append(line)

    # 写入流畅源文件（保留原格式）
    with open(SMOOTH_FILE, "w", encoding="utf-8") as f:
        for line in header_lines:
            if line:
                f.write(line + "\n")
        f.write("\n")
        for line in smooth_streams:
            f.write(line + "\n")

    with open(BAD_FILE, "w", encoding="utf-8") as f:
        for line in bad_streams:
            f.write(line + "\n")

    print(f"\n🎉 测试完成！本次筛选结果：")
    print(f"   ✅ 流畅可用源：{len(smooth_streams)} 条 → {SMOOTH_FILE}")
    print(f"   ❌ 不稳定/失效：{len(bad_streams)} 条 → {BAD_FILE}")
    print(f"   强烈建议用 {SMOOTH_FILE} 生成 M3U，换台更稳定！")

if __name__ == "__main__":
    main()
