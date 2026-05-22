#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外劳电工信息汇总 — txt → HTML 自动生成脚本
用法: python build.py
输入: 外劳电工信息汇总.txt（统一格式，每条用 --- 分隔）
输出: 外劳电工信息汇总.html

新增岗位：在 txt 里复制现有条目格式填写，然后运行本脚本。
"""

import re, json, os, sys

TXT_FILE = "外劳电工信息汇总.txt"
HTML_FILE = "index.html"

# ═══════════════════════════════════════════
#  解析统一格式的 txt
# ═══════════════════════════════════════════

def parse_txt(filepath):
    """解析 txt，返回岗位列表。每条用 --- 分隔，字段为「标签：值」。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按 --- 行切分
    blocks = re.split(r'\n---+\s*\n', content)
    jobs = []
    job_id = 1

    for block in blocks:
        block = block.strip()
        if not block or block.startswith('#'):
            continue

        job = {
            "id": job_id,
            "title": "",
            "company": "",
            "salary": "",
            "age": "",
            "language": "",
            "workTime": "",
            "accommodation": "",
            "category": "",
            "requirement": "",
            "remark": "",
            "agent": "",
        }

        # 逐行解析 标签：值
        lines = block.split('\n')
        current_field = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 匹配 "标签：值" 或 "标签: 值"
            m = re.match(r'^([一-龥\w]+)[：:]\s*(.*)', line)
            if m:
                key = m.group(1).strip()
                value = m.group(2).strip()

                # 统一字段名
                key_lower = key.lower()
                if key in ('职位', '职位名称', '岗位', '岗位名称'):
                    job['title'] = value
                elif key in ('公司', '公司名称'):
                    job['company'] = value
                elif key in ('薪资', '薪资待遇', '薪酬', '工资', '薪金'):
                    job['salary'] = value
                elif key in ('年龄', '性别年龄', '年龄要求'):
                    job['age'] = value
                elif key in ('语言', '语言要求'):
                    job['language'] = value
                elif key in ('工时', '工作时间', '上班时间', '工作時長'):
                    job['workTime'] = value
                elif key in ('食宿', '食宿安排', '吃住'):
                    job['accommodation'] = value
                elif key in ('分类', '类别'):
                    job['category'] = value
                elif key in ('要求', '工作要求', '工作内容', '职位要求', '岗位要求'):
                    job['requirement'] = value
                elif key in ('备注', '注意', '其他'):
                    job['remark'] = value
                elif key in ('中介', '中介公司', '代理'):
                    job['agent'] = value
                else:
                    # 未知标签的内容追加到备注
                    if job['remark']:
                        job['remark'] += f'；{key}：{value}'
                    else:
                        job['remark'] = f'{key}：{value}'
            else:
                # 没有标签的续行，追加到 requirement
                if job['requirement']:
                    job['requirement'] += '；' + line
                else:
                    job['requirement'] = line

        # 跳过空条目
        if not job['title']:
            continue

        # 填充默认值
        job['company'] = job['company'] or '详见内文'
        job['salary'] = job['salary'] or '面议'
        job['age'] = job['age'] or '未注明'
        job['language'] = job['language'] or '未注明'
        job['workTime'] = job['workTime'] or '未注明'
        job['accommodation'] = job['accommodation'] or '未注明'
        job['category'] = job['category'] or '其他、全能技工'
        job['requirement'] = job['requirement'] or '详见原文'
        job['remark'] = job['remark'] or ''
        job['agent'] = job['agent'] or ''

        jobs.append(job)
        job_id += 1

    return jobs


# ═══════════════════════════════════════════
#  HTML 生成
# ═══════════════════════════════════════════

