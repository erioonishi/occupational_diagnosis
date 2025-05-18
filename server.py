import http.server #標準ライブラリのhttp.serverモジュールをインポート。簡易なWebサーバーを作るのに使う
import socketserver #TCPソケットサーバーを作るためのモジュール。http.serverと組み合わせて使う
import threading #スレッド(並行処理)を扱うためのモジュール。サーバーを止める処理に使う
import json #JSON形式のデータの読み書き

PORT = 8000 #サーバーが使うポート番号を指定。この場合http://localhost:8000でアクセス【下に追記】
result_data = {} #診断結果などのデータを格納するための空の辞書(dict)を用意

#サーバーオブジェクトを外で定義（shutdown用）
httpd = None #グローバル変数として、サーバーインスタンス(TCPServerオブジェクト)を保存するための変数

#リクエスト処理用のクラスを定義しますSimpleHTTPRequestHandlerを継承して、GET/POSTを独自処理
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self): #ブラウザなどからのGETリクエストを処理
        if self.path == '/shutdown': #パス/shutdownにアクセスされたときの処理です(=閉じるボタンを押したとき)
            self.send_response(200) #ステータスコード200OKを送信【下に追記】
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers() #ヘッダーにtext/plain(プレーンテキスト)を設定しヘッダーの送信を終了
            self.wfile.write("サーバーを停止します。ブラウザを閉じてください。".encode('utf-8'))
           
            # 安全な shutdown（別スレッドで即座に閉じる）
            threading.Thread(target=shutdown_server, daemon=True).start() #shutdown_server関数を別スレッドで実行して、サーバー停止を安全に行う
        
        elif self.path == '/result': #パス/resultにアクセスされたときの処理(診断結果ページ用)
            #結果データをJSONで返す
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result_data).encode('utf-8')) #result_data(診断結果)をJSON文字列に変換して送信
        else:
            #通常のファイル配信
            if self.path == '/':#【下に追記】
                self.path = '/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self): #クライアント(診断アプリ)が結果を送信してきたときの処理
        if self.path == '/submit_result': #パスが/submit_resultのとき(診断結果の送信処理)
            content_length = int(self.headers['Content-Length']) #POSTデータの長さ(バイト数)を取得
            post_data = self.rfile.read(content_length) #POSTリクエストのデータ本体を読み取り
            result = json.loads(post_data) #受け取ったJSON文字列をPythonの辞書型に変換
            global result_data #result_dataという変数に結果を保存(あとで/resultに返す用
            result_data = result  #サーバー内の結果データを更新
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            #結果を正しく受け取ったことをクライアントに伝えるレスポンス(JSON形式)を返す
        else:
            self.send_response(404)#/submit_result以外のPOSTリクエストには「404 Not Found」で応答

def shutdown_server():
    global httpd #停止スイッチ用のグローバル変数
    print("サーバーを停止中...")
    httpd.shutdown()
    httpd.server_close()
    print("サーバーを停止しました。")

def run_server():
    global httpd #グローバル変数のhttpdに格納されたサーバーをシャットダウンして閉じる
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd_instance:
        httpd = httpd_instance  # shutdown用に保存
        print(f"サーバーを起動しました → http://localhost:{PORT}")
        try:
            httpd.serve_forever() #サーバーをずっと動かす(リクエストを待つ)
        except KeyboardInterrupt:
            print("\n手動でサーバーを停止します。")
            shutdown_server()

if __name__ == '__main__': #このファイルを直接実行した場合にサーバーを起動するための記述【下に追記】
    run_server()
'''
★TCPソケットサーバー
TCP(ransmission Control Protocol)という通信方式を使って、データをやりとりする「受け手」となるサーバーのこと
<例>
⓵サーバーは「ポスト」：クライアントがメッセージを投函する場所
⓶ライアントは「郵便配達員」：ポストに届けたり、受け取ったりする
⓷CPソケットは「ポストの口」：データの入口（IPアドレスとポート番号で特定）

★サーバーインスタンスって
次のようなコードがあるとする
with socketserver.TCPServer(("", 8000), MyHandler) as httpd:
ここでhttpdは、あなたのPC上で動いているWebサーバーの実体(インスタンス)を意味
この httpd を使って、サーバーを動かしたり（httpd.serve_forever()）
停止したり（httpd.shutdown()）
閉じたり（httpd.server_close()）することができる

★ポート番号8000
ポート番号は「部屋の番号」のようなもので、1つのPCの中に複数のサーバーがあってもいいように、それぞれに番号をつけている
80：本来のWeb(http)の標準ポート(ブラウザが自動でアクセス)
8000：よく開発用として使われる番号(本番用ではない)
理由：標準ポート（80）は管理者権限が必要
    8000 は自由に使えるし、開発用サーバーのデフォルトでよく使われる

★ステータスコード 200 OK
Webのやりとりでは、リクエストに対して「どうなったか」を3ケタの数字ステータスコードで返します。
コード	    意味
200	        成功（OK）
404	        見つからない（Not Found）
500	        サーバーエラー

★トップページ(/)の場合はindex.htmlにリダイレクト
if self.path == '/':
    self.path = '/index.html'
URLの末尾が /（トップページ）だったら、自動的に/index.htmlを表示するようにする
これはWebの習慣で/にアクセスされたときに、サーバーはよくindex.htmlを返すようになっている

★if __name__ == '__main__':
    run_server()
このファイルが直接実行された時だけ、run_server()を呼んでサーバーを起動
もし他のファイルからこのファイルをimportしただけならサーバーは起動しない

★グローバル関数について
サーバーの停止を一回目終了の時の処理ともう一度診断したときにも使いたい
◇ローカル関数との違い
グローバル関数（大域）	             ローカル関数（局所）
スクリプト全体から呼び出せる	     関数の中など、限られた場所でしか使えない
よく使う処理に便利	                一時的な処理や他から隠したい処理に使う
◇今回のコード
def shutdown_server():
    global httpd
    print("サーバーを停止中...")
    httpd.shutdown()
    httpd.server_close()
    print("サーバーを停止しました。")
ファイルのトップレベルで定義されていてどこからでも呼び出せるようになっている(今回だとMyHandlerの中からも呼んでいる)
◇グローバル関数の必要性
共通処理をどこからでも呼び出せるようにするため
⓵サーバーの停止処理をまとめて一か所に書いておきたい
⓶いろんな場所から(ハンドラの中でも)呼び出したい
'''