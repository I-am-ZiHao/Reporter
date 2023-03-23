# Reporter

當兵回報機器人

利用放假時間寫的 LineBot，用於整理大家的放假回報。<br>
主要用的是 Django + MongoDB。<br>

回報格式：<br>
時間：20:00<br>
學號：xxxxx<br>
姓名：xxx<br>
電話：09xxxxxxxx<br>
現在位置：在家<br>
現在在幹嘛：休息<br>
跟誰：家人<br>
身體狀況：良好<br>

初次使用請先輸入本班五碼學號範圍，格式如下：<br>
學號範圍：xxxxx-xxxxx<br>

接著輸入「確認學號範圍」檢查輸入是否正確。<br>

完成以上動作後可開始回報，輸入「他媽的回報」後，機器人便會按照學號順序進行統整；若尚未回報完，則機器人會回覆尚未回報之學號。<br>

輸入「使用說明」，機器人會回傳以上內容。

Local dev:
`python manage.py runserver`
