import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Users/iwasakieiten/Library/Mobile Documents/com~apple~CloudDocs/codex/HP作りたい！";
const buildDir = path.join(workspaceDir, ".codex-build/pancreatitis-slides");
const previewDir = path.join(buildDir, "previews");
const outputDir = path.join(workspaceDir, "output/presentations");
const finalPath = path.join(outputDir, "pancreatitis-research-highlights-2026-11.pptx");
const skillDir = "/Users/iwasakieiten/.codex/plugins/cache/openai-primary-runtime/presentations/26.1104.22356/skills/presentations";
const runtimePython = "/Users/iwasakieiten/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";

const C = {
  navy: "#123A62",
  blue: "#4D8EAF",
  pale: "#EAF5FA",
  pale2: "#F5FAFC",
  red: "#C84D4D",
  orange: "#D87942",
  teal: "#417F79",
  green: "#667C53",
  gray: "#5E6872",
  lightGray: "#D8E2E8",
  black: "#1B2630",
  white: "#FFFFFF",
};
const FONT = "Hiragino Sans";

const assets = {
  logo: path.join(workspaceDir, "assets/tokai-gastro-logo.png"),
  plozasiran: path.join(workspaceDir, "weekly-highlights/images/2026-11-08/plozasiran-hypertriglyceridemia-pancreatitis.jpg"),
  fluids: path.join(workspaceDir, "weekly-highlights/images/2026-08-30/acute-pancreatitis-fluid-network-meta-analysis.jpg"),
  necrosectomy: path.join(workspaceDir, "weekly-highlights/images/2026-10-18/immediate-vs-on-demand-necrosectomy.jpg"),
  glp1: path.join(workspaceDir, "weekly-highlights/images/2026-10-18/glp1-recurrent-acute-pancreatitis.jpg"),
  pediatric: path.join(workspaceDir, "weekly-highlights/images/2026-11-01/pediatric-gallstone-pancreatitis-cholecystectomy.jpg"),
  pancreas: path.join(workspaceDir, "assets/hero-pancreas.jpeg"),
};

async function bytes(file) {
  const b = await fs.readFile(file);
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontFamily: FONT,
    fontSize: style.fontSize ?? 22,
    bold: style.bold ?? false,
    color: style.color ?? C.black,
  };
  if (style.align) {
    shape.text.paragraphFormat = { alignment: style.align };
  }
  return shape;
}

function addRule(slide, left, top, width, height, fill) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill, width: 0 },
  });
}

function addPanel(slide, position, fill = C.white, line = C.lightGray, width = 1) {
  return slide.shapes.add({
    geometry: "rect",
    position,
    fill,
    line: { style: "solid", fill: line, width },
  });
}

async function addImage(slide, file, position, alt, fit = "contain") {
  const ext = path.extname(file).toLowerCase();
  const contentType = ext === ".png" ? "image/png" : "image/jpeg";
  return slide.images.add({
    blob: await bytes(file),
    contentType,
    alt,
    fit,
    position,
    geometry: "rect",
  });
}

async function addChrome(slide, title, slideNo) {
  slide.background.fill = C.white;
  addRule(slide, 0, 0, 1280, 58, C.pale);
  addRule(slide, 0, 57, 1280, 2, C.blue);
  addText(slide, title, { left: 48, top: 9, width: 1080, height: 40 }, {
    fontSize: 30,
    bold: false,
    color: C.black,
  });
  await addImage(slide, assets.logo, { left: 1198, top: 7, width: 42, height: 42 }, "Tokai University Pancreato Biliary logo", "contain");
  addRule(slide, 42, 682, 1196, 2, C.pale);
  addText(slide, "Department of Internal Medicine, Tokai University School of Medicine", {
    left: 48, top: 687, width: 760, height: 18,
  }, { fontSize: 11, color: C.gray });
  addText(slide, String(slideNo), { left: 1170, top: 687, width: 55, height: 18 }, {
    fontSize: 11, color: C.gray, align: "right",
  });
}

function addDesignLine(slide, text) {
  addText(slide, text, { left: 50, top: 78, width: 730, height: 28 }, {
    fontSize: 17, color: C.gray,
  });
}

function addBigMetric(slide, primary, secondary, accent = C.navy) {
  addText(slide, primary, { left: 50, top: 118, width: 720, height: 68 }, {
    fontSize: 44, bold: true, color: accent,
  });
  if (secondary) {
    addText(slide, secondary, { left: 52, top: 188, width: 700, height: 44 }, {
      fontSize: 26, bold: true, color: C.red,
    });
  }
}

function addBody(slide, lines, top = 250) {
  addText(slide, lines.join("\n"), { left: 55, top, width: 715, height: 210 }, {
    fontSize: 22, color: C.black,
  });
}

function addTakeHome(slide, text, caveat) {
  addPanel(slide, { left: 48, top: 548, width: 1168, height: 82 }, C.white, C.red, 2);
  addText(slide, text, { left: 68, top: 560, width: 1128, height: 34 }, {
    fontSize: 24, bold: true, color: C.red,
  });
  addText(slide, caveat, { left: 70, top: 596, width: 1125, height: 24 }, {
    fontSize: 15, color: C.gray,
  });
}

