#查看删除我的好友-web版本

基于git大神[0x5e](https://github.com/0x5e)的项目[查看被删的微信好友](https://github.com/0x5e/wechat-deleted-friends)。用webpy二次开发的web版本。Demo地址：http://139.196.22.71:8890

#### 功能

1. 可以当微信群发消息用。
2. 查找已经删除自己的好友。并且列到对话的最顶端，方便手动删除。
3. 原项目方便程序员使用。此版本方便所有人使用。

#### 依赖：

在原项目的基础上，加了以下依赖：

1. webpy
2. Jinja2
3. MySQLdb(因为在多线程时，session没法保存状态，所以偷懒用了mysql)