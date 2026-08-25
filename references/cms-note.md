# note draft adapter

## 目次

1. [適用範囲](#適用範囲)
2. [外部変更前の条件](#外部変更前の条件)
3. [操作allowlist](#操作allowlist)
4. [画面と対象の解決](#画面と対象の解決)
5. [ログインhandleの検証](#ログインhandleの検証)
6. [下書きの新規作成と再開](#下書きの新規作成と再開)
7. [記事の適用](#記事の適用)
8. [下書き保存と再読検証](#下書き保存と再読検証)
9. [再試行](#再試行)
10. [失敗報告](#失敗報告)

## 適用範囲

このadapterはnoteの未公開下書きだけを作成、更新、保存、再読する。公開、予約投稿、販売設定、公開確認、アカウント切替は責務に含めない。

無料記事と有料記事の本文生成は共通の [paid-articles.md](paid-articles.md) が担当する。有料記事では無料部分、有料部分、価格案、有料ライン案までローカルに完成させられる。ただし、このadapterは販売設定画面へ遷移せず、価格や有料ラインをnoteへ設定しない。記事が完成していることと、note上で販売可能になっていることを混同しない。

browser providerは設定に従い、Chromeでは[browser-chrome.md](browser-chrome.md)、Safariでは[browser-safari.md](browser-safari.md)を読む。

## 外部変更前の条件

次をすべて満たすまでnoteへ書き込まない。

- Briefが設定済みautomation gateを通過している（`guided` は確認時刻、`autopilot` は解決時刻と空のconflicts）
- Article Packageのpreflightがpass
- title、body blocks、links、inline hashtags、images、thumbnailが確定済み
- 参照する画像が当該run配下にあり、相対パス、MIME、容量、寸法、hashを検証済み
- run stateとimmutable idempotency keyを保存済み
- browser providerが利用可能
- `.state/workspace.json` に育成時確認済みの `expected_account_handle` がある
- 現在ページが許可されたnote origin

条件不足時はローカル成果物を保持し、外部変更前に失敗報告を返す。

## 操作allowlist

許可する意味操作は次だけとする。

```text
observe_session
observe_account_handle
navigate_to_draft
find_existing_draft
create_new_draft
set_title
set_body_block
set_heading
set_link
set_inline_hashtags
upload_inline_image
upload_thumbnail
insert_embed
save_draft
observe_saved_state
reread_same_draft
verify_draft
verify_embed
```

次の操作はallowlistへ追加しない。

- 公開、投稿、Publish
- 予約投稿
- 公開または販売設定画面への遷移
- 公開確認の続行
- アカウント追加、ログアウト、アカウント切替
- Password、Cookie、token、MFA codeの入力、抽出、保存
- 下書き削除

許可操作と禁止操作を区別できない場合は停止する。ボタン名や画面位置から推測して操作しない。

## 画面と対象の解決

固定CSS selector、class名、XPath、DOM順、固定座標を保存またはハードコードしない。各操作の直前にsemantic observationを取り、次の順で一意な対象を解決する。

1. roleとaccessible name
2. labelまたは表示名
3. placeholder
4. 周辺見出しと対象の関係

対象が0件または複数件なら書き込まない。未知画面、許可外origin、公開関連画面、エディタ以外への予期しない遷移では停止する。

UI文言は観察から得た現在値を使う。既知の日本語または英語ラベルは意味確認の候補にできるが、selectorやクリック位置として固定しない。

## ログインhandleの検証

記事編集前に、現在ログイン中のnoteアカウントを検証する。

1. account menuまたはログイン中ユーザーのprofile linkをsemantic observationで一意に特定する。
2. display nameやavatarではなく、現在アカウントのcanonical handleを抽出する。
3. 候補がない、複数ある、handleを確定できない場合は停止する。
4. `.state/workspace.json` の `expected_account_handle` と、抽出したcanonical handleを完全一致で比較する。
5. `manage.py verify-account --observed-handle <canonical-handle>` が成功した場合だけ下書き操作へ進む。

先頭の `@` など表示上の表記差はオンボーディング時にcanonical formへ保存しておき、stage時に曖昧な正規化をしない。大小文字差、部分一致、profile URLの類似、display name一致を許可しない。

不一致時は `account_mismatch` として停止し、期待handleと観察handleを報告する。自動で正しいアカウントを探したり切り替えたりしない。

## 下書きの新規作成と再開

### 既存下書き

run stateに `draft_ref` または `draft_url` がある場合は、同じ下書きだけを開く。現在のtitleとcontent fingerprintを読取り、前回checkpointまたは期待manifestと一致することを確認してから不足部分だけを適用する。

既存内容が別記事を示す場合は上書きせず `draft_conflict` で停止する。

### 新規下書き

保存済みDraftRefがない場合だけ、新規記事作成の意味対象を一意に確認して一度だけ実行する。idempotency keyは `new-run` 時に保存する。作成直後、titleやbodyを入力する前に取得できた `draft_ref` と `draft_url` をcheckpointする。

新規作成後に接続が切れ、DraftRefを保存できたか不明な場合は二つ目を作らない。下書き一覧を読取り専用で確認し、run ID、title候補、作成時刻、content fingerprintから候補を一件へ絞る。確定できなければ利用者へ確認を求める。

## 記事の適用

### Titleとbody

- titleはArticle Packageの値を一度適用し、再観察して一致を確認する。
- bodyは正規化済みblock順に `paragraph / heading / list / quote / image / inline_hashtags` を適用する。
- subtitle専用入力が安全に確認できない場合は、Article Packageで指定された本文blockとして扱い、未知のUIへ入力しない。
- placeholder、内部claim ID、生成指示を本文へ残さない。

### Headings

heading blockごとにlevelと本文を適用する。現在のeditorが提供するsemanticなformat controlまたはbrowser documentationで保証された入力方法だけを使う。levelを確認できなければ通常本文へ黙って変換せず停止する。

### Links

credentialを含まない検証済み`https` URLだけを使用する。意味のある対象テキストとlink controlを一意に確認し、適用後にanchor textと遷移先を再読する。URL自体を表示名にせず、通常段落へ生URLを残さない。link controlを安全に使えない場合は`save_unverified`とする。リンク先を開く必要がある場合も、現在の下書きを失わない読取り方法だけを使う。

### Code blocks

- Article Packageの各code fenceを、一つのsemantic code blockとして適用する。空行を境に通常段落や番号付きリストへ分割させない。
- editorが空行でcode blockを終了する場合は、その空行だけASCII space一文字にする。比較時は各行の末尾ASCII spaceとtabを除いてsource fenceと一致させる。zero-width文字、全角空白、見えない制御文字はcopy時の事故になるため使わない。
- 保存前と再読後に、code block数だけでなく全文、順序、先頭行を照合する。source fenceの先頭行または続きが通常の`p`、`li`へ漏れていないことも確認する。
- 一件でも分割、欠落、順序不一致、通常本文への漏れがあれば`verified`にしない。

### Images

- 当該runのmanifestにある検証済みファイルだけをuploadする。
- inline imageは指定されたblock位置で一件ずつuploadし、完了状態を確認してから次へ進む。
- hashまたは配置から既に存在すると確認できた画像を再uploadしない。
- 画像数、順序、placementを再読検証する。
- alt text入力がeditor上で安全に利用できる場合だけ設定し、未対応ならreceiptへ明示する。
- browserがローカルファイル送信を拒否した場合は、次の画像へ進まない。本文がautosaveされていてもstageは完了ではなく `save_unverified` とし、`error_code: browser_file_transfer_rejected`、挿入できなかった画像path、同じ下書きでの再開手順を記録する。

### Thumbnail

thumbnail指定がある場合だけ一件uploadする。inline imageをthumbnailとして推測流用しない。upload後にthumbnail previewまたは同等の現在状態を確認する。

### Inline hashtags

Article Packageの `inline_hashtags` を本文末尾の専用blockとして入力する。各値は先頭 `#` を一つだけ持つ検証済みテキストとし、重複を除く。公開設定画面のtag UIへ移動しない。

### Rich media embeds

Article Packageまたはrich-media planにrequiredなembedがある場合だけ、現在のsemanticな「埋め込み」controlを使う。検証済みcanonical HTTPS URLを一件ずつ入力し、provider、title、preview、前後blockの順序を観察してから次へ進む。検索結果redirect、広告URL、短縮URLへ置換しない。

前回記事・関連記事として独立blockに置くnote記事URLは、`article-package.json embeds` にある場合、対応するMarkdown fallback anchorの位置でnote標準の記事カードへ置き換える。成功時に通常linkを重複表示しない。本文中の引用linkまで一律にカード化しない。

previewが失敗した場合は同じcanonical URLのcaptionと通常linkを残し、required embedを完了扱いにしない。その時点で後続embedの挿入も止め、未完了suffixをreceiptへ `embed:<canonical-url>` として記録して`save_unverified`とする。別動画を推測で選ばない。

## 下書き保存と再読検証

記事適用後、意味が一意な下書き保存controlまたはbrowser documentationで保証されたautosave状態だけを使用する。「公開」「投稿」「次へ」「Publish」と区別できないcontrolは操作しない。

成功判定には次の両方が必要である。

1. 現在画面で下書き保存済み状態を観察した。
2. 同じ `draft_ref` または `draft_url` を安全に再読し、期待manifestと一致した。

再読では次を確認する。

- titleの完全一致
- 正規化した本文block、heading level、順序のfingerprint一致
- code fenceごとの正規化全文と順序の一致、および通常本文へのcode漏れが0件
- anchor textとURL
- unordered／ordered listの種類、全item、順序
- quote blockの全文と順序
- 生URL、疑似list、平文化したcodeが0件
- inline hashtags
- 必須inline imageの数と順序
- thumbnailの存在
- required embedのURL、provider/title、数、順序
- `verified_embeds` がArticle Package内のrequired embedと完全一致
- 同じDraftRefであること

保存表示だけ、URL取得だけ、本文の一部一致だけでは成功にしない。両条件を満たした場合だけ `verification.status: verified`、`published: false` のreceiptを保存する。判断不能なら `save_unverified` とする。

schema 3 receiptでは `article-package.json` と次を一致させる。

- `expected_body_image_count`: manifestのbody image数
- `observed_body_image_count`: 再読で確認したbody image数
- `verified_image_paths`: manifestと同じ順序のrun相対path
- `thumbnail_present`: thumbnail必須時は `true`
- `verified_thumbnail_path`: 確認したthumbnailのrun相対path
- `rich_text.headings_match`: heading level、全文、順序が一致
- `rich_text.lists_match`: list種類、全item、順序が一致
- `rich_text.quotes_match`: quote全文、順序が一致
- `rich_text.code_blocks_match`: code block全文、順序が一致し、本文への漏れがない
- `rich_text.anchor_links_match`: 成功したembed fallbackを除く通常linkの表示名とHTTPS遷移先が一致
- `rich_text.no_exposed_raw_urls`: code block外の生URLが0件

一つでも不足、順序不一致、観察不能なら `verified` にしない。本文だけ一致した状態を記事全体の完了として報告しない。

## 再試行

- 読取り、待機、同じDraftRefへの不足分適用だけを冪等再試行できる。
- 新規下書き作成、ログイン、MFA、CAPTCHA、アカウント切替、公開関連操作は自動再試行しない。
- 各再試行前にcheckpointと現在のDraftRefを確認する。
- 既に一致するtitle、block、link、image、thumbnailを再入力しない。
- browser provider変更は同じstage内で自動実行しない。

## 失敗報告

失敗時はローカル成果物を保持し、次の形式で報告する。

```text
phase: <intake|research|outline|draft|images|preflight|stage|verify>
operation: <失敗したallowlist actionまたは能力確認>
provider: <chrome|safari>
error_code: <stable_error_code>
cause: <観察できた直接原因>
expected_account_handle: <育成済みhandleまたは未設定>
observed_account_handle: <安全に確認できたhandleまたは不明>
last_checkpoint: <最後に完了したcheckpoint>
draft_ref: <既知の場合>
draft_url: <既知の場合>
external_mutation: <none|draft_created|draft_updated|save_unverified>
retryable: <true|false>
retry_steps:
  - <同じ下書きを安全に再開する手順>
manual_steps:
  - <利用者がnote上で行う最小手順>
local_artifacts:
  - <article.md、画像、manifestなどの相対パス>
```

推測した原因や成功を記載しない。手動手順にはtitle、body、heading、link、画像順、thumbnail、inline hashtags、既知の下書きURLを含め、公開操作を案内しない。

画像不足時の利用者向け先頭文は次の形にする。

```text
下書き本文は保存されましたが、画像3枚の挿入は完了していません。状態は save_unverified です。
```

「保存しました」「確認済み」を先頭に置かず、部分成功を全体成功に見せない。
