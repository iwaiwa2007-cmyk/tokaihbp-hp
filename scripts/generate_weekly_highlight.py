#!/usr/bin/env python3
"""
Generate a weekly pancreatobiliary research highlight page.

Usage:
  python3 scripts/generate_weekly_highlight.py
  python3 scripts/generate_weekly_highlight.py --date 2026-07-19

This script:
  - searches PubMed for the last 7 days
  - searches ClinicalTrials.gov for newly posted relevant trials
  - creates weekly-highlights/weekly-highlight-YYYY-MM-DD.html
  - updates the top page What's New
  - updates sitemap.xml

After reviewing the generated page, use GitHub Desktop to commit and push.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DIR = ROOT / "weekly-highlights"
INDEX_PATH = ROOT / "index.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
BASE_URL = "https://iwaiwa2007-cmyk.github.io/TOKAIHBP-HP/"

PUBMED_TERMS = [
    "ERCP",
    "endoscopic retrograde cholangiopancreatography",
    "EUS",
    "endoscopic ultrasound",
    "EUS-guided",
    "acute pancreatitis",
    "chronic pancreatitis",
    "autoimmune pancreatitis",
    "IgG4-related disease",
    "primary sclerosing cholangitis",
    "liver transplantation",
]

TRIAL_TERMS = [
    "ERCP",
    "endoscopic retrograde cholangiopancreatography",
    "EUS",
    "endoscopic ultrasound",
    "EUS-guided",
    "acute pancreatitis",
    "chronic pancreatitis",
    "autoimmune pancreatitis",
    "post-ERCP pancreatitis",
]

JOURNAL_Q = {
    "BMJ Open": "Q1",
    "BMC Gastroenterology": "Q2",
    "Surgical Endoscopy": "Q1",
    "Digestive Diseases and Sciences": "Q2",
    "Medicine": "Q2-Q3",
    "Journal of Controlled Release": "Q1",
    "World Journal of Surgery": "Q1",
    "American Journal of Transplantation": "Q1",
    "Journal of Pediatric Gastroenterology and Nutrition": "Q1-Q2",
    "ACG Case Reports Journal": "症例報告誌 / SJR未確認",
    "Case Reports in Gastrointestinal Medicine": "症例報告誌 / SJR未確認",
}


@dataclass
class Paper:
    pmid: str
    title: str
    journal: str
    pub_date: str
    abstract: str
    category: str
    topic: str
    score: int


@dataclass
class Trial:
    nct_id: str
    title: str
    status: str
    phase: str
    sponsor: str
    enrollment: str
    first_posted: str
    last_updated: str
    conditions: str
    interventions: str
    outcomes: str
    url: str


def request_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TokaiHBPWeeklyHighlight/1.0 (research education site)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Report date in YYYY-MM-DD. Default: today.")
    parser.add_argument("--dry-run", action="store_true", help="Create HTML only; do not update index/sitemap.")
    return parser.parse_args()


def report_dates(date_arg: str | None) -> tuple[dt.date, dt.date, dt.date]:
    if date_arg:
        report_date = dt.date.fromisoformat(date_arg)
    else:
        report_date = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    start_date = report_date - dt.timedelta(days=6)
    return report_date, start_date, report_date


def pubmed_search(start: dt.date, end: dt.date) -> list[str]:
    query = "(" + " OR ".join(f'"{term}"' for term in PUBMED_TERMS) + ")"
    query += f' AND ("{start:%Y/%m/%d}"[Date - Publication] : "{end:%Y/%m/%d}"[Date - Publication])'
    params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "term": query,
            "retmax": "80",
            "retmode": "json",
            "sort": "pub+date",
        }
    )
    data = json.loads(request_text(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"))
    return data.get("esearchresult", {}).get("idlist", [])


def pubmed_fetch(pmids: list[str]) -> list[Paper]:
    if not pmids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    xml_text = request_text(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}")
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = text_or_empty(article.find(".//PMID"))
        title = clean_text("".join(article.findtext(".//ArticleTitle", default="")))
        journal = clean_text(article.findtext(".//Journal/Title", default=""))
        pub_date = extract_pub_date(article)
        abstract = clean_text(" ".join(node.text or "" for node in article.findall(".//AbstractText")))
        category, topic, score = classify_paper(title, abstract, journal)
        if score <= 0:
            continue
        papers.append(Paper(pmid, title, journal, pub_date, abstract, category, topic, score))
    papers.sort(key=lambda p: (p.score, p.pub_date), reverse=True)
    return papers


def text_or_empty(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text.strip()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_pub_date(article: ET.Element) -> str:
    pub_date = article.find(".//JournalIssue/PubDate")
    if pub_date is None:
        return ""
    year = text_or_empty(pub_date.find("Year"))
    month = text_or_empty(pub_date.find("Month"))
    day = text_or_empty(pub_date.find("Day"))
    return " ".join(part for part in [year, month, day] if part)


def classify_paper(title: str, abstract: str, journal: str) -> tuple[str, str, int]:
    text = f"{title} {abstract}".lower()
    score = 0
    category = "immune-transplant"
    topic = "topic-aip"
    if any(k in text for k in ["ercp", "endoscopic retrograde", "papillary", "choledocholithiasis", "biliary obstruction"]):
        category, topic, score = "endoscopy", "topic-ercp", score + 8
    if any(k in text for k in ["eus", "endoscopic ultrasound", "lumen-apposing", "axios"]):
        category, topic, score = "endoscopy", "topic-eus", score + 9
    if any(k in text for k in ["acute pancreatitis", "chronic pancreatitis", "idiopathic pancreatitis", "post-ercp pancreatitis"]):
        category, topic, score = "pancreatitis", "topic-pancreas", score + 8
    if any(k in text for k in ["randomized", "trial", "meta-analysis", "systematic review", "multicentre", "multicenter"]):
        score += 3
    if any(k in text for k in ["guideline", "review", "update"]):
        score += 2
    if "large language model" in text or "artificial intelligence" in text or "machine learning" in text:
        category, topic, score = "pancreatitis", "topic-ai", score + 4
    if "primary sclerosing cholangitis" in text or re.search(r"\bpsc\b", text):
        category, topic, score = "immune-transplant", "topic-psc", score + 7
    if "autoimmune pancreatitis" in text or "igg4" in text:
        category, topic, score = "immune-transplant", "topic-aip", score + 7
    if "liver transplant" in text or "liver transplantation" in text:
        category, topic, score = "immune-transplant", "topic-transplant", score + 7
    if "case report" in text or "case reports" in journal.lower():
        score -= 2
    return category, topic, score


def previous_pmids() -> set[str]:
    pmids: set[str] = set()
    for path in WEEKLY_DIR.glob("weekly-highlight-*.html"):
        pmids.update(re.findall(r"PMID:\s*(\d+)", path.read_text(encoding="utf-8", errors="ignore")))
        pmids.update(re.findall(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/", path.read_text(encoding="utf-8", errors="ignore")))
    return pmids


def select_papers(papers: list[Paper]) -> dict[str, list[Paper]]:
    seen = previous_pmids()
    grouped = {"endoscopy": [], "pancreatitis": [], "immune-transplant": []}
    # Do not exclude the file being generated if rerunning today; duplicate protection is mostly for prior weeks.
    for paper in papers:
        if paper.pmid in seen and len(grouped.get(paper.category, [])) >= 2:
            continue
        if paper.category in grouped and len(grouped[paper.category]) < 5:
            grouped[paper.category].append(paper)
    return grouped


def trials_search(start: dt.date, end: dt.date) -> list[Trial]:
    trials: dict[str, Trial] = {}
    for term in TRIAL_TERMS:
        params = urllib.parse.urlencode(
            {
                "query.term": term,
                "pageSize": "50",
                "format": "json",
            }
        )
        try:
            data = json.loads(request_text(f"https://clinicaltrials.gov/api/v2/studies?{params}"))
        except Exception:
            continue
        for study in data.get("studies", []):
            protocol = study.get("protocolSection", {})
            ident = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            nct_id = ident.get("nctId", "")
            first_posted = get_date(status.get("studyFirstPostDateStruct", {}))
            if not nct_id or not date_in_range(first_posted, start, end):
                continue
            title = ident.get("briefTitle", "")
            if not is_relevant_trial(title, protocol):
                continue
            design = protocol.get("designModule", {})
            sponsor = protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")
            enrollment = design.get("enrollmentInfo", {})
            arms = protocol.get("armsInterventionsModule", {}).get("interventions", [])
            outcomes = protocol.get("outcomesModule", {}).get("primaryOutcomes", [])
            trials[nct_id] = Trial(
                nct_id=nct_id,
                title=title,
                status=status.get("overallStatus", ""),
                phase=", ".join(design.get("phases", [])) or "NA",
                sponsor=sponsor,
                enrollment=str(enrollment.get("count", "")),
                first_posted=first_posted,
                last_updated=get_date(status.get("lastUpdatePostDateStruct", {})),
                conditions=", ".join(protocol.get("conditionsModule", {}).get("conditions", [])),
                interventions=", ".join(i.get("name", "") for i in arms if i.get("name")) or "記載なし",
                outcomes=", ".join(o.get("measure", "") for o in outcomes if o.get("measure")) or "記載なし",
                url=f"https://clinicaltrials.gov/study/{nct_id}",
            )
    return list(trials.values())[:5]


def get_date(date_struct: dict) -> str:
    return date_struct.get("date", "") if isinstance(date_struct, dict) else ""


def date_in_range(date_text: str, start: dt.date, end: dt.date) -> bool:
    if not date_text:
        return False
    try:
        value = dt.date.fromisoformat(date_text[:10])
    except ValueError:
        return False
    return start <= value <= end


def is_relevant_trial(title: str, protocol: dict) -> bool:
    text = json.dumps(protocol, ensure_ascii=False).lower() + " " + title.lower()
    must = [
        "ercp",
        "endoscopic ultrasound",
        "eus",
        "acute pancreatitis",
        "chronic pancreatitis",
        "autoimmune pancreatitis",
        "post-ercp pancreatitis",
    ]
    return any(term in text for term in must)


def template_style() -> str:
    latest = latest_weekly_file()
    if latest:
        text = latest.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"<style>(.*?)</style>", text, flags=re.S)
        if match:
            return match.group(1)
    raise RuntimeError("No weekly highlight template found. Keep at least one weekly-highlight HTML file.")


def latest_weekly_file() -> Path | None:
    files = sorted(WEEKLY_DIR.glob("weekly-highlight-*.html"))
    return files[-1] if files else None


def short_ja_title(paper: Paper) -> str:
    title = paper.title.lower()
    if "post-ercp pancreatitis" in title:
        return "ERCP後膵炎に関する研究"
    if "choledocholithiasis" in title:
        return "総胆管結石診療に関する研究"
    if "acute pancreatitis" in title:
        return "急性膵炎に関する研究"
    if "autoimmune pancreatitis" in title:
        return "自己免疫性膵炎に関する研究"
    if "primary sclerosing cholangitis" in title:
        return "PSCに関する研究"
    if "liver transplant" in title:
        return "肝移植に関する研究"
    if "eus" in title or "endoscopic ultrasound" in title:
        return "EUSに関する研究"
    if "ercp" in title:
        return "ERCPに関する研究"
    return "胆膵領域の新着研究"


def topic_logo(topic: str) -> str:
    labels = {
        "topic-ercp": ("ERCP", '<path d="M6 4v7c0 3 2 5 5 5h1c3 0 5-2 5-5V4"/><path d="M9 4v7c0 1.2.8 2 2 2h1c1.2 0 2-.8 2-2V4"/><path d="M12 16v4"/>'),
        "topic-eus": ("EUS", '<circle cx="10" cy="10" r="5"/><path d="M14 14l5 5"/><path d="M4 14c2-2 4-2 6 0s4 2 6 0"/>'),
        "topic-pancreas": ("膵炎", '<path d="M4 13c2-5 7-6 10-4 2 1 4 1 6 0"/><path d="M5 15c3 2 7 2 10 0 2-1 4-1 5 1"/><path d="M8 10c-1 3 0 6 3 8"/>'),
        "topic-ai": ("AI", '<rect x="6" y="6" width="12" height="12" rx="3"/><path d="M9 10h.01"/><path d="M15 10h.01"/><path d="M9 14c2 1 4 1 6 0"/><path d="M12 2v4"/><path d="M12 18v4"/>'),
        "topic-transplant": ("移植", '<path d="M7 20c0-6 3-10 8-12"/><path d="M11 18c5 0 8-4 8-10V5h-3c-6 0-10 4-10 10"/><path d="M9 13c2 .5 4 .5 6 0"/>'),
        "topic-psc": ("PSC", '<path d="M7 4v16"/><path d="M17 4v16"/><path d="M7 8c4 0 6 2 10 2"/><path d="M7 14c4 0 6-2 10-2"/><path d="M7 18c4 0 6-2 10-2"/>'),
        "topic-aip": ("AIP", '<path d="M12 3l7 4v5c0 4-3 7-7 9-4-2-7-5-7-9V7l7-4z"/><path d="M9 12l2 2 4-5"/>'),
    }
    label, svg = labels.get(topic, labels["topic-aip"])
    return f'<span class="topic-logo {topic}" aria-label="{html.escape(label)}領域"><svg viewBox="0 0 24 24" aria-hidden="true">{svg}</svg><small>{html.escape(label)}</small></span>'


def paper_summary(paper: Paper) -> str:
    if paper.abstract:
        text = paper.abstract
        text = re.split(r"(?<=[。.!?])\s+", text)[0]
        if len(text) > 180:
            text = text[:177] + "..."
        return f"PubMed抄録からの要約候補です。{html.escape(text)}"
    return "抄録が取得できないため、タイトルと掲載誌情報をもとに確認してください。"


def journal_badges(paper: Paper) -> str:
    q = JOURNAL_Q.get(paper.journal, "SJR確認要")
    badge_class = "high" if "Q1" in q else "clinical" if "Q2" in q else ""
    return f'<span class="badge {badge_class}">{html.escape(paper.journal or "Journal未取得")} / {html.escape(q)}</span>'


def render_papers(papers: list[Paper]) -> str:
    if not papers:
        return '<p class="note">該当する重要論文候補はありませんでした。</p>'
    chunks = []
    for paper in papers:
        title = f"{paper.title}；{short_ja_title(paper)}"
        chunks.append(
            f"""
      <article class="paper">
        <div class="paper-heading">
          <p class="paper-title"><a href="https://pubmed.ncbi.nlm.nih.gov/{html.escape(paper.pmid)}/" target="_blank" rel="noopener">{html.escape(title)}</a></p>
          {topic_logo(paper.topic)}
        </div>
        <div class="badges">
          {journal_badges(paper)}
          <span class="badge">PMID: {html.escape(paper.pmid)}</span>
          <span class="badge">PubDate: {html.escape(paper.pub_date or "未取得")}</span>
        </div>
        <p>{paper_summary(paper)}</p>
      </article>
            """.rstrip()
        )
    return "\n".join(chunks)


def render_trials(trials: list[Trial], start: dt.date, end: dt.date) -> str:
    if not trials:
        return f"""
      <p class="note">ClinicalTrials.govでは対象期間内に直接関連する新規登録試験は抽出されませんでした。</p>
      <h3>検索条件</h3>
      <p>対象期間: {start:%Y年%-m月%-d日}〜{end:%Y年%-m月%-d日}。検索語: {html.escape(", ".join(TRIAL_TERMS))}。</p>
        """.rstrip()
    rows = []
    for trial in trials:
        rows.append(
            f"""
      <h3>注目試験: <a href="{html.escape(trial.url)}" target="_blank" rel="noopener">{html.escape(trial.nct_id)}</a></h3>
      <table class="trial-table">
        <tbody>
          <tr><th>試験名</th><td><a href="{html.escape(trial.url)}" target="_blank" rel="noopener">{html.escape(trial.title)}</a></td></tr>
          <tr><th>対象疾患・テーマ</th><td>{html.escape(trial.conditions)}</td></tr>
          <tr><th>介入・検査内容</th><td>{html.escape(trial.interventions)}</td></tr>
          <tr><th>ステータス・フェーズ</th><td>{html.escape(trial.status)} / Phase: {html.escape(trial.phase)}</td></tr>
          <tr><th>登録日・最終更新日</th><td>First posted: {html.escape(trial.first_posted)} / Last updated: {html.escape(trial.last_updated)}</td></tr>
          <tr><th>スポンサー</th><td>{html.escape(trial.sponsor)}</td></tr>
          <tr><th>予定/実登録数</th><td>{html.escape(trial.enrollment)}</td></tr>
          <tr><th>主要評価項目</th><td>{html.escape(trial.outcomes)}</td></tr>
          <tr><th>臨床的に重要そうな点</th><td>胆膵領域の診療、手技、教育、または膵炎診療に直接関連する新規登録試験として確認が必要です。</td></tr>
        </tbody>
      </table>
            """.rstrip()
        )
    return (
        f'<p class="note">ClinicalTrials.govでは対象期間内に関連する新規登録試験が{len(trials)}件抽出されました。</p>\n'
        f"<h3>検索条件</h3>\n<p>対象期間: {start:%Y年%-m月%-d日}〜{end:%Y年%-m月%-d日}。検索語: {html.escape(', '.join(TRIAL_TERMS))}。</p>\n"
        + "\n".join(rows)
    )


def render_html(report_date: dt.date, start: dt.date, end: dt.date, papers_by_category: dict[str, list[Paper]], trials: list[Trial]) -> str:
    style = template_style()
    filename = f"weekly-highlight-{report_date:%Y-%m-%d}.html"
    title_range = f"{start:%Y年%-m月%-d日}〜{end:%-m月%-d日}"
    canonical = f"{BASE_URL}weekly-highlights/{filename}"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>今週の胆膵疾患研究ハイライト | {html.escape(title_range)}</title>
  <meta name="description" content="PubMedとClinicalTrials.govをもとにした、胆膵内視鏡・ERCP・EUS、膵炎、PSC、IgG4関連疾患、肝移植領域の週次研究ハイライトです。">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../assets/apple-touch-icon.png">
  <link rel="stylesheet" href="../style.css?v=20260710-1">
  <style>{style}</style>
</head>
<body>
  <header class="site-header">
    <a class="brand" href="../index.html#home" aria-label="Home">
      <img class="brand-logo" src="../assets/tokai-gastro-logo.png" alt="Tokai University Gastroenterology">
      <span><span class="brand-ja">東海大学医学部消化器内科胆膵班</span><span class="brand-en">Tokai University School of Medicine, Biliary-Pancreatic Clinical Group</span></span>
    </a>
    <button class="nav-toggle" type="button" aria-label="メニューを開く" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="site-nav" aria-label="Primary navigation">
      <a href="../index.html#home">Home</a>
      <a href="{filename}">Highlights</a>
      <a href="../AIP_Diagnosis/index.html">AIP tool</a>
      <a href="../index.html#members">PI</a>
      <a href="../index.html#research">Research</a>
      <a href="../index.html#education">Education</a>
      <a href="../index.html#publications">Publications</a>
      <a href="../index.html#contact">Contact</a>
    </nav>
  </header>

  <main class="page">
    <section class="highlight-hero">
      <p class="eyebrow">Weekly Pancreatobiliary Research Highlight</p>
      <h1>今週の胆膵疾患研究ハイライト</h1>
      <p>PubMedとClinicalTrials.govを中心に、胆膵内視鏡・ERCP・EUS、急性膵炎・慢性膵炎、肝移植・PSC・IgG4関連疾患の臨床的に重要そうな新着情報を整理した週次レポートです。</p>
      <p>雑誌のQ分類はSCImago等で確認できる範囲の目安です。分野や年度により変動するため、正式な評価には原典をご確認ください。</p>
      <div class="hero-meta">
        <span class="pill">対象期間: {html.escape(title_range)}</span>
        <span class="pill">作成日: {report_date:%Y年%-m月%-d日}</span>
        <span class="pill">自動生成ドラフト</span>
      </div>
    </section>

    <nav class="nav" aria-label="ページ内ナビゲーション">
      <a href="#endoscopy">ERCP・EUS</a>
      <a href="#pancreatitis">膵炎</a>
      <a href="#immune-transplant">PSC・IgG4・移植</a>
      <a href="#trials">臨床試験</a>
    </nav>

    <details id="endoscopy" class="card section-panel" open>
      <summary class="section-summary"><h2>胆膵内視鏡・ERCP・EUS</h2></summary>
{render_papers(papers_by_category.get("endoscopy", []))}
    </details>

    <details id="pancreatitis" class="card section-panel" open>
      <summary class="section-summary"><h2>急性膵炎・慢性膵炎</h2></summary>
{render_papers(papers_by_category.get("pancreatitis", []))}
    </details>

    <details id="immune-transplant" class="card section-panel" open>
      <summary class="section-summary"><h2>肝移植・PSC・IgG4関連疾患</h2></summary>
{render_papers(papers_by_category.get("immune-transplant", []))}
    </details>

    <details id="trials" class="card section-panel" open>
      <summary class="section-summary"><h2>新規登録臨床研究</h2></summary>
{render_trials(trials, start, end)}
    </details>

    <p class="footer">
      このページは医師・医学生・研究者向けの文献整理メモです。患者さんへの医療広告、個別診療相談、治療効果の保証を目的としたものではありません。<br>
      <a href="../index.html">トップページへ戻る</a>
    </p>
  </main>
  <script src="../script.js"></script>
</body>
</html>
"""