async function addSquareVisual(slide, file, alt) {
  addPanel(slide, { left: 820, top: 92, width: 396, height: 396 }, C.pale2, C.lightGray, 1);
  await addImage(slide, file, { left: 832, top: 104, width: 372, height: 372 }, alt, "contain");
}

function addCitation(slide, text) {
  addText(slide, text, { left: 52, top: 644, width: 1160, height: 27 }, {
    fontSize: 11, color: C.gray,
  });
}

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

// 1. Plozasiran
{
  const slide = presentation.slides.add();
  await addChrome(slide, "重症高TG血症　plozasiranで膵炎を予防", 1);
  addDesignLine(slide, "SHASTA-3 / SHASTA-4　Double-blind Phase III RCT　757例");
  addBigMetric(slide, "急性膵炎  1 vs 5 / 100人年", "rate ratio 0.22　P=0.008", C.navy);
  addBody(slide, [
    "・12か月のTG中央値　79-81%低下",
    "・TG <500 mg/dL達成　91-93% vs 50-51%",
    "・有害事象　73% vs 73%",
  ], 250);
  await addSquareVisual(slide, assets.plozasiran, "APOC3標的siRNAによる高TG血症と膵炎予防の比較");
  addTakeHome(slide, "TG低下だけでなく、膵炎イベント抑制を示した", "膵炎は統合副次解析。企業資金試験であり、長期・実臨床データが必要");
  addCitation(slide, "Plozasiran for Severe Hypertriglyceridemia and Risk of Pancreatitis. N Engl J Med. PMID: 42981569");
  slide.speakerNotes.text = [
    "話し方:",
    "高TG血症治療が、数値改善から膵炎予防へ進んだ点を強調する。",
    "膵炎は主要評価項目ではなく、2試験の統合副次解析である。",
    "Source: https://pubmed.ncbi.nlm.nih.gov/42981569/",
  ].join("\n");
}

// 2. Fluid resuscitation
{
  const slide = presentation.slides.add();
  await addChrome(slide, "急性膵炎の初期輸液　LRを用いた中等量・目標指向型", 2);
  addDesignLine(slide, "Component network meta-analysis　12 RCT　1,216例");
  addBigMetric(slide, "LR vs 生食  iOR 0.51", "積極的輸液の有害事象  iOR 3.35", C.teal);
  addBody(slide, [
    "・中等症・重症化　iOR 0.51（95%CI 0.33-0.79）",
    "・局所合併症　iOR 0.53（95%CI 0.33-0.85）",
    "・循環動態、心腎機能をみながら調整",
  ], 250);
  await addSquareVisual(slide, assets.fluids, "適量の乳酸リンゲル液と過剰輸液を比較する医学イラスト");
  addTakeHome(slide, "大量輸液を避け、LRを用いた中等量・目標指向型へ", "エビデンスの確実性は低-中等度。重症例では個別化が必要");
  addCitation(slide, "Non-aggressive Lactated Ringer's resuscitation in acute pancreatitis. Pancreatology. PMID: 42648911");
  slide.speakerNotes.text = [
    "話し方:",
    "WATERFALL以降の流れとして、輸液量と液種を一枚で示す。",
    "LRは生食より良好な可能性がある一方、過剰輸液は明確に避けたい。",
    "Source: https://pubmed.ncbi.nlm.nih.gov/42648911/",
  ].join("\n");
}

// 3. Necrosectomy
{
  const slide = presentation.slides.add();
  await addChrome(slide, "感染性壊死性膵炎　ネクロセクトミーはオンデマンド", 3);
  addDesignLine(slide, "Immediate vs on-demand endoscopic necrosectomy　4 RCT　215例");
  addBigMetric(slide, "臨床成功・死亡に明確な差なし", "ネクロセクトミー実施率  RR 1.65", C.navy);
  addBody(slide, [
    "・即時群　EUSドレナージ後72時間以内に実施",
    "・入院期間、費用、追加ドレナージ、有害事象も差なし",
    "・必要時介入を基本とするstep-up strategyを支持",
  ], 250);
  await addSquareVisual(slide, assets.necrosectomy, "即時ネクロセクトミーとオンデマンド戦略の比較");
  addTakeHome(slide, "即時介入は処置数を増やすが、転帰改善は示さない", "大半のアウトカムはlow to very low certainty");
  addCitation(slide, "Immediate versus on-demand endoscopic necrosectomy. Surg Endosc. PMID: 42881308");
  slide.speakerNotes.text = [
    "話し方:",
    "できるからすぐ行う、ではなく、ドレナージ後の反応を見て追加介入する。",
    "処置回数を増やしても、臨床成功や死亡は改善しなかった。",
    "Source: https://pubmed.ncbi.nlm.nih.gov/42881308/",
  ].join("\n");
}

