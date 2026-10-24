# 地球から宇宙の果てへ — Space 001

70秒、縦型1080×1920、30fps、H.264/AAC MP4。ナレーションなし。全編独自生成CG、日英字幕、生成アンビエント音楽・移動効果音付き。6場面を加減速する透視投影、回転、奥行き、縮小、発光、1.15秒クロスフェードで接続する。

## GitHub Actions

このフォルダの内容をリポジトリ直下へ保存する。Actions → Render Space 001 → Run workflow。完了後、実行ページのArtifactsから `space-001` をダウンロードする（GitHubへのログインが必要、保持7日）。MP4は通常のGit履歴には入れない。

`publish_release` は既定でオフ。外部公開の承認がある場合だけオンにすると、ReleaseにもMP4と検証結果を添付する。公開リポジトリのReleaseは外部公開される。リポジトリ設定がActionsと必要なcontents:write権限を許可している必要がある。MP4はReleaseの単一ファイル2GiB制限より十分小さい想定で、実測サイズはquality_report.json参照。Actionsの利用枠・Artifact容量はアカウント契約によるため、有料枠を有効にしないこと。私有リポジトリでは無料残量を確認してから実行する。

## ローカル実行（Ubuntu）

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-noto-cjk
python -m pip install -r requirements.txt
python render.py
```

出力: `output/space_001.mp4`、代表フレーム6枚、`quality_report.json`、`layout.json`。720pの全尺プレビューは `python render.py --preview --out output/preview`。フレームをパイプで逐次FFmpegに渡し、全フレームをメモリに保持しない。音声合成のみ全尺の配列を使用（数百MB以下）。生成結果は乱数シード固定。OS・ライブラリ・エンコーダで僅かな差はあり得る。

## 品質確認

レンダリング後にverify.pyを自動実行。FFprobeで長さ、寸法、fps、映像・音声コーデックを確認。FFmpegで全尺デコード。1/8/22/36/50/64秒の字幕を除いた映像領域の輝度を確認。全描画字幕のbboxを安全域（横5.5〜89%、下84%以内）に照合。音声の有無、非無音、ピークを確認する。終端68〜70秒の暗転は意図した演出。TikTok UIは端末や表示形式によって変わるので投稿前に実機確認を推奨する。

これは宇宙のスケールを表すアート映像であり、観測画像・正確な軌道や宇宙論シミュレーションではない。全場面に「CG・模式表現 / Not to scale」を表示する。素材と権利はcredits.md参照。
