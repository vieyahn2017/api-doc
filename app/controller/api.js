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
        $scope.isNew = true;
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
    $scope.save_api = function(new_item){
        if($scope.apiForm.$invalid) {
            return;
        }
        $scope.isUnique = true;
        var r = check_unique(new_item);
        //console.log(r);
        if(!r) {
            alert("接口名重复了，重新起一个吧");
            return;
        } else {
            //console.log("接口名可用：" + new_item.name);
        }

        if($scope.isNew) {
            //$scope.apiList.push($scope.new_item);
            /*
             * 以前github.com/yilujun100/snsshop-project是在这里添加到apiList
             * 我这边没法直接套用，apiList和new_item格式已经不匹配了
             * 目前是加入到$http.post().success(){}里面
             * */

        }
        else {
            angular.extend($scope.edit_api, $scope.new_item);
        }
        $scope.edit_api = null;
        //console.log($scope.edit_api);
        //angular.extend($scope.edit_api, $scope.new_item);
        //console.log($scope.edit_api);
        $scope.save_me_yh(new_item);
    };

    $scope.save_me_yh = function(new_item){ //yanghao
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
        }
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
        }

        $q.all([post_paramsList(), post_responseList()])
            .then(function(result){
                //console.log($scope.save_api_item);
                //console.log(result);
                $http.post($scope.base_url + "m/api",
                    angular.toJson($scope.save_api_item, true)
                ).success(function (data) {
                        //console.log(data.rows);
                        $scope.apiList.push(data.rows);
                        var scroll_id;
                        if($scope.edit_api) {
                            scroll_id = $scope.edit_api._id;
                        } else {
                            scroll_id = data.rows._id;
                        }

                        $scope.isNew = false;
                        $scope.current = null;
                        $scope.edit_api = null;

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

    $scope.edit = function(api_item) {
        var copy = angular.copy(api_item);
        $scope.current = copy;
        $scope.edit_api = api_item;
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

