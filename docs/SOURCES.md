# 情報源の調査メモ

確認日: 2026年8月30日

このサイトは記事本文を取得せず、RSS/Atomに含まれる見出し・リンク・短い概要だけを正規化します。元記事ページのスクレイピングはしません。媒体名と元記事リンクを必ず表示します。

## 初期状態で有効

| 情報源 | 種類 | 主なカテゴリー | 確認内容 |
|---|---|---|---|
| NHK NEWS WEB | 公共放送 | 日本 | RSSがHTTP 200で取得可能 |
| 日本銀行 | 一次情報 | お金と暮らし | 公式サイトが総合RSSの提供を案内 |
| 国連ニュース | 国際機関 | 世界 | 公式RSSが取得可能 |
| KBS WORLD Japanese | 公共放送 | 韓国 | 公式ページが日本語ニュースRSSを案内。実取得も確認 |
| Blender Foundation | 公式技術情報 | アートと技術 | 公式フィードが取得可能 |
| NASA | 政府機関 | 科学と健康 | 公式ニュースリリースフィードが取得可能 |
| Smithsonian Magazine | 美術館系メディア | ちょっといい話 | 公式フィードが取得可能 |

## 初期状態で無効・見送り

- 厚生労働省: RSS自体は提供されていますが、RSS情報に基づくウェブサイトやメールマガジンの作成・再配布を営利・非営利を問わず禁止する注意書きがあるため、`enabled: false` にしています。
- 首相官邸: RSS案内に同種の再利用禁止があるため採用していません。
- Korea.net: 公式RSS案内ページは現存しますが、2026年8月30日の実取得では同一URLへの302転送が繰り返され取得不能だったため、KBS WORLD Japaneseへ切り替えました。
- e-Stat: RSS配信は2023年9月30日で終了したと公式案内に明記されています。

利用条件は変わることがあります。公開前および情報源追加時に各サイトの最新条件を再確認してください。

## 参照ページ

- https://www.boj.or.jp/whatsnew/
- https://world.kbs.co.kr/service/about_rss.htm?lang=j
- https://www.korea.net/Others/Subscribe-to-Koreanet/RSS-Service
- https://www.mhlw.go.jp/rss/
- https://japan.kantei.go.jp/rss.html
- https://www.e-stat.go.jp/rss
