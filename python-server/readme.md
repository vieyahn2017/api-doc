基于tornado-restful-seed种子项目而来。


### 说明：
Python后台采用的schematics封装的mongodb的orm，
本身支持的数据类型有基础类型（StringType, IntType, BooleanType），
有复合类型（ListType, DictType, PolyModelType）。
目前的参数项只支持一级子目录，
是因为schematics的ListType也只是实现了对StringType的包含（保存子参数id用），
因此实现支持多级目录还是比较难。


### 尾声：

【 version2.0已经修改了取了巨大进步，但是目前的局限性不容易克服。
不一定说实现不了，但是我考虑到技能覆盖面的问题。决定新的后台，转用java重写一版，也正好练练手。】


### 当初的todo：
加一个tornado编写的mongodb数据库可视化工具。