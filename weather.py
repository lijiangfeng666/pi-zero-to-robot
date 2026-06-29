"""
天气查询模块 — 树莓派语音机器人
数据源：中国天气网 weather.com.cn（主） + wttr.in（后备）
"""

import re
import json
import os
from collections import Counter

import requests


CITY_CODES = {
    "北京": "101010100", "上海": "101020100", "天津": "101030100", "重庆": "101040100",
    "广州": "101280101", "深圳": "101280601", "珠海": "101280701", "汕头": "101280501",
    "佛山": "101280301", "东莞": "101281601", "中山": "101281701", "惠州": "101280303",
    "湛江": "101281001", "江门": "101281101", "茂名": "101282001", "肇庆": "101280901",
    "梅州": "101280401", "汕尾": "101282101", "河源": "101281201", "清远": "101281301",
    "韶关": "101280201", "揭阳": "101281901", "阳江": "101281801", "潮州": "101281501",
    "云浮": "101281401",
    "杭州": "101210101", "宁波": "101210401", "温州": "101210701", "绍兴": "101210501",
    "嘉兴": "101210301", "金华": "101210901", "台州": "101210601", "湖州": "101210201",
    "丽水": "101210801", "舟山": "101211101",
    "南京": "101190101", "苏州": "101190401", "无锡": "101190201", "常州": "101191101",
    "南通": "101190501", "徐州": "101190801", "扬州": "101190601", "盐城": "101190701",
    "镇江": "101190301", "泰州": "101191201", "淮安": "101190901", "连云港": "101191001",
    "宿迁": "101191301",
    "成都": "101270101", "绵阳": "101270401", "德阳": "101272001", "宜宾": "101271101",
    "南充": "101270501", "泸州": "101271001", "达州": "101270601", "乐山": "101271401",
    "自贡": "101270301", "眉山": "101271501", "广元": "101272101", "遂宁": "101270701",
    "内江": "101271201", "广安": "101270801", "资阳": "101271301", "巴中": "101270901",
    "雅安": "101271701", "阿坝": "101271901", "甘孜": "101271801", "凉山": "101271601",
    "福州": "101230101", "厦门": "101230201", "泉州": "101230501", "漳州": "101230601",
    "莆田": "101230401", "龙岩": "101230701", "三明": "101230801", "南平": "101230901",
    "宁德": "101230301",
    "武汉": "101200101", "宜昌": "101200901", "襄阳": "101200201", "荆州": "101200801",
    "黄石": "101200601", "十堰": "101201101", "孝感": "101200401", "荆门": "101201401",
    "鄂州": "101200301", "黄冈": "101200501", "咸宁": "101200701", "随州": "101201201",
    "长沙": "101250101", "株洲": "101250301", "湘潭": "101250201", "衡阳": "101250401",
    "岳阳": "101251001", "常德": "101250601", "益阳": "101250701", "邵阳": "101250901",
    "郴州": "101250501", "永州": "101251401", "怀化": "101251201", "娄底": "101250801",
    "济南": "101120101", "青岛": "101120201", "烟台": "101120501", "潍坊": "101120601",
    "临沂": "101120901", "淄博": "101120301", "济宁": "101120701", "泰安": "101120801",
    "威海": "101121301", "日照": "101121001", "东营": "101121201", "聊城": "101121701",
    "德州": "101120401", "滨州": "101121101", "菏泽": "101121001", "枣庄": "101121401",
    "郑州": "101180101", "洛阳": "101180901", "开封": "101180801", "南阳": "101180701",
    "新乡": "101180301", "安阳": "101180201", "信阳": "101180601", "平顶山": "101180401",
    "商丘": "101181001", "许昌": "101180501", "周口": "101181401", "驻马店": "101181601",
    "石家庄": "101090101", "唐山": "101090501", "保定": "101090201", "邯郸": "101091001",
    "秦皇岛": "101091101", "廊坊": "101090601", "衡水": "101090801",
    "合肥": "101220101", "芜湖": "101220301", "蚌埠": "101220201", "马鞍山": "101220501",
    "安庆": "101220601", "黄山": "101221001", "阜阳": "101220801", "滁州": "101221101",
    "六安": "101221501", "宿州": "101220701", "淮南": "101220401", "淮北": "101221201",
    "南宁": "101300101", "桂林": "101300501", "柳州": "101300301", "北海": "101301301",
    "梧州": "101300601", "玉林": "101300901", "百色": "101301001", "钦州": "101301101",
    "河池": "101301201", "贵港": "101300801", "防城港": "101301401",
    "南昌": "101240101", "九江": "101240201", "赣州": "101240701", "景德镇": "101240801",
    "上饶": "101240301", "宜春": "101240501", "吉安": "101240601", "抚州": "101240401",
    "萍乡": "101240901", "新余": "101241001", "鹰潭": "101241101",
    "沈阳": "101070101", "大连": "101070201", "鞍山": "101070301", "抚顺": "101070401",
    "长春": "101060101", "吉林": "101060201", "哈尔滨": "101050101", "大庆": "101050901",
    "兰州": "101160101", "天水": "101160901", "酒泉": "101160801", "嘉峪关": "101161401",
    "武威": "101160501", "张掖": "101160701", "平凉": "101161301", "庆阳": "101160401",
    "定西": "101160201", "陇南": "101161001", "临夏": "101161101",
    "昆明": "101290101", "大理": "101290201", "丽江": "101291401", "西双版纳": "101291601",
    "曲靖": "101290401", "红河": "101290301", "玉溪": "101290701", "楚雄": "101291501",
    "昭通": "101291001", "文山": "101291101", "德宏": "101291501", "普洱": "101290901",
    "保山": "101290501", "怒江": "101291201", "迪庆": "101291301", "临沧": "101290801",
    "贵阳": "101260101", "遵义": "101260201", "六盘水": "101260801", "安顺": "101260301",
    "海口": "101310101", "三亚": "101310201",
    "呼和浩特": "101080101", "包头": "101080201", "鄂尔多斯": "101080701",
    "拉萨": "101140101", "日喀则": "101140201",
    "乌鲁木齐": "101130101", "克拉玛依": "101130201",
    "银川": "101170101", "西宁": "101150101",
    "台北": "101340101", "香港": "101320101", "澳门": "101330101",
}

