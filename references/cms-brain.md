# Brain draft adapter

## 目次

1. [適用範囲](#適用範囲)
2. [実装状態と能力確認](#実装状態と能力確認)
3. [noteとの共通部分](#noteとの共通部分)
4. [外部変更前の条件](#外部変更前の条件)
5. [操作allowlist](#操作allowlist)
6. [ログインhandleの検証](#ログインhandleの検証)
7. [販売条件の確定](#販売条件の確定)
8. [有料ラインの配置](#有料ラインの配置)
9. [記事の適用](#記事の適用)
10. [下書き保存と再読検証](#下書き保存と再読検証)
11. [失敗報告](#失敗報告)

## 適用範囲

このadapterはBrainの未公開下書きだけを作成、更新、保存、再読する。販売開始、公開、価格の確定反映、紹介設定の確定反映、アカウント切替は責務に含めない。

Brainは有料記事の販売と紹介機能を持つため、noteに無い次の三つを扱う。

- 価格
- 紹介（アフィリエイト）率
- 有料ラインの位置

これらは金銭に直結するため、保存済み設定から推測しない。実行のたびに利用者へ確認する。

## 実装状態と能力確認

現時点でBrainエディタに対するsemantic observationの検証が完了していない。検証が完了するまで、このadapterは次のように振る舞う。

1. Brain経路が要求された時点で能力確認を行い、確認できない場合は `brain_adapter_unavailable` を返して停止する。
2. ローカルの `article.md`、画像、`image-plan.md` を完成させた状態で保持する。
3. 利用者へ手動の貼り付け手順を提示する。手順には title、本文、見出し、リンク、画像順、アイキャッチ、有料ラインの位置候補を含める。価格と紹介率は利用者が決める項目として空欄で示す。

「Brainへ保存した」と報告してよいのは、[下書き保存と再読検証](#下書き保存と再読検証)の両条件を満たした場合だけとする。UIを操作できなかった実行を成功として扱わない。

## 規約由来の運用制約

Brainの販売者用および購入者用の利用規約には、自動化ツール、ボット、スクレイピング、クローラ、プログラムによるアクセス、APIに関する記述が存在しない。明示的な禁止も明示的な許可もない状態であるため、次の二つの包括条項に抵触しない側へ倒して運用する。

- 本サービス又はサーバーに対する妨害と運営が判断する行為
- その他運営が不適切と判断する行為

いずれも運営の裁量で判定され、該当と判断された場合は提供停止、登録抹消、サーバー内データ削除が行われうる。販売者アカウントは本人確認書類と決済手段に紐づくため、停止の影響はnoteより大きい。また規約は、IDを利用して行われた行為の責任をID保有者に帰属させる。自動操作の結果は利用者の責任になる。

この前提から、Brain経路には次を課す。

- **無人実行の対象外とする。** 定期実行からBrainへ書き込まない。利用者が同席する実行だけで操作する。詳細は [scheduling.md](scheduling.md) を読む。
- **1回の実行で扱う記事は1本までとする。** 連続投稿、まとめ投稿、複数記事の並列処理を行わない。
- **操作は人の操作速度を超えない。** 画面遷移と入力の間に観察を挟み、待機を省いた連続実行を行わない。
- **読み取りのポーリングを行わない。** 保存状態と再読検証は必要最小限の回数にとどめる。
- **失敗時に自動で繰り返さない。** 再試行の上限は既定の範囲を超えず、失敗が続く場合は停止して利用者へ報告する。
- **他者のアカウント、他者の記事、購入者情報を収集しない。** 操作対象は利用者自身の下書きだけとする。

利用者が本人確認済みの自分のアカウントで、同席のうえ、自分の記事の下書きを作る。この範囲を超える使い方へ拡張しない。規約は改定されうるため、Brain経路の能力確認時に現行の規約を確認する。

## noteとの共通部分

次は [cms-note.md](cms-note.md) の規定をそのまま適用する。ここでは差分だけを定義する。

- 画面と対象の解決（固定selector、XPath、DOM順、固定座標を保存しない）
- 下書きの新規作成と再開、DraftRefのcheckpoint、二重作成の防止
- 再試行の範囲
- 失敗報告の形式

browser providerは設定に従い、Chromeでは [browser-chrome.md](browser-chrome.md)、Safariでは [browser-safari.md](browser-safari.md) を読む。

## 外部変更前の条件

[cms-note.md](cms-note.md) の条件に加えて、次をすべて満たすまでBrainへ書き込まない。

- `.state/workspace.json` に育成時確認済みの `expected_brain_handle` がある
- 現在ページが許可されたBrain origin
- 当該runの `brief.json` に、利用者が今回の実行で確認した価格と紹介率がある
- 有料ラインの位置が `outline.md` 上で確定している
- Brain adapterの能力確認に成功している

いずれかが欠ける場合はローカル成果物を保持し、外部変更前に失敗報告を返す。

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
upload_inline_image
upload_thumbnail
set_paywall_position
set_price
set_referral_rate
save_draft
observe_saved_state
reread_same_draft
verify_draft
```

次の操作はallowlistへ追加しない。

- 販売開始、公開、Publish
- 予約公開
- 販売状態の切替
- 出金、売上、口座に関わる画面への遷移
- アカウント追加、ログアウト、アカウント切替
- Password、Cookie、token、MFA codeの入力、抽出、保存
- 下書き削除

`set_price` と `set_referral_rate` は下書き上の入力にとどめる。販売開始を伴うcontrolと区別できない場合は操作しない。

## ログインhandleの検証

手順は [cms-note.md](cms-note.md) の「ログインhandleの検証」と同一とし、比較先だけを `expected_brain_handle` に置き換える。

```bash
python3 <skill-directory>/scripts/manage.py verify-account \
  --workspace <workspace> --platform brain --observed-handle <canonical-handle>
```

noteのhandleとBrainのhandleが同一文字列であっても、別プラットフォームの値として独立に保存し、独立に照合する。片方の照合結果をもう片方へ流用しない。

不一致時は `account_mismatch` として停止し、期待handleと観察handleを報告する。自動で正しいアカウントを探したり切り替えたりしない。

## 販売条件の確定

記事本文が確定したあと、Brainへ触れる前に次を利用者へ提示して確認する。

```text
title: <確定タイトル>
price: <利用者が指定した金額>
referral_rate: <利用者が指定した率>
paywall_after: <有料ラインを置く見出しまたはblock>
free_ratio: <無料部分が全体に占めるおおよその割合>
```

- 価格と紹介率は毎回確認する。前回値、他の記事、他の利用者の設定から引き継がない。
- 利用者が金額を決められない場合は下書きを作らず、記事とアイキャッチをローカルに残して停止する。
- 確認結果は `brief.json` へ、確認時刻とともに保存する。
- 無人実行では確定しない。詳細は [scheduling.md](scheduling.md) を読む。

## 有料ラインの配置

有料ラインは、購入判断に必要な情報が無料部分に揃ったあとへ置く。

- 無料部分だけで、記事が扱う問題と結論の方向が読者に伝わること。
- 有料部分の直前で話題を不自然に切断しないこと。
- 見出しの途中ではなく、blockの境界へ置くこと。
- 位置は `outline.md` で本文執筆前に決め、執筆後に変更した場合は利用者へ再確認する。

無料部分が記事全体をほぼ含む場合、および無料部分だけでは記事の主題が判別できない場合は、どちらも位置を再検討する。

## 記事の適用

title、本文block、見出し、リンク、画像、アイキャッチの適用手順は [cms-note.md](cms-note.md) の「記事の適用」に従う。差分は次のとおり。

- アイキャッチはBrain側の現在の推奨比率を観察して正規化する。noteの `1280×670` を無検証で流用しない。
- 有料ラインは本文blockの適用が完了したあとに一度だけ挿入し、挿入後に位置を再観察する。
- 価格と紹介率は本文と有料ラインの適用が完了したあとに入力する。入力後、それぞれの現在値を再読して一致を確認する。
- inline hashtagsはBrain上での扱いが確認できるまで適用しない。

## 下書き保存と再読検証

成功判定には次の両方が必要である。

1. 現在画面で下書き保存済み状態を観察した。
2. 同じ `draft_ref` または `draft_url` を安全に再読し、期待manifestと一致した。

再読では [cms-note.md](cms-note.md) の確認項目に加えて次を確認する。

- 有料ラインが期待するblock境界にある
- 価格の現在値が確認済みの値と一致する
- 紹介率の現在値が確認済みの値と一致する
- 販売状態が未公開である

両条件を満たした場合だけ `verification.status: verified`、`published: false`、`for_sale: false` のreceiptを保存する。判断不能なら `save_unverified` とする。価格または紹介率が一致しない場合は `verified` にしない。

## 失敗報告

形式は [cms-note.md](cms-note.md) の「失敗報告」に従い、次の項目を追加する。

```text
expected_brain_handle: <育成済みhandleまたは未設定>
observed_brain_handle: <安全に確認できたhandleまたは不明>
price_confirmed: <true|false>
referral_rate_confirmed: <true|false>
paywall_position: <確定している場合のみ>
```

手動手順には有料ラインの位置候補までを含め、価格と紹介率は利用者が入力する項目として空欄で示す。販売開始の操作は案内しない。
