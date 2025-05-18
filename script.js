let questions = [];//質問データを格納するための空の配列
let currentQuestion = 0;//現在表示中の質問のインデックス(0番目からスタート)を保持
let scores = {};//各職業に対するスコアを記録するオブジェクト<例>{ "パン屋": 10, "警察官": 4 }

fetch('questions.json')
    .then(response => response.json())//fetchで受け取ったレスポンスをJSON形式に変換
    .then(data => {
        questions = data;//読み込んだ質問データ(data)をquestionsにセット
        initScores();//スコアの初期化
        showQuestion();//最初の質問の表示
    });

function initScores() {//スコアを0で初期化する関数の定義
    questions.forEach(q => {
        q.choices.forEach(choice => {
            Object.keys(choice.impact).forEach(job => {
                if (!(job in scores)) {
                    scores[job] = 0;
                }
            });
        });
    });
}//すべての質問、すべての選択肢を見て、出てくる職業名(=choice.impactのキー)をスコアに追加
//まだscoresにその職業がなければ0で初期化

function showQuestion() {//質問を画面に表示する関数の定義
    const q = questions[currentQuestion];//現在の質問(インデックスcurrentQuestion)を取り出す
    document.getElementById('question-text').textContent = q.text;//質問文を<div id="question-text">に表示
    const choicesDiv = document.getElementById('choices');//選択肢を表示する場所を取得
    choicesDiv.innerHTML = '';//前の選択肢があれば一旦消す
    q.choices.forEach((choice, idx) => {
        const btn = document.createElement('button');
        btn.textContent = choice.option;
        btn.className = 'choice-btn';
        btn.onclick = () => selectChoice(btn, choice);
        choicesDiv.appendChild(btn);
    });//各選択肢についてボタンを作成し、選択されたときにselectChoice()を呼ぶ
    document.getElementById('next-btn').disabled = true;//選択肢を選ばないと「次へ」ボタンを押せないように、無効化
}

function selectChoice(btn, choice) {//ボタンを選択したときの処理を定義する関数
    document.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('selected'));//他の選択肢のボタンの「選択中スタイル（selected）」をすべて解除
    btn.classList.add('selected');//今選ばれたボタンだけにselectedクラスを付けて、見た目を変える
    Object.keys(choice.impact).forEach(job => {
        scores[job] += choice.impact[job];//この選択肢のimpact(影響値)を見て、それぞれの職業のスコアに加算
    });
    document.getElementById('next-btn').disabled = false;//選択肢が選ばれたので「次へ」ボタンを押せるようにする
}

document.getElementById('next-btn').onclick = () => {//「次へ」ボタンを押したときの処理
    currentQuestion++;//currentQuestionを1つ進めて
    if (currentQuestion < questions.length) {
        showQuestion();//まだ質問が残っていれば次の質問を表示
    } else {
        showResult();//全部終わったら結果を表示
    }
};

function showResult() {//診断結果を計算・送信する関数
    const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);//scoresの職業とスコアを配列にしてスコアが高い順に並び替え<例>[["パン屋", 15],["教師", 12],...]
    const topJob = sorted[0];//一番スコアの高かった職業を取り出す

    const resultToSend = {
        top_job: topJob[0],//1位の職業名
        top_score: topJob[1],//そのスコア
        top_three: sorted.slice(0, 3).map(([job, score]) => ({ job, score }))//上位3つの職業とスコア
    };

    fetch('/submit_result', {//サーバーに診断結果をPOSTで送る。内容はJSON形式
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(resultToSend)
    }).then(() => {
        //結果ページへ遷移
        location.href = '/result.html';
    });
}