DRSG_RULES = [
    (float('inf'), 36, "背心+短裤", "宽檐帽+墨镜，避免暴晒"),
    (36, 30, "短袖+短裤", "加防晒冰袖/帽子"),
    (30, 25, "短袖+薄长裤", "早晚备薄外套"),
    (25, 20, "薄长袖+棉麻长裤", "阴雨天加薄风衣"),
    (20, 15, "卫衣+休闲裤", "有风时内搭薄毛衣"),
    (15, 10, "薄毛衣+风衣", "必加围巾"),
    (10, 5, "轻羽绒+加绒裤", "帽子+围巾+厚袜"),
    (5, 1, "羽绒服+保暖内衣", "手套+围巾+防水靴"),
    (1, float('-inf'), "厚羽绒服+两层裤子", "全副武装，减少皮肤裸露"),
]

WEATHER_ALERTS = [
    "台风", "暴雪", "冰冻", "冻雨", "冰雹", "沙尘暴", "暴雨",
    "雷电", "雷阵雨", "大雨", "中雪", "大雪", "大风", "雾霾",
    "小雨", "小雪", "雨夹雪", "霜冻", "雾", "霾",
]

ALERT_LV = {
    "台风": "1", "暴雪": "1", "冰冻": "1", "冻雨": "1",
    "冰雹": "1", "沙尘暴": "1", "暴雨": "1",
    "雷电": "2", "雷阵雨": "2", "大雨": "2",
    "中雪": "2", "大雪": "2", "大风": "2", "雾霾": "2",
    "小雨": "3", "小雪": "3", "雨夹雪": "3",
    "霜冻": "3", "雾": "3", "霾": "3",
}

ALERT_ICON = {"1": "⚡", "2": "⚠", "3": "·"}

