# firstrepo
    bot example

# jsonファイルの秘匿方法の提案
## 1. Google Cloudに保存→pythonから取得
    一番手軽、無料体験期間があるのが良い
    https://iret.media/127289
    を参考に読み込むだけ
    リンクは環境変数にTOKENとして突っ込むとかして見えないようにするとかの対策は色々考えられそう
## 2. さくらクラウドに保存→pythonから取得
    鯖代が最初からかかるのでGCとおんなじ感じになりそう
## 3. aws-secretsmanager-get-secretsをgithub actions で使う
    勉強不足なのでよくわからん、Azureのもあったけど使えれば便利なんかなぁ