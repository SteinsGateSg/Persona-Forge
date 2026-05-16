const translations = {
  en: {
    title: "Persona-Forge",
    description:
      "Persona-Forge is a reusable character voice training framework built around GPT-SoVITS, reference-bank tooling, and repo-friendly release workflows.",
    "landing.kicker": "A Framework for Character Voices",
    "landing.quote":
      "Between constellations and code, a voice system begins to take shape.",
    "landing.subquote":
      "A local-first framework for shaping character voice systems around GPT-SoVITS, reference banks, and local synthesis.",
    "landing.button": "Enter Framework",
    "hero.eyebrow": "Character Voice Toolkit",
    "hero.lede":
      "A reusable framework for building anime and character voice systems: manifest generation, GPT-SoVITS training wrappers, reference-bank labeling, and local synthesis.",
    "hero.repoButton": "GitHub Repository",
    "hero.exampleButton": "Example Character Repo",
    "hero.kicker": "Current Alignment",
    "hero.status1.label": "Mode",
    "hero.status1.value": "Local-first",
    "hero.status2.label": "Backend",
    "hero.status3.label": "Layout",
    "hero.status3.value": "Two-repo split",
    "hero.status4.label": "Status",
    "hero.status4.value": "Smoke-tested",
    "hero.microcopy":
      "Reusable tooling, held apart from any single character's worldline.",
    "visual.tag": "Attractor Field",
    "visual.title": "A quieter atlas beneath the same stars",
    "visual.body":
      "Constellations, instrument lines, and field notes resting where observation turns into method.",
    "stats.cli": "primary CLI commands",
    "stats.repos": "repository layers",
    "stats.instance": "validated character instance",
    "stats.version": "current framework tag",
    "overview.tag": "Framework Scope",
    "overview.title": "What Persona-Forge owns",
    "overview.body":
      "Persona-Forge keeps only reusable workflow code. Character-specific datasets, curated refs, release weights, and demos should live in separate character repositories.",
    "overview.card1.title": "Manifest Builder",
    "overview.card1.body":
      "Turn transcript CSV plus wav directories into GPT-SoVITS-ready training lists.",
    "overview.card2.title": "Training Wrappers",
    "overview.card2.body":
      "Run prepare, SoVITS training, GPT training, and SoVITS export without hand-editing upstream configs.",
    "overview.card3.title": "Reference Tooling",
    "overview.card3.body":
      "Label emotion candidates, shortlist refs, and shape a stable reference bank.",
    "overview.card4.title": "Repo Hygiene",
    "overview.card4.body":
      "Support a clean split between framework repo, character repo, GitHub, and Hugging Face assets.",
    "workflow.tag": "Constellation",
    "workflow.title": "The path from transcripts to a stable voice map",
    "workflow.body":
      "Manifest construction, feature preparation, staged training, reference curation, and listening checks remain in one framework layer.",
    "workflow.step1.title": "Build manifest",
    "workflow.step1.body":
      "Normalize transcript CSV and wav paths into a single training list.",
    "workflow.step2.title": "Prepare dataset",
    "workflow.step2.body":
      "Extract text, HuBERT, wav32k, and semantic features through upstream GPT-SoVITS scripts.",
    "workflow.step3.title": "Train + export",
    "workflow.step3.body":
      "Tune SoVITS and GPT in stages, export inference-ready weights, and keep resumable checkpoints.",
    "workflow.step4.title": "Curate refs",
    "workflow.step4.body":
      "Label and shortlist reference clips for emotion-aware prompting and demos.",
    "quick.tag": "Quick Start",
    "quick.title": "Minimal local path",
    "quick.body":
      "Install the framework, point it at an existing GPT-SoVITS clone, and start with manifest building or a doctor check before training.",
    "commands.tag": "Commands",
    "commands.title": "Core entrypoints",
    "commands.item1": "Create a training list from transcripts and wav files.",
    "commands.item2": "Run upstream feature extraction and semantic preparation.",
    "commands.item3": "Train or resume the acoustic / timbre side.",
    "commands.item4": "Export a SoVITS checkpoint into an inference weight file.",
    "commands.item5": "Train or resume the text-to-semantic stage.",
    "commands.item6": "Generate audio from a fixed GPT + SoVITS pair.",
    "commands.item7":
      "Label and shortlist reference candidates with an OpenAI-compatible API.",
    "commands.item8": "Check local prerequisites before a real run.",
    "links.docs.tag": "Docs",
    "links.docs.title": "Repository documents",
    "links.arch.tag": "Layout",
    "links.arch.title": "Repository Constellation",
    "links.arch.item1": "framework repo for reusable tools",
    "links.arch.item2": "character repo for voices, refs, and mood fragments",
    "links.arch.item3": "Hugging Face for large assets",
    "links.arch.item4": "GitHub Pages for visual fronts",
    "links.external.tag": "Signals",
    "links.external.title": "Beyond this page",
    "links.external.repo": "GitHub framework repo",
    "links.external.example": "Mayuri-Amadeus character repo",
    "links.external.model": "Example HF model repo",
    "links.external.dataset": "Example HF dataset repo",
    "roadmap.tag": "Next",
    "roadmap.title": "What comes after this first release",
    "roadmap.item1.title": "1. Profile-driven workflows",
    "roadmap.item1.body":
      "Reduce command repetition and let character repos declare defaults more cleanly.",
    "roadmap.item2.title": "2. Ref packaging tools",
    "roadmap.item2.body":
      "Automate turning labeled candidates into a release-ready reference-bank structure.",
    "roadmap.item3.title": "3. Evaluation and CI",
    "roadmap.item3.body":
      "Add smoke tests, small evaluation helpers, and stricter repo validation."
  },
  zh: {
    title: "Persona-Forge",
    description:
      "Persona-Forge 是一个围绕 GPT-SoVITS、参考库工具和发布工作流组织的通用角色语音训练框架。",
    "landing.kicker": "角色语音框架",
    "landing.quote":
      "在群星与代码之间，一套角色语音系统开始成形。",
    "landing.subquote":
      "一个以本地工作流为核心、围绕 GPT-SoVITS、参考库与本地推理组织起来的角色语音框架。",
    "landing.button": "进入框架页",
    "hero.eyebrow": "角色语音工具链",
    "hero.lede":
      "一个面向二次元与角色语音系统的可复用框架：涵盖 manifest 构建、GPT-SoVITS 训练封装、参考音频情感标注与本地推理。",
    "hero.repoButton": "GitHub 仓库",
    "hero.exampleButton": "角色实例仓库",
    "hero.kicker": "当前相位",
    "hero.status1.label": "模式",
    "hero.status1.value": "本地优先",
    "hero.status2.label": "后端",
    "hero.status3.label": "结构",
    "hero.status3.value": "双仓库拆分",
    "hero.status4.label": "状态",
    "hero.status4.value": "已做 smoke test",
    "hero.microcopy":
      "把可复用工具留在更高的一层，让每个角色沿着自己的世界线展开。",
    "visual.tag": "吸引场一隅",
    "visual.title": "同一片星空下，更安静的一幅坐标图",
    "visual.body":
      "星座线、仪器轮廓与笔记痕迹停在同一个画面里，像是观测开始变成方法的时刻。",
    "stats.cli": "核心 CLI 命令",
    "stats.repos": "仓库层级",
    "stats.instance": "已验证角色实例",
    "stats.version": "当前框架版本",
    "overview.tag": "框架边界",
    "overview.title": "Persona-Forge 应该负责什么",
    "overview.body":
      "Persona-Forge 只保留可复用工作流代码。角色专属数据、精选参考库、最终权重和 demo 应该放在独立的角色仓库中。",
    "overview.card1.title": "Manifest 构建器",
    "overview.card1.body":
      "把转写 CSV 和 wav 目录整理成 GPT-SoVITS 可直接使用的训练列表。",
    "overview.card2.title": "训练封装",
    "overview.card2.body":
      "直接跑 prepare、SoVITS 训练、GPT 训练和 SoVITS 导出，不必手工改上游配置。",
    "overview.card3.title": "参考库工具",
    "overview.card3.body":
      "标注情感候选、筛选参考音频，并把它们整理成稳定清晰的 reference bank。",
    "overview.card4.title": "仓库卫生",
    "overview.card4.body":
      "支持框架仓库、角色仓库、GitHub 与 Hugging Face 之间的干净分层。",
    "workflow.tag": "星图路径",
    "workflow.title": "从台词到稳定声线的一条路径",
    "workflow.body":
      "Manifest 构建、特征准备、分阶段训练、参考库整理与试听检查，都留在同一层框架工作流里。",
    "workflow.step1.title": "构建 manifest",
    "workflow.step1.body":
      "把转写 CSV 与 wav 路径规范化成单一训练列表。",
    "workflow.step2.title": "准备数据",
    "workflow.step2.body":
      "通过上游 GPT-SoVITS 脚本抽取文本、HuBERT、wav32k 和 semantic 特征。",
    "workflow.step3.title": "训练并导出",
    "workflow.step3.body":
      "分阶段训练 SoVITS 和 GPT，导出可推理权重，并保留可续跑 checkpoint。",
    "workflow.step4.title": "整理参考库",
    "workflow.step4.body":
      "标注并筛选参考音频，为情绪控制和试听 demo 做准备。",
    "quick.tag": "快速开始",
    "quick.title": "最小本地起步路径",
    "quick.body":
      "安装框架，指向一个现有的 GPT-SoVITS 克隆，然后先从 manifest 构建或 doctor 检查开始。",
    "commands.tag": "命令",
    "commands.title": "核心入口",
    "commands.item1": "从转写和 wav 文件生成训练列表。",
    "commands.item2": "执行上游特征抽取与 semantic 准备。",
    "commands.item3": "训练或续训声学 / 音色侧。",
    "commands.item4": "把 SoVITS checkpoint 导出成推理权重文件。",
    "commands.item5": "训练或续训 text-to-semantic 阶段。",
    "commands.item6": "用固定 GPT + SoVITS 组合生成语音。",
    "commands.item7": "通过 OpenAI 兼容接口标注并筛选参考音频。",
    "commands.item8": "在正式运行前检查本地依赖。",
    "links.docs.tag": "文档",
    "links.docs.title": "仓库内文档",
    "links.arch.tag": "布局",
    "links.arch.title": "仓库星图",
    "links.arch.item1": "框架仓库负责可复用工具",
    "links.arch.item2": "角色仓库负责声音、参考库与情绪碎片",
    "links.arch.item3": "大资产放 Hugging Face",
    "links.arch.item4": "视觉首页放在 GitHub Pages",
    "links.external.tag": "信号",
    "links.external.title": "页面之外",
    "links.external.repo": "GitHub 框架仓库",
    "links.external.example": "Mayuri-Amadeus 角色仓库",
    "links.external.model": "示例 HF 模型仓库",
    "links.external.dataset": "示例 HF 数据集仓库",
    "roadmap.tag": "下一步",
    "roadmap.title": "第一版发布之后继续做什么",
    "roadmap.item1.title": "1. Profile 驱动工作流",
    "roadmap.item1.body":
      "减少重复命令，让角色仓库能更干净地声明默认值。",
    "roadmap.item2.title": "2. 参考库打包工具",
    "roadmap.item2.body":
      "自动把已标注候选整理成适合发布的 reference bank 结构。",
    "roadmap.item3.title": "3. 评测与 CI",
    "roadmap.item3.body":
      "补上 smoke test、小型评测工具和更严格的仓库校验。"
  },
  ja: {
    title: "Persona-Forge",
    description:
      "Persona-Forge は GPT-SoVITS、参照バンクツール、公開向けワークフローを軸にした再利用可能なキャラクターボイス学習フレームワークです。",
    "landing.kicker": "キャラクターボイスフレームワーク",
    "landing.quote":
      "星図とコードのあいだで、ひとつの音声システムが形を帯びていく。",
    "landing.subquote":
      "GPT-SoVITS、参照バンク、ローカル推論を軸に、キャラクターボイスを形にしていくためのローカル主体フレームワークです。",
    "landing.button": "フレームワークへ進む",
    "hero.eyebrow": "キャラクターボイスツールキット",
    "hero.lede":
      "アニメ / キャラクター音声システム向けの再利用可能なフレームワーク。manifest 構築、GPT-SoVITS 学習ラッパー、参照音声ラベリング、ローカル推論までをまとめます。",
    "hero.repoButton": "GitHub リポジトリ",
    "hero.exampleButton": "キャラクター実例リポジトリ",
    "hero.kicker": "現在の位相",
    "hero.status1.label": "モード",
    "hero.status1.value": "ローカル優先",
    "hero.status2.label": "バックエンド",
    "hero.status3.label": "構成",
    "hero.status3.value": "二分割リポジトリ",
    "hero.status4.label": "状態",
    "hero.status4.value": "スモークテスト済み",
    "hero.microcopy":
      "再利用ツールをより高い層に置き、それぞれのキャラクターを別の世界線として扱うための構成です。",
    "visual.tag": "アトラクタフィールド",
    "visual.title": "同じ星空の下にある、より静かな座標図",
    "visual.body":
      "星座線、機材の輪郭、書き込みの跡がひとつの画面に重なり、観測が方法へ変わる瞬間を映しています。",
    "stats.cli": "主要 CLI コマンド",
    "stats.repos": "リポジトリ層",
    "stats.instance": "検証済みキャラクター実例",
    "stats.version": "現在のフレームワーク版",
    "overview.tag": "フレームワークの範囲",
    "overview.title": "Persona-Forge が担うもの",
    "overview.body":
      "Persona-Forge は再利用可能なワークフローコードだけを保持します。キャラクター固有データ、厳選参照バンク、最終重み、デモは別リポジトリで管理すべきです。",
    "overview.card1.title": "Manifest ビルダー",
    "overview.card1.body":
      "転写 CSV と wav ディレクトリから GPT-SoVITS 用の学習リストを生成します。",
    "overview.card2.title": "学習ラッパー",
    "overview.card2.body":
      "上流設定を手で編集せずに prepare、SoVITS 学習、GPT 学習、SoVITS 書き出しを実行できます。",
    "overview.card3.title": "参照バンクツール",
    "overview.card3.body":
      "感情候補のラベリング、参照候補の絞り込み、安定した参照バンクへの整理を支援します。",
    "overview.card4.title": "リポジトリ衛生",
    "overview.card4.body":
      "フレームワークリポジトリ、キャラクターリポジトリ、GitHub、Hugging Face の役割分離を支えます。",
    "workflow.tag": "星図の経路",
    "workflow.title": "台詞から安定した声線へ至る道筋",
    "workflow.body":
      "manifest 構築、特徴準備、段階的学習、参照整理、試聴確認までを 1 つのフレームワーク層に収めています。",
    "workflow.step1.title": "manifest 構築",
    "workflow.step1.body":
      "転写 CSV と wav パスを 1 つの学習リストへ正規化します。",
    "workflow.step2.title": "データ準備",
    "workflow.step2.body":
      "上流 GPT-SoVITS スクリプトでテキスト、HuBERT、wav32k、semantic 特徴を抽出します。",
    "workflow.step3.title": "学習と書き出し",
    "workflow.step3.body":
      "SoVITS と GPT を段階的に調整し、推論用重みを書き出し、再開可能な checkpoint を保持します。",
    "workflow.step4.title": "参照整理",
    "workflow.step4.body":
      "感情制御やデモ向けに参照音声をラベル付けし、候補を絞り込みます。",
    "quick.tag": "クイックスタート",
    "quick.title": "最小のローカル導入",
    "quick.body":
      "フレームワークをインストールし、既存の GPT-SoVITS クローンを指定して、まず manifest 構築か doctor から始めます。",
    "commands.tag": "コマンド",
    "commands.title": "主要エントリポイント",
    "commands.item1": "転写と wav から学習リストを生成する。",
    "commands.item2": "上流の特徴抽出と semantic 準備を実行する。",
    "commands.item3": "音響 / 音色側を学習または再開する。",
    "commands.item4": "SoVITS checkpoint を推論用重みへ変換する。",
    "commands.item5": "text-to-semantic 段階を学習または再開する。",
    "commands.item6": "固定 GPT + SoVITS 組み合わせで音声を生成する。",
    "commands.item7": "OpenAI 互換 API で参照候補をラベル付けして絞り込む。",
    "commands.item8": "本実行前にローカル依存を確認する。",
    "links.docs.tag": "ドキュメント",
    "links.docs.title": "リポジトリ内ドキュメント",
    "links.arch.tag": "レイアウト",
    "links.arch.title": "リポジトリ星図",
    "links.arch.item1": "フレームワークリポジトリは再利用ツールを担当",
    "links.arch.item2": "キャラクターリポジトリは声、参照、感情の断片を担当",
    "links.arch.item3": "大きな資産は Hugging Face へ",
    "links.arch.item4": "ビジュアルページは GitHub Pages へ",
    "links.external.tag": "シグナル",
    "links.external.title": "このページの先へ",
    "links.external.repo": "GitHub フレームワークリポジトリ",
    "links.external.example": "Mayuri-Amadeus キャラクターリポジトリ",
    "links.external.model": "例の HF モデルリポジトリ",
    "links.external.dataset": "例の HF データセットリポジトリ",
    "roadmap.tag": "次の段階",
    "roadmap.title": "この初版の次に進めること",
    "roadmap.item1.title": "1. Profile 駆動ワークフロー",
    "roadmap.item1.body":
      "コマンドの重複を減らし、キャラクター側で既定値をより整然と宣言できるようにする。",
    "roadmap.item2.title": "2. 参照バンク整形ツール",
    "roadmap.item2.body":
      "ラベル済み候補を公開向け reference bank 構造へ自動整理する。",
    "roadmap.item3.title": "3. 評価と CI",
    "roadmap.item3.body":
      "smoke test、小さな評価補助、より厳密なリポジトリ検証を追加する。"
  }
};

function applyLanguage(lang) {
  const locale = translations[lang] || translations.en;
  document.documentElement.lang = lang;
  document.title = locale.title;
  const meta = document.querySelector('meta[name="description"]');
  if (meta) meta.setAttribute("content", locale.description);
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (locale[key]) {
      node.textContent = locale[key];
    }
  });
  document.querySelectorAll(".lang-chip").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === lang);
  });
  localStorage.setItem("persona-forge-lang", lang);
}

const preferred = localStorage.getItem("persona-forge-lang");
const browserLang = navigator.language.startsWith("zh")
  ? "zh"
  : navigator.language.startsWith("ja")
    ? "ja"
    : "en";
const initialLang = preferred || browserLang;

document.querySelectorAll(".lang-chip").forEach((button) => {
  button.addEventListener("click", () => applyLanguage(button.dataset.lang));
});

applyLanguage(initialLang);
