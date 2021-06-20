#!/bin/bash
SCRIPT_DIR=$(cd $(dirname $0);pwd) #スクリプトのフルパス
LOCK_FILE="$SCRIPT_DIR/lock.pid"

if [ -e $LOCK_FILE ]; then
  #ロックファイルが存在する場合は何もしない
  echo "実行中。2重起動を禁止しています。"
else
  #ロックファイルがあれば作って処理を起動
  echo $$ > $LOCK_FILE #とりあえずプロセスIDを書き込んでおく
  
  #強制終了された時には子プロセスを殺してロックファイルを削除する
  trap 'kill $(jobs -p);rm -f $LOCK_FILE;echo 強制終了されました。' EXIT

  #処理本体
  /usr/bin/python3 $SCRIPT_DIR/main.py >>$SCRIPT_DIR/pole.log 2>>$SCRIPT_DIR/pole-err.log

  #ロックファイルを削除
  rm -f $LOCK_FILE 
fi