def write_weekly_page(report_date: dt.date, content: str) -> Path:
    WEEKLY_DIR.mkdir(exist_ok=True)
    path = WEEKLY_DIR / f"weekly-highlight-{report_date:%Y-%m-%d}.html"
    path.write_text(content, encoding="utf-8")
    return path


def update_index(report_date: dt.date, start: dt.date, end: dt.date, page_path: Path) -> None:
    text = INDEX_PATH.read_text(encoding="utf-8")
    href = f"weekly-highlights/{page_path.name}"
    if href in text:
        return
    text = text.replace('<details class="news-item" open>', '<details class="news-item">', 1)
    item = f"""
          <details class="news-item" open>
            <summary>
              <time datetime="{report_date:%Y-%m-%d}">{report_date:%Y.%-m.%-d}</time>
              <span>今週の胆膵疾患研究ハイライトを公開しました</span>
            </summary>
            <div class="news-body">
              <p><a href="{href}">今週の胆膵疾患研究ハイライト（{start:%Y年%-m月%-d日}〜{end:%-m月%-d日}）</a> を作成しました。PubMedとClinicalTrials.govをもとに、胆膵内視鏡、ERCP・EUS、膵炎、PSC、IgG4関連疾患、肝移植領域の新着情報を整理しています。</p>
            </div>
          </details>
"""
    marker = '<div class="news-list" aria-label="お知らせ一覧">\n'
    if marker not in text:
        raise RuntimeError("Could not find news-list in index.html")
    text = text.replace(marker, marker + item, 1)
    INDEX_PATH.write_text(text, encoding="utf-8")


def update_sitemap(report_date: dt.date, page_path: Path) -> None:
    text = SITEMAP_PATH.read_text(encoding="utf-8")
    loc = f"{BASE_URL}weekly-highlights/{page_path.name}"
    if loc in text:
        return
    url = f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{report_date:%Y-%m-%d}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
"""
    text = text.replace("</urlset>", url + "</urlset>")
    SITEMAP_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    report_date, start, end = report_dates(args.date)
    print(f"Generating weekly highlight: {start} to {end}")
    pmids = pubmed_search(start, end)
    print(f"PubMed candidates: {len(pmids)}")
    papers = pubmed_fetch(pmids)
    grouped = select_papers(papers)
    print("Selected papers:", {key: len(value) for key, value in grouped.items()})
    trials = trials_search(start, end)
    print(f"ClinicalTrials.gov candidates: {len(trials)}")
    content = render_html(report_date, start, end, grouped, trials)
    page_path = write_weekly_page(report_date, content)
    if not args.dry_run:
        update_index(report_date, start, end, page_path)
        update_sitemap(report_date, page_path)
    print(f"Created: {page_path.relative_to(ROOT)}")
    print("Review the generated page, then commit and push with GitHub Desktop.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
