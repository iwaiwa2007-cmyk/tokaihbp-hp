# Weekly highlight generation

毎週日曜日に「今週の胆膵疾患研究ハイライト」を作るための補助スクリプトです。

## 実行

```bash
python3 scripts/generate_weekly_highlight.py
```

日付を指定して試す場合:

```bash
python3 scripts/generate_weekly_highlight.py --date 2026-07-19
```

## 作成・更新されるもの

- `weekly-highlights/weekly-highlight-YYYY-MM-DD.html`
- `index.html` の What&apos;s New
- `sitemap.xml`

## 運用

1. 日曜日にCodexでこのスクリプトを実行します。
2. 作成されたHTMLを軽く確認します。
3. GitHub Desktopで変更をcommit/pushします。

PubMedとClinicalTrials.govを自動取得します。
