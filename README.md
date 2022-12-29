<div align="center">
  <h1>RuFoundation - 中文翻译</h1>
  <h3>由SCP基金会俄罗斯分支开发的与Wikidot兼容的Wiki引擎</h3>
  <h4><a href="https://boosty.to/scpfanpage">#StandWithSCPRU</a></h4>
  <img src="https://i.kym-cdn.com/photos/images/facebook/001/839/765/e80.png" width="300px" alt="scp-ru">
</div>


## 配置要求

注意：这是我测试的，在你那里配置要求可能会有所不同。

* [Windows 10](https://www.microsoft.com/zh-cn/windows/?r=1)
* [NodeJS v17.3.0](https://nodejs.org/en/download/)
* [Python 3.10.1](https://www.python.org/download/)-译者注：需要添加python到根目录
* [Rust 1.63](https://www.rust-lang.org/zh-CN/)

## 如何启动？

* 首先，解压后进入解压文件夹，在命令行执行`web/jsyarn install`
* 之后，在项目的根目录下执行命令：
```
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver --watch
```


## Seeding the database

To start working, the following objects are required:

要播种数据库，需要下面的东西：
* 至少一个网站备份（在本地主机）
* 部分页面（例如`nav:top`和`nav:side`）对网站外观非常重要！

您可以通过运行以下命令来预配这些基本结构：

- `python manage.py createsite -s scp-ru -d localhost:8000 -t "SCP Foundation" -H "Russian branch"`
- `python manage.py seed -s scp-ru`

## 在Docker隔离沙箱运行

### Requirements (tested with):

- Docker 20.10.14
- Docker-Compose 1.29.2

### Getting started

To start the project, use:

- `docker-compose up`

To completely delete all data, use:

- `docker-compose down`
- `rm -rf ./files ./archive ./postgresql`

To create users, sites and seed inside the database, start the project and afterwards use syntax such as this:

- `docker exec -it scpdev_web python manage.py createsite -s scp-ru -d localhost -t "SCP Foundation" -H "Russian branch"`
- `docker exec -it scpdev_web seed -s scp-ru`

To update current app that is running, do:

- `docker-compose up -d --no-deps --build web`

Note: in more recent versions, you may want to use `docker compose` instead of `docker-compose`.