# 分类显示顺序（HTML 侧边栏用）
CATEGORY_ORDER = ["全部", "电工", "弱电技工", "水电、屋宇维修", "机械、工程技术员", "专才岗位", "其他、全能技工"]

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>外劳电工信息汇总</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f0f2f5; color: #333; display: flex; min-height: 100vh; }
.sidebar {
  width: 240px; background: #1a1a2e; color: #eee; flex-shrink: 0;
  display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh;
  overflow-y: auto; z-index: 10; transition: transform 0.3s;
}
.sidebar-header { padding: 24px 20px; border-bottom: 1px solid rgba(255,255,255,.1); }
.sidebar-header h2 { font-size: 18px; color: #fff; }
.sidebar-header p { font-size: 12px; color: #888; margin-top: 4px; }
.category-list { list-style: none; padding: 8px 0; flex: 1; }
.category-list li {
  padding: 12px 20px; cursor: pointer; display: flex; justify-content: space-between;
  align-items: center; font-size: 14px; transition: background .15s; border-left: 3px solid transparent;
}
.category-list li:hover { background: rgba(255,255,255,.05); }
.category-list li.active { background: rgba(255,255,255,.1); border-left-color: #4fc3f7; color: #4fc3f7; }
.category-list li .count { font-size: 11px; background: rgba(255,255,255,.15); padding: 2px 8px; border-radius: 10px; }
.category-list li.active .count { background: #4fc3f7; color: #1a1a2e; }
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar {
  background: #fff; padding: 16px 28px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}
.topbar .menu-btn { display: none; background: none; border: none; font-size: 24px; cursor: pointer; padding: 4px 8px; color: #555; }
.topbar .search-box { flex: 1; min-width: 200px; position: relative; }
.topbar .search-box input {
  width: 100%; padding: 10px 40px 10px 16px; border: 1px solid #ddd; border-radius: 8px;
  font-size: 14px; outline: none; transition: border .2s;
}
.topbar .search-box input:focus { border-color: #4fc3f7; }
.topbar .search-box .clear-btn {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; font-size: 18px; cursor: pointer; color: #999;
  display: none; line-height: 1;
}
.topbar .result-info { font-size: 13px; color: #888; white-space: nowrap; }
.content { flex: 1; padding: 20px 28px; overflow-y: auto; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.job-card {
  background: #fff; border-radius: 10px; padding: 20px; cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,.06); transition: transform .15s, box-shadow .15s;
  border-left: 4px solid transparent;
}
.job-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.job-card .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.job-card .card-title { font-size: 16px; font-weight: 600; color: #1a1a2e; flex: 1; }
.job-card .card-salary {
  font-size: 15px; font-weight: 700; color: #e65100; white-space: nowrap;
  background: #fff3e0; padding: 3px 10px; border-radius: 6px; margin-left: 8px;
}
.job-card .card-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.job-card .card-tag { font-size: 12px; padding: 3px 10px; border-radius: 12px; background: #e8f5e9; color: #2e7d32; }
.job-card .card-tag.lang { background: #e3f2fd; color: #1565c0; }
.job-card .card-tag.age { background: #fce4ec; color: #c62828; }
.job-card .card-tag.time { background: #f3e5f5; color: #7b1fa2; }
.job-card .card-tag.accom { background: #fff8e1; color: #f57f17; }
.job-card .card-tag.agent { background: #f5f5f5; color: #616161; }
.job-card .card-remark {
  font-size: 13px; color: #666; margin-top: 10px; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 100;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal {
  background: #fff; border-radius: 12px; max-width: 700px; width: 100%; max-height: 85vh;
  overflow-y: auto; box-shadow: 0 8px 30px rgba(0,0,0,.2); position: relative;
}
.modal-close {
  position: sticky; top: 12px; float: right; background: #eee; border: none;
  width: 32px; height: 32px; border-radius: 50%; font-size: 18px; cursor: pointer;
  z-index: 2; margin-right: 12px; display: flex; align-items: center; justify-content: center;
  transition: background .15s;
}
.modal-close:hover { background: #ddd; }
.modal-body { padding: 24px 28px 28px; clear: both; }
.modal-title { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; padding-right: 40px; }
.modal-company { font-size: 14px; color: #888; margin-bottom: 16px; }
.modal-salary {
  display: inline-block; font-size: 20px; font-weight: 700; color: #e65100;
  background: #fff3e0; padding: 6px 16px; border-radius: 8px; margin-bottom: 20px;
}
.modal-section { margin-bottom: 18px; }
.modal-section h4 { font-size: 14px; color: #999; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
.modal-section .info-row { display: flex; flex-wrap: wrap; gap: 12px; font-size: 14px; }
.modal-section .info-item { background: #f5f5f5; padding: 8px 14px; border-radius: 6px; white-space: nowrap; }
.modal-section .info-item strong { color: #555; margin-right: 4px; }
.modal-section .full-text { font-size: 14px; line-height: 1.7; color: #444; }
.modal-section .highlight-box {
  background: #fffde7; border: 1px solid #fff9c4; padding: 12px 16px;
  border-radius: 8px; font-size: 13px; color: #6d4c41; line-height: 1.6;
}
.empty { text-align: center; padding: 60px 20px; color: #999; }
.empty .icon { font-size: 48px; margin-bottom: 16px; }
.menu-mask { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 9; }
@media (max-width: 768px) {
  .sidebar { position: fixed; left: 0; top: 0; transform: translateX(-100%); height: 100vh; }
  .sidebar.open { transform: translateX(0); }
  .topbar .menu-btn { display: block; }
  .menu-mask.show { display: block; }
  .card-grid { grid-template-columns: 1fr; }
  .content { padding: 12px; }
  .topbar { padding: 12px; }
}
</style>
</head>
<body>

<div class="menu-mask" id="menuMask" onclick="toggleSidebar()"></div>

<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <h2>外劳电工信息</h2>
    <p>香港·澳门电工类职位</p>
  </div>
  <ul class="category-list" id="categoryList"></ul>
</aside>

<main class="main">
  <div class="topbar">
    <button class="menu-btn" onclick="toggleSidebar()">&#9776;</button>
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="搜索职位、技能、要求..." oninput="doSearch()">
      <button class="clear-btn" id="clearBtn" onclick="clearSearch()">&times;</button>
    </div>
    <span class="result-info" id="resultInfo"></span>
  </div>
  <div class="content">
    <div class="card-grid" id="cardGrid"></div>
    <div class="empty" id="emptyState" style="display:none">
      <div class="icon">&#128269;</div>
      <p>没有找到匹配的职位</p>
    </div>
  </div>
</main>

<div class="modal-overlay" id="modalOverlay" style="display:none" onclick="closeModal(event)">
  <div class="modal" id="modalBox" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>

<script>
var JOBS = __JOBS_DATA__;

var CATEGORY_ORDER = __CATEGORY_ORDER__;
var activeCategory = "全部";
var searchQuery = "";

function getVisibleCategories() {
  // 只保留至少有一条数据的分类
  var result = ["全部"];
  CATEGORY_ORDER.slice(1).forEach(function(cat) {
    if (JOBS.some(function(j) { return j.category === cat; })) {
      result.push(cat);
    }
  });
  return result;
}

function renderCategories() {
  var cats = getVisibleCategories();
  var list = document.getElementById('categoryList');
  list.innerHTML = cats.map(function(cat) {
    var count = cat === "全部" ? JOBS.length : JOBS.filter(function(j) { return j.category === cat; }).length;
    return '<li class="' + (cat === activeCategory ? 'active' : '') + '" onclick="selectCategory(\'' + cat.replace(/'/g, "\\'") + '\')"><span>' + cat + '</span><span class="count">' + count + '</span></li>';
  }).join('');
}

function getFilteredJobs() {
  return JOBS.filter(function(j) {
    var matchCat = activeCategory === "全部" || j.category === activeCategory;
    if (!matchCat) return false;
    if (!searchQuery) return true;
    var q = searchQuery.toLowerCase();
    return (j.title + j.company + j.salary + j.language + j.requirement + (j.remark||'') + j.category).toLowerCase().indexOf(q) !== -1;
  });
}

function renderCards() {
  var jobs = getFilteredJobs();
  var grid = document.getElementById('cardGrid');
  var empty = document.getElementById('emptyState');
  var info = document.getElementById('resultInfo');
  if (jobs.length === 0) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    info.textContent = '0 条结果';
  } else {
    empty.style.display = 'none';
    info.textContent = '共 ' + jobs.length + ' 条';
    grid.innerHTML = jobs.map(function(j) {
      return '<div class="job-card" onclick="openDetail(' + j.id + ')"><div class="card-header"><span class="card-title">' + esc(j.title) + '</span><span class="card-salary">' + esc(j.salary) + '</span></div><div class="card-remark">' + esc(j.requirement).substring(0, 80) + (j.requirement.length > 80 ? '...' : '') + '</div><div class="card-meta"><span class="card-tag lang">' + esc(j.language) + '</span><span class="card-tag age">' + esc(j.age) + '</span><span class="card-tag time">' + esc(j.workTime) + '</span><span class="card-tag accom">' + esc(j.accommodation) + '</span>' + (j.agent ? '<span class="card-tag agent">' + esc(j.agent) + '</span>' : '') + '</div></div>';
    }).join('');
  }
}

function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function selectCategory(cat) { activeCategory = cat; renderCategories(); renderCards(); }

function doSearch() {
  searchQuery = document.getElementById('searchInput').value.trim();
  document.getElementById('clearBtn').style.display = searchQuery ? 'block' : 'none';
  renderCards();
}

function clearSearch() {
  document.getElementById('searchInput').value = '';
  searchQuery = '';
  document.getElementById('clearBtn').style.display = 'none';
  renderCards();
}

function openDetail(jobId) {
  var job = JOBS.find(function(j) { return j.id === jobId; });
  if (!job) return;
  var body = document.getElementById('modalBody');
  body.innerHTML =
    '<h2 class="modal-title">' + esc(job.title) + '</h2>' +
    '<div class="modal-company">' + esc(job.company) + '</div>' +
    '<div class="modal-salary">' + esc(job.salary) + '</div>' +
    '<div class="modal-section"><h4>基本要求</h4><div class="info-row">' +
      '<div class="info-item"><strong>语言：</strong>' + esc(job.language) + '</div>' +
      '<div class="info-item"><strong>年龄：</strong>' + esc(job.age) + '</div>' +
      '<div class="info-item"><strong>工时：</strong>' + esc(job.workTime) + '</div>' +
      '<div class="info-item"><strong>食宿：</strong>' + esc(job.accommodation) + '</div>' +
      (job.agent ? '<div class="info-item"><strong>中介：</strong>' + esc(job.agent) + '</div>' : '') +
    '</div></div>' +
    '<div class="modal-section"><h4>工作内容及要求</h4><div class="full-text">' + esc(job.requirement) + '</div></div>' +
    (job.remark ? '<div class="modal-section"><h4>备注</h4><div class="highlight-box">' + esc(job.remark) + '</div></div>' : '') +
    '<div class="modal-section"><div class="info-item" style="display:inline-block"><strong>分类：</strong>' + esc(job.category) + '</div></div>';
  document.getElementById('modalOverlay').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modalOverlay')) return;
  document.getElementById('modalOverlay').style.display = 'none';
  document.body.style.overflow = '';
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { document.getElementById('modalOverlay').style.display = 'none'; document.body.style.overflow = ''; }
});

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('menuMask').classList.toggle('show');
}

renderCategories();
renderCards();
</script>
</body>
</html>
'''


def generate_html(jobs, output_path):
    """根据岗位数据生成 HTML 文件"""
    jobs_json = json.dumps(jobs, ensure_ascii=False, indent=2)
    cats_json = json.dumps(CATEGORY_ORDER, ensure_ascii=False)

    html = HTML_TEMPLATE.replace('__JOBS_DATA__', jobs_json)
    html = html.replace('__CATEGORY_ORDER__', cats_json)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return len(jobs)


# ═══════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if not os.path.exists(TXT_FILE):
        print(f"[ERROR] 找不到 {TXT_FILE}，请确保脚本与 txt 文件在同一目录")
        sys.exit(1)

    print(f"Parsing {TXT_FILE} ...")
    jobs = parse_txt(TXT_FILE)

    if not jobs:
        print("[ERROR] 没有解析到任何岗位信息，请检查 txt 文件格式")
        sys.exit(1)

    # 统计
    cats = {}
    for j in jobs:
        cats[j['category']] = cats.get(j['category'], 0) + 1

    print(f"Parsed {len(jobs)} jobs:")
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")

    count = generate_html(jobs, HTML_FILE)
    print(f"\nGenerated {HTML_FILE} ({count} jobs)")
    print("Open it in a browser to view.")


if __name__ == '__main__':
    main()
