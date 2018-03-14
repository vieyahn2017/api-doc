## app是简单的angularjs app

无法直接点击html运行，会报错，如下的跨域错误
```
XMLHttpRequest cannot load file:///***/api-doc/app/view/index.html. 
Cross origin requests are only supported for protocol schemes: http, data, chrome, chrome-extension, https.
(anonymous) @ angular.min.js:71
```

### 要用web服务器来运行
我尝试过的三种方式：

## 1.用tomcat启动 
apache-tomcat-8.0.37
将整个app考入$tomcat\webapps
编辑$tomcat\conf\server.xml，增加如下配置：
```
    <Host name="127.0.0.1" debug="0" appBase="webapps" unpackWARs="true" autoDeploy="true" xmlValidation="false"  xmlNamespaceAware="false"
      <Context path="" docBase="app" debug="0" reloadable="true" crossContext="true"/>
      <Logger className="org.apache.catalina.logger.FileLogger" directory="logs" prefix="tot_log." suffix=".txt" timestamp="true"/>
    </Host>
```
其中关键字段是docBase=app（app是本文件夹名）

## 2. 用nginx启动
暂略

## 3. 安装nodejs，用http-server启动

安装：通过npm进行全局安装
npm install http-server -g
启动：
进入app文件夹，在当前文件夹内输入命令http-server即可

默认端口8080。 带端口的启动方式 http-server -p 8080