WTHR_KW = {
    "晴": "晴", "多云": "多云", "阴": "阴",
    "小雨": "小雨", "中雨": "中雨", "大雨": "大雨", "暴雨": "暴雨",
    "小雪": "小雪", "中雪": "中雪", "大雪": "大雪", "暴雪": "暴雪",
    "雷阵雨": "雷阵雨", "雷电": "雷电",
    "雨夹雪": "雨夹雪", "冻雨": "冻雨",
    "雾": "雾", "霾": "霾", "雾霾": "雾霾",
    "大风": "大风", "台风": "台风",
    "冰雹": "冰雹", "沙尘暴": "沙尘暴",
    "浮尘": "沙尘暴", "扬沙": "沙尘暴",
    "阵雨": "小雨", "强降雨": "大雨",
}

last_city = None
_city_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_city")


def query_weather(city, period="今天"):
    global last_city
    if not city:
        city = _get_last_city()
        if not city:
            return {"success": False, "text": "请问查哪个城市的天气"}

    data = _fetch_cn(city)
    if data is None:
        data = _fetch_wttrin(city)
    if data is None:
        return {"success": False, "text": f"{city}的天气暂时查不到，稍后再试"}

    _save_last_city(city)

    is_week = period in ("一周", "未来一周", "未来7天")
    text = _format_week(data) if is_week else _format_today(data)
    return {"success": True, "text": text, "city": city, "period": period, "data": data}


def _get_code(city):
    code = CITY_CODES.get(city)
    if code:
        return code
    clean = re.sub(r"[市县区]", "", city)
    code = CITY_CODES.get(clean)
    if code:
        return code
    for name, code in CITY_CODES.items():
        if clean in name or name in clean:
            return code
    return None


def _fetch_cn(city):
    code = _get_code(city)
    if not code:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://www.weather.com.cn/",
    }
    try:
        url = f"http://www.weather.com.cn/weather/{code}.shtml"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        if resp.status_code != 200:
            return None
        return _parse_cn(resp.text, city)
    except requests.RequestException:
        return None


def _parse_cn(html, city):
    forecasts = []
    ul = re.search(r'<ul[^>]*class="t[^"]*"[^>]*>(.*?)</ul>', html, re.S)
    if not ul:
        return None
    for li in re.findall(r"<li[^>]*>(.*?)</li>", ul.group(1), re.S):
        dm = re.search(r"<h1[^>]*>(.*?)</h1>", li)
        if not dm:
            continue
        date = dm.group(1).strip()
        cm = re.search(r'<p[^>]*class="wea"[^>]*>(.*?)</p>', li, re.S)
        cond = re.sub(r"<[^>]+>", "", cm.group(1)).strip() if cm else ""
        tm = re.search(r'<p[^>]*class="tem"[^>]*>(.*?)</p>', li, re.S)
        hi = lo = None
        if tm:
            h = re.search(r"<span>(.*?)</span>", tm.group(1))
            if h:
                hi = _to_int(h.group(1))
            l = re.search(r"/\s*<i>(.*?)</i>", tm.group(1))
            if l:
                lo = _to_int(l.group(1))
            elif not h:
                a = re.search(r"<i>(.*?)</i>", tm.group(1))
                if a:
                    hi = _to_int(a.group(1))
        wm = re.search(r'<p[^>]*class="win"[^>]*>(.*?)</p>', li, re.S)
        wind = re.sub(r"<[^>]+>", "", wm.group(1)).strip() if wm else ""
        forecasts.append({"date": date, "condition": cond, "temp_high": hi, "temp_low": lo, "wind": wind})
    return {"city": city, "forecasts": forecasts} if forecasts else None


