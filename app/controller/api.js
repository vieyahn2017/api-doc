/**
 ** yanghao 2017-7-14.
 */

function apiController($scope, $http, $q, $routeParams, $location, $window, $anchorScroll, $timeout) {

    var href = $routeParams.href;
    $scope.href = href;
    $scope.base_url = get_base_url();
    // $http.get($scope.base_url + "m/api?desc=true&href=" + href).success(function(data){  //添加的时候倒序方便点
    $http.get($scope.base_url + "m/api?href=" + href).success(function(data){
        $scope.apiList = data.rows;
        console.log($scope.apiList);
        $timeout(function(){
            var id = $routeParams.name;
            $scope.scrollTo(id);
        });
    }).error(function(){
        $scope.apiList = [];
    });

    var param_demo = {
        "name": "param",
        "default": "",
        "required": "false",
        "type_": "string",
        "description": ""
    };

    var empty = {
        "_id": "-1",
        "name": "接口名",
        "url": "接口url",
        "method": "GET",
        "description": "接口描述",
        "paramsList": [
            {
                "name": "id",
                "default": "",
                "required": "false",
                "type_": "int",
                "description": ""
            }
        ],
        "responseList":[
            {
                "name": "id",
                "default": "1",
                "required": "false",
                "type_": "int",
                "description": "id."
            },
            {
                "name": "name",
                "default": "",
                "required": "true",
                "type_": "string",
                "description": "the name"
            }
        ],
        "responseDemo": "{\n    \"msg\": \"\", \n    \"result\": {},  \n    \"code\": 1\n}",
        "paramsDemo": "\\",
        "category_href": href
    };

    $scope.TYPES = [
        "string", "int", "boolean", "json", "list"
    ];
    $scope.METHODS = [
        "GET", "POST", "PUT", "DELETE"
    ];

    $scope.add = function(){
        $scope.current = angular.copy(empty);
        $scope.isNew = true;
    };
    $scope.edit = function(api_item) {
        $scope.current = angular.copy(api_item);
        $scope.edit_api_item = api_item;
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
        $scope.save_api_item = angular.copy(new_item);

        var post_paramsList = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "m/api/param",
                angular.toJson(new_item.paramsList, true)
            ).success(function (data) {
                    $scope.save_api_item.paramsIdList = data.rows;
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
                    $scope.save_api_item.responseIdList = data.rows;
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
                        $scope.apiList.push(data.rows);
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
        $scope.save_api_item = angular.copy(update_item);

        var put_paramsList = function() {
            var deferred = $q.defer();
            $http.put($scope.base_url + "m/api/param",
                angular.toJson(update_item.paramsList, true)
            ).success(function (data) {
                    $scope.save_api_item.paramsIdList = data.rows;
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        var put_responseList = function() {
            var deferred = $q.defer();
            $http.put($scope.base_url + "m/api/param",
                angular.toJson(update_item.responseList, true)
            ).success(function (data) {
                    $scope.save_api_item.responseIdList = data.rows;
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        $q.all([put_paramsList(), put_responseList()])
            .then(function(result){
                //console.log($scope.save_api_item);
                //console.log(result);
                $http.put($scope.base_url + "m/api",
                    angular.toJson($scope.save_api_item, true)
                ).success(function (data) {
                        //console.log(data.rows);
                        angular.extend($scope.edit_api_item, data.rows);
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

    $scope.remove_param = function(collection, item){
        //  <button ng-show="show_edit" class="btn btn-danger btn-xs pull-right" style="margin-right: 5px;" ng-click="remove(apiList, item); save_me();">delete</button>
        if(confirm("确认删除param?")) {
            for(var i = 0; i < collection.length; i++) {
                if(collection[i] == item) {
                    collection.splice(i, 1);
                }
            }
        }
    };

    //在页面上关闭删除权限，可以在postman发delete删除
    //http://127.0.0.1:3000/api/v1/m/api?id=5971c9aef0881b2d19f49bc4

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
    $scope.add_param = function(current){
        var copy = angular.copy(param_demo);
        current.paramsList.push(copy);
    };
    $scope.add_response = function(current){
        var copy = angular.copy(param_demo);
        current.responseList.push(copy);
    };

    $scope.back = function(){
        $scope.scrollTo("top");
    };

}

