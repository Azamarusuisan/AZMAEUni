# Brain capability observation

## QA Brief

- Purpose: verify the Brain draft adapter against the live editor
- User authorization: create and edit one unpublished QA draft
- Publication: prohibited
- Sale activation: prohibited
- Account switching: prohibited
- Test title: `Brain adapter capability test`
- Test body: `This unpublished draft is used only to verify the Brain editor adapter.`
- Price, referral rate, and paywall: observe controls only; do not confirm or save values

## Environment

- Observed: 2026-07-31
- Browser: dedicated Hermes Chrome profile
- Origin: `https://brain-market.com`
- Draft state: one empty draft created by the user

## Editor observations

- The title is uniquely resolvable by placeholder `記事タイトルを入力`.
- The body is the only live `role=textbox` editing region.
- The main-image file input is uniquely related to the visible text
  `メイン画像をアップロードする` and `推奨サイズ：横1280px × 縦670px`.
- A second JPEG/PNG file input remains after excluding the main-image input and
  is reserved for inline body images.
- `下書き保存`, `プレビュー`, and `販売設定に進む` are each uniquely exposed
  as named buttons.
- The sales-settings button does not navigate while the required title and body
  are empty.

## Pending observations

- Paywall insertion control and resulting block boundary
- Price field
- Referral-rate field
- Draft-only sales-setting state
- Save indicator and reread verification
