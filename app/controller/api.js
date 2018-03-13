/**
 ** yanghao 2017-7-14.
 */

function apiController($scope, $http, $q, $routeParams, $location, $anchorScroll, $timeout) {

    var href = $routeParams.href;

    $scope.href = href;

    $scope.base_url = "http://10.169.110.220:3000/api/v1/";
    // $http.get($scope.base_url + "cc/api?desc=true&href=" + href).success(function(data){  //添加的时候倒序方便点
    $http.get($scope.base_url + "cc/api?href=" + href).success(function(data){
        $scope.apiList = data.rows;
        console.log($scope.apiList);
        $timeout(function(){
            var id = $routeParams.name;
            $scope.scrollTo(id);
        });
    }).error(function(){
            $scope.apiList = [];
        });


    var empty = {
        "name":"接口名",
        "url": "接口url",
        "method": "GET",
        "description": "接口描述",
        "paramsList": [
            {
                "name": "id",
                "default": "",
                "required": true,
                "type_": "int",
                "description": ""
            }
            // {
            //     "name": "dev_id",
            //     "default": "",
            //     "required": true,
            //     "type_": "string",
            //     "description": ""
            // },
            // {
            //     "name": "xd_id",
            //     "default": "",
            //     "required": true,
            //     "type_": "string",
            //     "description": ""
            // }
        ],
        "responseList":[
            // {
            //     "name": "msg",
            //     "default": "",
            //     "required": true,
            //     "type_": "string",
            //     "description": "message."
            // },
            // {
            //     "name": "code",
            //     "default": "1",
            //     "required": true,
            //     "type_": "int",
            //     "description": "code = 1 success/ -1 failed"
            // },
            // {
            //     "name": "rows",
            //     "default": "",
            //     "required": true,
            //     "type_": "list",
            //     "description": "the fetch data. {}"
            // }
            {
                "name": "id",
                "default": "1",
                "required": true,
                "type_": "int",
                "description": "id."
            },
            {
                "name": "name",
                "default": "",
                "required": true,
                "type_": "string",
                "description": "the name"
            }
        ],
        "responseDemo": '{"msg": "",  "result": {},  "code": 1} ',
        "paramsDemo": "\\",
        "category_href": href,

    };

    $scope.TYPES = [
       "string", "int", "boolean", "json", "list"
    ];
    $scope.METHODS = [
        "GET", "POST", "PUT", "DELETE"
    ];
    $scope.add = function(){
        $scope.current = angular.copy(empty);
        console.log($scope.current);
        $scope.isNew = true;
    };
    $scope.save_me = function(){
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

        angular.forEach($scope.apiList, function(item) {
            console.log(item.name);
            console.log(item.paramsParamList);
            console.log(item.responseParamList);
            console.log("====@@@========");
        })

        $http.post("php/save.php",
                "content=" + encodeURIComponent(angular.toJson($scope.apiList, true)) + "&href=" + href
            ).success(function (data) {
                var name;
                if($scope.edit_api) {
                    name = $scope.edit_api.name;
                }

                $scope.isNew = false;
                $scope.current = null;
                $scope.edit_api = null;

                $timeout(function(){
                    if(name) {
                        $scope.scrollTo(name);
                    }
                });
            }).error(function (data, status, headers, config) {
                alert("add failed");
                console.log(arguments);
            });

    };

    var check_unique = function(){
        var r = true;
        // if($scope.edit_api && $scope.edit_api.name == $scope.current.name) {
        //     return r;
        // }
        // angular.forEach($scope.apiList, function(item){
        // if($scope.current.name == item.name) {
        //         r = false;
        //     }
        // });
        return r;
    };

    $scope.save = function(){
        if($scope.apiForm.$invalid) {
            return;
        }
        if(!check_unique()) {
            alert("接口名重复了，重新起一个吧");
            return;
        }
        if($scope.isNew) {
            $scope.apiList.unshift($scope.current);
        }
        else {
            angular.extend($scope.edit_api, $scope.current);
        }
        $scope.save_me();
    };


    $scope.save_new = function(new_item){//yanghao
        if($scope.apiForm.$invalid) {
            return;
        }
        $scope.ret_item = angular.copy(new_item);

        var post_a = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "cc/api/param",
                angular.toJson(new_item.paramsList, true)
            ).success(function (data) {
                $scope.ret_item.paramsIdList = data.rows;
                deferred.resolve($scope.ret_item);
                console.log($scope.ret_item);
            }).error(function (data, status, headers, config) {
                console.log(arguments);
            });
            return deferred.promise;
        }
        var post_b = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "cc/api/param",
                angular.toJson(new_item.responseList, true)
            ).success(function (data) {
                $scope.ret_item.responseIdList = data.rows;
                deferred.resolve($scope.ret_item);
                console.log($scope.ret_item);
            }).error(function (data, status, headers, config) {
                console.log(arguments);
            });
            return deferred.promise;
        }

        // 要求上面2个执行之后，执行这个post
        $q.all([post_a(), post_b()])
            .then(function(result){
                console.log($scope.ret_item);
                console.log(result);
                $http.post($scope.base_url + "cc/api",
                    angular.toJson($scope.ret_item, true)
                    //angular.toJson(result[1], true)
                ).success(function (data) {
                    //console.log(data);

                    var name;
                    if($scope.edit_api) {
                        name = $scope.edit_api.name;
                    }

                    $scope.isNew = false;
                    $scope.current = null;
                    $scope.edit_api = null;

                    $timeout(function(){
                        if(name) {
                            $scope.scrollTo(name);
                        }
                    });

                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            });

        console.log($scope.ret_item);

    };

    $scope.edit = function(api) {
        var copy = angular.copy(api);
        $scope.current = copy;
        $scope.edit_api = api;
    };
    $scope.cancel = function(){
        $scope.isNew = false;
        $scope.current = null;
        $scope.edit_api = null;
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

    $scope.remove = function(collection, item){
        //  <button ng-show="show_edit" class="btn btn-danger btn-xs pull-right" style="margin-right: 5px;" ng-click="remove(apiList, item); save_me();">delete</button>
        if(confirm("确认删除?")) {
            for(var i = 0; i < collection.length; i++) {
                if(collection[i] == item) {
                    collection.splice(i, 1);
                }
            }
        }
    };

    //在页面上关闭删除权限，可以在postman发delete删除
    //http://10.0.0.161:30003/api/v1/cc/api?id=5971c9aef0881b2d19f49bc4

    $scope.remove_2 = function(item){
        //  <button ng-show="show_edit" class="btn btn-danger btn-xs pull-right" style="margin-right: 5px;" ng-click="remove(apiList, item); save_me();">delete</button>
        if(confirm("确认删除?")) {

        $http.delete($scope.base_url + "cc/api?id=" + item._id
            ).success(function (data) {
                $window.location.reload();
            }).error(function (data, status, headers, config) {
                alert("delete failed");
                console.log(arguments);
            });

        }
    };
    $scope.add_param = function(current){
        var copy = angular.copy(empty.paramsList[0]);
        current.paramsList.push(copy);
    };
    $scope.add_response = function(current){
        var copy = angular.copy(empty.responseList[0]);
        current.responseList.push(copy);
    };

    $scope.back = function(){
        $scope.scrollTo("top");
    };

}