// 4. GLP-1RA
{
  const slide = presentation.slides.add();
  await addChrome(slide, "膵炎既往例とGLP-1受容体作動薬", 4);
  addDesignLine(slide, "Systematic review　4 studies　10,624例");
  addBigMetric(slide, "急性膵炎再発の増加は示されず", "vs SGLT2阻害薬  OR 0.57（0.52-0.64）", C.green);
  addBody(slide, [
    "・placebo比較　OR 0.26（95%CI 0.05-1.32）",
    "・比較データは2研究のみ",
    "・適応交絡と選択バイアスを除外できない",
  ], 250);
  await addSquareVisual(slide, assets.glp1, "膵炎既往例でGLP-1受容体作動薬と再発リスクを検討するイラスト");
  addTakeHome(slide, "膵炎既往だけで一律に避ける根拠は弱い", "無条件に安全とする段階ではない。個別リスクと適応を確認");
  addCitation(slide, "Risk of recurrent acute pancreatitis with GLP-1 receptor agonists. Acta Diabetol. PMID: 42873314");
  slide.speakerNotes.text = [
    "話し方:",
    "臨床で質問されやすいテーマとして提示する。",
    "現時点では再発増加のシグナルは乏しいが、因果的な安全性は確定していない。",
    "Source: https://pubmed.ncbi.nlm.nih.gov/42873314/",
  ].join("\n");
}

// 5. Pediatric gallstone pancreatitis
{
  const slide = presentation.slides.add();
  await addChrome(slide, "小児胆石性膵炎　同一入院中胆嚢摘出", 5);
  addDesignLine(slide, "US National Readmission Database 2016-2020　13,517例");
  addBigMetric(slide, "60日再入院  4.4% vs 24.8%", "adjusted HR 0.16", C.orange);
  addBody(slide, [
    "・胆嚢摘出なし + ERCP　再入院14.85%",
    "・胆嚢摘出 + ERCP　再入院3.7%",
    "・小児でも早期の根治治療を支持",
  ], 250);
  await addSquareVisual(slide, assets.pediatric, "小児胆石性膵炎の同一入院中胆嚢摘出と再入院予防");
  addTakeHome(slide, "同一入院中胆嚢摘出で再入院が大幅に少ない", "請求データによる観察研究。重症度、施設方針、適応交絡に注意");
  addCitation(slide, "Index-admission cholecystectomy in pediatric gallstone pancreatitis. Surg Endosc. PMID: 42963408");
  slide.speakerNotes.text = [
    "話し方:",
    "成人の胆石性膵炎で確立した考え方が、小児データでも支持された。",
    "絶対差が大きい一方、観察研究である点を残す。",
    "Source: https://pubmed.ncbi.nlm.nih.gov/42963408/",
  ].join("\n");
}

// 6. Visceral adiposity and severe PEP
{
  const slide = presentation.slides.add();
  await addChrome(slide, "内臓脂肪は重症PEPのリスク指標", 6);
  addDesignLine(slide, "日本2施設　胆道ERCP 3,087例　PEP 85例（2.75%）");
  addBigMetric(slide, "中等症-重症PEP  OR 2.79", "発症予測ではなく、重症化予測", C.navy);
  addBody(slide, [
    "・内臓脂肪量は中等症-重症群で高値",
    "・多変量解析で独立した関連",
    "・術前CTを用いた身体組成評価の可能性",
  ], 250);
  addPanel(slide, { left: 790, top: 98, width: 426, height: 346 }, C.pale2, C.lightGray, 1);
  await addImage(slide, assets.pancreas, { left: 802, top: 110, width: 402, height: 322 }, "膵臓と医学研究を示すイラスト", "contain");
  addText(slide, "Visceral adiposity", { left: 840, top: 460, width: 340, height: 38 }, {
    fontSize: 27, bold: true, color: C.teal, align: "center",
  });
  addTakeHome(slide, "術前CTをPEP重症化リスク層別化に使える可能性", "後ろ向きcohort。PEP 85例であり、外部検証が必要");
  addCitation(slide, "Visceral Adipose Tissue as a Predictor of Severe Post-ERCP Pancreatitis. JHBPS. PMID: 42494284");
  slide.speakerNotes.text = [
    "話し方:",
    "PEPの発症因子ではなく、重症化因子として身体組成を見る点が新しい。",
    "既存CTから取得できるため、将来的な自動リスク評価につながる可能性がある。",
    "Source: https://pubmed.ncbi.nlm.nih.gov/42494284/",
  ].join("\n");
}

await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, `slide-${index + 1}.png`), new Uint8Array(await png.arrayBuffer()));
}
const montage = await presentation.export({ format: "webp", montage: true });
await fs.writeFile(path.join(previewDir, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const candidatePath = path.join(buildDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(pathToFileURL(
  path.join(skillDir, "container_tools/artifact_tool_utils.mjs"),
).href);

const requirements = {
  explicitTotalSlideCount: 6,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  requiredEmbeddedWorkbookChartOwnerSlides: [],
};
const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  requiredNativeTableOwnerSlides: [],
  fontPolicy: { basis: "design", families: ["Aptos"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "pancreatitis-research-highlights-2026-11.validation.json"),
});

console.log(JSON.stringify({
  slideCount: presentation.slides.items.length,
  previewDir,
  finalPath,
  validation: result,
}, null, 2));
