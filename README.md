# Paper Agent

ローカルLLMを使って論文を読み取り、共通観点で整理・比較するための最小エージェントです。

Google Agent Development Kit (ADK) から実行できます。

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Ollama を起動し、利用するモデルを取得してください。

```bash
ollama pull llama3.1
ollama serve
```

ADK で使うモデルは環境変数で変更できます。

```bash
export ADK_OLLAMA_MODEL=llama3.1
export OLLAMA_API_BASE=http://localhost:11434
```

ADK の論文読み取りツールは、デフォルトでは起動した作業ディレクトリ配下のファイルだけを読み取ります。
別ディレクトリの論文を扱う場合は、許可するディレクトリを明示してください。

```bash
export PAPER_AGENT_ALLOWED_DIR=/path/to/papers
```

## Usage

ADK の対話CLIで起動します。

```bash
adk run paper_agent_adk
```

1回だけ問い合わせる場合:

```bash
adk run paper_agent_adk "path/to/paper.pdf を読んで、研究目的と提案手法を整理してください"
```

Web UIで試す場合:

```bash
adk web .
```

ブラウザで `http://localhost:8000/` を開き、エージェント一覧から `paper_agent_adk` を選択してください。

このADK agentは `paper_agent_adk/agent.py` の `root_agent` で定義されています。論文ファイルを読むためのツールとして `load_paper_for_analysis` と `load_papers_for_comparison` を使います。

## Output Policy

- 論文に書かれている内容と解釈を区別します。
- 根拠となる page/chunk を可能な限り保持します。
- 論文に記載されていない内容は断定せず、「記載なし」または不明点として扱います。
