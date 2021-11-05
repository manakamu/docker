■新コンテナの起動
docker-compose up -d --build

■使用していたコンテナの停止、削除
docker-compose down -v

■新たな設定でデータベースのマイグレート
docker-compose exec web python manage.py migrate --noinpu

■Djangoプロジェクト内のstatic関係のファイルを、nginxのstaticディレクトリへ移動する
docker-compose exec web python manage.py collectstatic --no-input --clear