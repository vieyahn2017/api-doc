/**
 ** yanghao 2017-7-14.
 */

function apiController($scope, $http, $q, $routeParams, $location, $window, $anchorScroll, $timeout) {

    var href = $routeParams.href;
    $scope.href = href;
    $scope.base_url = get_base_url();

    $scope.show_api_list = function () {
        // $http.get($scope.base_url + "m/api?desc=true&href=" + href).success(function(data){  //添加的时候倒序方便点
        $http.get($scope.base_url + "m/api?href=" + href).success(function(data){
            //console.log(data.rows);
            var apiListTemp = data.rows;
            for(var i = 0; i < apiListTemp.length; i++) {
                api_extend_fn(apiListTemp[i]);
            }
            $scope.apiList = apiListTemp;
            console.log($scope.apiList);
            $timeout(function(){
                var id = $routeParams.id;
                $scope.scrollTo(id);
            });
        }).error(function(){
            $scope.apiList = [];
        });
    };

    $scope.show_api_list();


    var api_extend_fn = function (api) {
        //console.log(api);
        var paramsList = api.paramsList;
        for(var i = 0; i < paramsList.length; i++) {
            var skip = 0;
            if(paramsList[i].children.length > 0) {
                for(var j = 0; j < paramsList[i].children.length; j++) {
                    var item = paramsList[i].children[j];
                    paramsList.splice(i + 1, 0, item); // splice(i, 0, item) i处，增加item, 0是删除0个元素
                    //console.log(paramsList[i+1] == item); //3.27 这边splice进去的item，应该和item是同一个对象？
                }
                skip = paramsList[i].children.length + 1;
            }
            i += skip;
            // if(i>20) break;
        }
        var responseList = api.responseList;
        for(var i = 0; i < responseList.length; i++) {
            var skip = 0;
            if(responseList[i].children.length > 0) {
                for(var j = 0; j < responseList[i].children.length; j++) {
                    var item = responseList[i].children[j];
                    responseList.splice(i + 1, 0, item); // splice(i, 0, item) i处，增加item, 0是删除0个元素
                }
                skip = responseList[i].children.length + 1;
            }
            i += skip;
            // if(i>20) break;
        }
        //console.log(api);
        return api;
    }

    $http.get($scope.base_url + "m/api/authenticated").success(function(data){
        if(data.code == 1) {
            $scope.authenticated = true;
        } else if (data.code == -1) {
            $scope.authenticated = false;
        }
        //console.log($scope.authenticated);
    }).error(function(){
        $scope.authenticated = false;
    });

    var uuid = function () {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
        });
    };

    var param_demo = function() {
        return {
            "name": "param",
            "default": "",
            "required": "false",
            "type_": "string",
            "description": "",
            "_id": uuid(),
            "children": [],
            "parent_id": null
        }
    };
    var json_sub_param_demo = function(parent_id) {
        var param = param_demo();
        param.name = "json_param";
        param.parent_id = parent_id;
        return param;
    };
    var empty = {
        "_id": "-1",
        "name": "接口名",
        "url": "接口url",
        "method": "GET",
        "description": "接口描述",
        "paramsList": [
            param_demo()
        ],
        "responseList":[
            param_demo()
        ],
        "responseDemo": "{\n    \"msg\": \"\", \n    \"result\": {},  \n    \"code\": 1\n}",
        "paramsDemo": "\\",
        "category_href": href
    };

    $scope.TYPES = [
        "string", "int", "boolean", "list", "json"
    ];
    $scope.METHODS = [
        "GET", "POST", "PUT", "DELETE"
    ];


    $scope.add = function(){
        $scope.current = angular.copy(empty);
        $scope.isNew = true;
    };
    $scope.edit = function(api_item) {
        $scope.current = api_item;
        $scope.isNew = false;
    };

    var check_unique_un = function(new_item){
        /* $scope.isUnique没法传递返回，难不成绑定过程，与$http的方法不同步。 也没法在$http.success里面return，那是闭包
         *  api.html 里面把div id="{{item.name}} 改成了 div id="{{item._id}}
         */
        $scope.isUnique = true;
        $http.get($scope.base_url + "m/api/exist?name=" + new_item.name + "&href=" + new_item.category_href
        ).success(function (data) {
                //console.log(data.code == 1);  //true
                //console.log(data.code == '1'); //true
                if(data.code == 1) {
                    $scope.isUnique = false;
                } else if (data.code == -1) {
                    $scope.isUnique = true;
                }
            }).error(function (data, status, headers, config) {
                console.log(arguments);
            });
        return $scope.isUnique;
    };
    var check_unique = function(new_item){
        return true;
    };

    $scope.save_api = function(current_item){
        console.log(current_item);
        if($scope.apiForm.$invalid) {
            return;
        }
        $scope.isUnique = true;
        var r = check_unique(current_item);
        //console.log(r);
        if(!r) {
            alert("接口名重复了，重新起一个吧");
            return;
        } else {
            //console.log("接口名可用：" + current_item.name);
        }

        if($scope.isNew) {
            $scope.save_me_yh(current_item);
        }
        else {
            $scope.update_me_yh(current_item);
        }
    };

    $scope.save_me_yh = function(new_item){ //yh
        $scope.save_api_item = new_item;
        $scope.save_api_item.temp_api_ids = [];

        var post_paramsList = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "m/api/param",
                angular.toJson(new_item.paramsList, true)
            ).success(function (data) {
                    $scope.save_api_item.paramsIdList = data.rows.param_ids;
                    $scope.save_api_item.temp_api_ids.push(data.rows.temp_api_id);
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        var post_responseList = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "m/api/param",
                angular.toJson(new_item.responseList, true)
            ).success(function (data) {
                    $scope.save_api_item.responseIdList = data.rows.param_ids;
                    $scope.save_api_item.temp_api_ids.push(data.rows.temp_api_id);
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        $q.all([post_paramsList(), post_responseList()])
            .then(function(result){
                //console.log($scope.save_api_item);
                //console.log(result);
                $http.post($scope.base_url + "m/api",
                    angular.toJson($scope.save_api_item, true)
                ).success(function (data) {
                        //console.log(data.rows);
                        $scope.apiList.push(api_extend_fn(data.rows));
                        $scope.isNew = false;
                        $scope.current = null;
                        var scroll_id = data.rows._id;
                        $timeout(function(){
                            //console.log(scroll_id);
                            $scope.scrollTo(scroll_id);
                        });
                    }).error(function (data, status, headers, config) {
                        console.log(arguments);
                    });
            });
        //console.log($scope.save_api_item);
    };

    $scope.update_me_yh = function(update_item){ //yh
        $scope.save_api_item = update_item;

        var put_paramsList = function(api_id) {
            var deferred = $q.defer();
            $http.put($scope.base_url + "m/api/param",
                angular.toJson({"api_id": api_id, "rows": update_item.paramsList}, true)
            ).success(function (data) {
                    $scope.save_api_item.paramsIdList = data.rows;
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        var put_responseList = function(api_id) {
            var deferred = $q.defer();
            $http.put($scope.base_url + "m/api/param",
                angular.toJson({"api_id": api_id, "rows": update_item.responseList}, true)
            ).success(function (data) {
                    $scope.save_api_item.responseIdList = data.rows;
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        $q.all([put_paramsList(update_item._id), put_responseList(update_item._id)])
            .then(function(result){
                //console.log($scope.save_api_item);
                //console.log(result);
                $http.put($scope.base_url + "m/api",
                    angular.toJson($scope.save_api_item, true)
                ).success(function (data) {
                        //console.log(data.rows);
                        //angular.extend($scope.edit_api_item, api_extend_fn(data.rows));
                        //这一句浅拷贝，对页面当前自动更新尤为关键
                        $scope.isNew = false;
                        $scope.current = null;
                        var scroll_id = $scope.save_api_item._id;
                        $timeout(function(){
                            $scope.scrollTo(scroll_id);
                        });
                    }).error(function (data, status, headers, config) {
                        console.log(arguments);
                    });
            });
        //console.log($scope.save_api_item);
    };

    $scope.cancel = function(){
        $scope.isNew = false;
        $scope.current = null;
    };

    $scope.editorOptions = {
        lineNumbers: true,
        matchBrackets: true,
        mode: "application/x-httpd-php",
        indentUnit: 4,
        indentWithTabs: true,
        enterMode: "keep",
        tabMode: "shift",
        onLoad: function(){
            console.log(123);
        }
    };

    $scope.scrollTo = function(id){
        var old = $location.hash();
        $location.hash(id);
        $anchorScroll();
        //reset to old to keep any additional routing logic from kicking in
        $location.hash(old);
    };

    $scope.add_param = function(collection){
        var param = param_demo();
        collection.push(param);
    };

    $scope.add_json_param_children = function(collection, item){
        //增加只能末位添加的检查
        var pos = collection.length - 1;
        do {
            var t = collection[pos];
            if(!t.parent_id) {  // !t.parent_id && t.type_ =='json'
                break;
            }
            pos -= 1;
        } while (pos >= 0);
        //console.log(collection.length);
        //console.log(pos);
        //console.log(collection.indexOf(item));
        if(collection.indexOf(item) != pos) {
            alert('只能在末位json param新增子项');
            return;
        }
        var sub_param = json_sub_param_demo(item._id);
        item.children.push(sub_param);
        collection.push(sub_param);
        // 上面push的是同一个对象，所以同时更新；
        // 但是如果是用下面这种方式，肯定就不同时更新了
        // var copy = angular.copy(sub_param);
        // collection.push(copy);
    };

    var remove_i = function(collection, item){
        for(var i = 0; i < collection.length; i++) {
            if(collection[i] == item) {
                collection.splice(i, 1);  // 在i处删除1个元素
                break;
            }
        }
    };

    $scope.remove_param = function(collection, item){
        if(confirm("确认删除param?")) {
            if (item.type_ == 'json' && item.children.length) {
                if(confirm("该param有子元素，请再次确认删除param?")) {
                    // 1.
                    remove_i(collection, item);
                    // 2.
                    for(var i = 0; i < collection.length; i++) {
                        if(collection[i].parent_id == item._id) {
                            remove_i(collection, collection[i]);
                            i--;
                            //这种用collection.length作为循环条件，但是在内部因为splice的操作，导致循环条件动态变化，并不符合真正的编程科学...
                        }
                    }
                }
            } else {
                remove_i(collection, item);
            }


        }
    };
    $scope.remove_json_param_children = function(collection, item){
        if(confirm("确认删除param??")) {
            // 1.
            remove_i(collection, item);
            // 2.
            for(var i = 0; i < collection.length; i++) {
                if(collection[i]._id == item.parent_id) {
                    remove_i(collection[i].children, item);
                    break;
                }
            }
        }
    };

    $scope.remove_api = function(item){
        //  <button ng-show="show_edit" class="btn btn-danger btn-xs pull-right" style="margin-right: 5px;" ng-click="remove(apiList, item); save_me();">delete</button>
        if(confirm("确认删除api?")) {
            $http.delete($scope.base_url + "m/api?id=" + item._id
            ).success(function (data) {
                    $window.location.reload();
                }).error(function (data, status, headers, config) {
                    alert("delete failed");
                    console.log(arguments);
                });
        }
    };


    $scope.back = function(){
        $scope.scrollTo("top");
    };

    $scope.log = function(current_item, current_param){
        console.log(current_item);
        if(current_param) {
            console.log(current_param);
        }
    };
}

