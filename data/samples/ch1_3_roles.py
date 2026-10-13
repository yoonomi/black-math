"""从全量 portraits.md 抽出前三章：黑风山、黄风岭、小西天。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "portraits.md"
DST = ROOT / "data" / "samples" / "portraits_ch1_3.md"

KEEP = {
    # 人物
    "白衣秀士",
    "黑风山土地",
    "无头僧",
    "灵吉菩萨",
    "小西天土地",
    "申猴",
    "戌狗",
    "黄袍员外",
    "龟将",
    "石中人",
    "袁守诚",
    # 黑风山小妖
    "狼斥候",
    "狼剑客",
    "狼力士",
    "狼弓手",
    "狼校卫",
    "狼侍卫",
    "狼刺客",
    "山匪头子",
    "骨嶙峋",
    "蛇巡司",
    "小呱呱",
    "小菌君",
    "小人参精",
    # 黄风岭小妖
    "鸦香客",
    "鼠司空",
    "鼠校卫",
    "鼠弩手",
    "鼠都尉",
    "鼬侍郎",
    "狸侍长",
    "小灵芝精",
    "石双双",
    "石苍苍",
    # 小西天小妖
    "骨灵精",
    "骨悚然",
    "干尸",
    "疾蝠",
    "青蝠",
    "雪僵尸",
    "掌灯狱使",
    "穿云鬼",
    "狼护法",
    "戒刀僧",
    "夜叉奴",
    "巡山鬼",
    "双刀僧",
    "支应僧",
    "监院僧",
    "泥塑金刚",
    "冻饿鬼",
    "提炉僧",
    "焦面鬼王",
    "迎客僧",
    # 头目
    "牯护院",
    "广智",
    "广谋",
    "波里个浪",
    "地狼",
    "沙国王父子",
    "沙大郎",
    "百目真人",
    "浪里个波",
    "赤尻马猴",
    "虎伥",
    "疯虎",
    "石母",
    "魔将·莲眼",
    "不白",
    "海上僧",
    "魔将·妄相",
    "无量蝠",
    "浪里个浪",
    "老人参精",
    "不净",
    "不能",
    "不空",
    "魔将·劫波",
    # 妖王
    "灵虚子",
    "黑风大王",
    "黑熊精",
    "金池长老",
    "虎先锋",
    "石先锋",
    "黄风大圣",
    "亢金龙",
    "亢金星君",
    "魔将·妙音",
    "黄眉",
}


def main():
    text = SRC.read_text(encoding="utf-8")
    parts = [p.strip() for p in re.split(r"(?=## 影神图角色)", text) if p.strip()]
    kept = []
    names = []
    for part in parts:
        m = re.search(r"## 影神图角色\s+(\S+)", part)
        if not m:
            continue
        name = m.group(1)
        if name in KEEP:
            kept.append(part)
            names.append(name)
    DST.write_text("\n\n".join(kept) + "\n", encoding="utf-8")
    missing = sorted(KEEP - set(names))
    print("kept", len(kept), "chars", DST.stat().st_size)
    print("names", "、".join(names))
    if missing:
        print("missing", "、".join(missing))


if __name__ == "__main__":
    main()