def _fetch_wttrin(city):
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        resp = requests.get(url, headers={"User-Agent": "curl/8.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        forecasts = []
        for i, day in enumerate(data.get("weather", [])):
            labels = {0: "今天", 1: "明天", 2: "后天"}
            date = labels.get(i, f"第{i+1}天")
            cond = (day.get("hourly") or [{}])[0].get("lang_zh", [{}])[0].get("value", "")
            hi = _to_int(day.get("maxtempC"))
            lo = _to_int(day.get("mintempC"))
            forecasts.append({"date": date, "condition": cond, "temp_high": hi, "temp_low": lo, "wind": ""})
        return {"city": city, "forecasts": forecasts} if forecasts else None
    except Exception:
        return None


def _to_int(v):
    if v is None:
        return None
    try:
        return int(float(str(v).replace("°", "").replace("℃", "")))
    except (ValueError, TypeError):
        return None


def _get_drsg(max_temp):
    if max_temp is None:
        return None
    for hi, lo, cloth, tip in DRSG_RULES:
        if lo <= max_temp < hi:
            return cloth, tip
    return None


def _get_alerts(conditions):
    alerts = []
    seen = set()
    for cond in conditions:
        if not cond:
            continue
        std = None
        for kw, st in WTHR_KW.items():
            if kw in cond:
                std = st
                break
        if not std:
            std = cond
        if std in seen:
            continue
        seen.add(std)
        lv = ALERT_LV.get(std)
        if lv:
            alerts.append((std, lv))
    alerts.sort(key=lambda x: (WEATHER_ALERTS.index(x[0]) if x[0] in WEATHER_ALERTS else 99))
    return alerts[:2]


def _format_today(data):
    city = data["city"]
    fc = data.get("forecasts", [])
    if not fc:
        return f"{city}天气数据获取失败"
    today = fc[0]
    cond = today.get("condition") or "未知"
    hi = today.get("temp_high")
    lo = today.get("temp_low")
    drsg = _get_drsg(hi)
    parts = [f"{city}{today['date']}天气，{cond}"]
    tp = []
    if hi is not None:
        tp.append(f"最高{hi}°")
    if lo is not None:
        tp.append(f"最低{lo}°")
    if tp:
        parts.append("，".join(tp))
    if drsg:
        cloth, tip = drsg
        parts.append(f"穿搭建议：{cloth}")
        if tip:
            parts.append(f"（{tip}）")
    alerts = _get_alerts([cond])
    if alerts:
        ap = []
        for c, lv in alerts:
            icon = ALERT_ICON.get(lv, "")
            ap.append(f"{icon}注意：{c}")
        parts.append("；".join(ap))
    return "，".join(parts) + "。"


def _format_week(data):
    city = data["city"]
    fc = data.get("forecasts", [])
    if not fc:
        return f"{city}未来一周数据获取失败"
    conds = [f.get("condition", "") for f in fc]
    main_c = Counter(conds).most_common(1)[0][0] if conds else "未知"
    hi_vals = [f["temp_high"] for f in fc if f.get("temp_high") is not None]
    lo_vals = [f["temp_low"] for f in fc if f.get("temp_low") is not None]
    parts = [f"{city}未来一周"]
    tp = []
    if hi_vals:
        tp.append(f"最高{max(hi_vals)}°")
    if lo_vals:
        tp.append(f"最低{min(lo_vals)}°")
    if tp:
        parts.append("，".join(tp))
    parts.append(f"以{main_c}为主")
    drsg = _get_drsg(max(hi_vals) if hi_vals else None)
    if drsg:
        cloth, tip = drsg
        parts.append(f"穿搭建议：{cloth}")
        if tip:
            parts.append(f"（{tip}）")
    days = []
    for f in fc:
        al = _get_alerts([f.get("condition", "")])
        if al:
            days.append((f["date"], f["condition"], al[0]))
    days.sort(key=lambda x: (WEATHER_ALERTS.index(x[2][0]) if x[2][0] in WEATHER_ALERTS else 99))
    if days[:3]:
        sp = ["特殊天气提醒："]
        items = []
        for d, c, (ac, lv) in days[:3]:
            icon = ALERT_ICON.get(lv, "")
            short_d = re.sub(r"[（(].*?[）)]", "", d).strip()
            items.append(f"{short_d}{icon}{c}")
        sp.append("，".join(items))
        parts.append("".join(sp))
    return "，".join(parts) + "。"


def _get_last_city():
    global last_city
    if last_city:
        return last_city
    try:
        with open(_city_file, encoding="utf-8") as f:
            c = f.read().strip()
            if c:
                last_city = c
                return c
    except OSError:
        pass
    return None


def _save_last_city(city):
    global last_city
    last_city = city
    try:
        with open(_city_file, "w", encoding="utf-8") as f:
            f.write(city.strip())
    except OSError:
        pass


def get_weather(city, period="今天"):
    return query_weather(city, period)


if __name__ == "__main__":
    import sys
    cities = sys.argv[1:] or ["北京"]
    for c in cities:
        print(f"\n{c} 今天:", query_weather(c, "今天").get("text"))
        print(f"{c} 一周:", query_weather(c, "一周").get("text"))
