■コンテナにログインして、シェルスクリプトに実行属性を付ける
docker exec -it my-redmine bash
chmod a+x reminder.sh

■crontabに下記を登録する
0 7,17 * * * docker exec my-redmine /usr/src/redmine/reminder.sh
