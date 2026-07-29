# Chrome browser provider

## 適用条件

`.state/workspace.json.browser` が `chrome` の場合だけ使用する。現在hostのDoctorで利用者が承認したChrome sessionだけを使う。providerは作業用tabを作成できる。既存profileへ接続できるproviderではそのlogin stateを保ち、Hermesが専用CDP browserを起動した場合は `/browser status` でsessionを確認して利用者が手動ログインしてから続行する。

外部変更前に[agent compatibility](agent-compatibility.md)で現在hostのChrome capabilityを確認する。利用できなければnoteへ移動せず、[cms-note.mdの失敗報告](cms-note.md#失敗報告)を返す。

## 接続手順

### Codex

1. ChatGPTのPlugins DirectoryでChrome pluginがインストール・有効化され、現在のWork/Codex chatへ公開されていることを確認する。
2. pluginが提供するChrome Skillと完全なtool documentationを読み、そこに記載された接続・観察・操作APIだけを使う。
3. `chrome:control-chrome` と `node_repl` が提供される環境では、そのインストール済みSkillの手順をそのまま使う。特定のscript pathやAPIを別環境へ仮定しない。
4. 接続またはbrowser選択に失敗した場合はpluginのtroubleshootingを読んで一度だけ復旧を試す。別のブラウザ制御方式へ無断で切り替えない。

### Claude Code

1. Claude in Chromeが現在のClaude Code sessionへ接続済みで、note.comへの操作許可があることを確認する。
2. 提供されたChrome tool documentationを完全に読み、そのtoolだけを使う。
3. providerが選んだ作業tab/sessionを観察し、noteへログイン済みか確認する。Claude側のpermission promptが出た場合は利用者の承認を待つ。
4. connector、site permission、または現在sessionを確認できなければ停止する。別browserやshell automationへ切り替えない。

### Hermes Agent

1. CLIで利用者が `/browser connect` を実行し、`/browser status` が利用者の承認したlocal Chromium CDP sessionを示していることを確認する。専用browserが起動した場合は利用者がnoteへ手動ログインする。
2. `browser_snapshot` で現在のsessionとnote画面を観察し、fresh refだけを `browser_click`、`browser_type`、upload capabilityに使う。
3. cloud/headless sessionや別profileへ黙って切り替えない。現在接続sessionが未ログインなら利用者に手動ログインを依頼する。
4. `browser_cdp` は通常toolで表現できず、current documentationで安全性を確認できた操作だけに限定する。

## セッション

- 現在hostのDoctorが確認したChrome sessionだけを使う。
- Cookie、local storage、Password、MFA code、session tokenを読み出し、保存し、会話へ表示しない。
- 未ログインなら利用者へChrome上での手動ログインを依頼して待機する。
- ログイン回避のために検索、別サイト、別ブラウザへ切り替えない。
- アカウント切替を操作しない。現在のhandleはnote adapterへ返し、一致判定を委ねる。

## 操作規則

現在hostの完全なbrowser documentationに記載されたAPIだけを使う。Codexでは現在のChrome pluginのtool documentationに明記された場合だけ、そのPlaywright APIを使う。ClaudeとHermesも接続済みbrowser capability以外のPlaywrightや別browser serverを起動しない。

各書込みの直前に画面を再観察し、次の順で一意な対象を解決する。

1. roleとaccessible name
2. labelまたは関連する表示テキスト
3. placeholder
4. 周辺見出しと対象の関係

CSS class、XPath、DOM位置、固定座標、過去の観察から保持したelement handleを操作契約へ保存しない。対象が0件または複数件なら書き込まず停止する。

各操作で次を確認する。

- 現在地がnote adapterの許可origin内
- 観察した画面種別が期待する画面と一致
- semantic targetが一意
- action IDがnote adapterのallowlist内
- 操作後の観察が期待状態と一致

未知画面、公開関連画面、MFA、CAPTCHA、利用規約同意、許可外originでは停止する。DOM全文、screenshot、認証状態は既定で永続化しない。

## note adapterへの返却

providerはページ固有の意味を推測せず、観察結果、現在URL、実行したaction ID、対象の一意性、操作後状態だけを返す。記事の作成、保存、再読検証は[cms-note.md](cms-note.md)に従う。
