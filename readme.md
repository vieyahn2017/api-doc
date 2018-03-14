## api-doc
基于mongodb的api文档管理系统。

前端采用angularjs，python后端（tornado框架）。


## 使用方法
1. 后端，进入python-server，安装依赖库后，执行python server.py启动程序
2. 前端：对应app文件夹
前端的启动：  
详见 [app的readme](app//readme.md)   
修改app目录下的[base.js](app//base.js)，里面对应的后端服务器（主机和端口），即可启动前端



### TODO: 
1. 修除以前框架没用上的代码和模块，权限系统改写（用mongo简单实现一个）
2. mongodb编辑api的功能（！重点）
3. 计划加一个tornado编写的mongodb数据库可视化工具（robomongo一类的）
4. java后端和golang后端。
