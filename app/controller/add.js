/**
 * yanghao 2017-7-14.
 */
function addController($scope, $http, $location, $routeParams) {

    var base_url = "http://10.0.0.161:30003/api/v1/";
    var json = "data/type.json";

    var href = $routeParams.href;
    $scope.href = href;
    $http.get(base_url + "cc/api/category?href=" + href).success(function (data) {
        item_get = data.rows[0];

        if (href && item_get) {
            $scope.current = item_get;
        }
        else {
            $scope.current = {
                "name": "",
                "href": "",
                "description": ""
            };
        }
        console.log($scope.current);

    }).error(function(){
            $scope.current = undefined;
        });

    var check_unique = function(){
        var r = true;
        // todo : 向服务器发请求 check

        //是新增的需要检查主键冲突哈哈哈我太蛋疼了
        // if(!href) {
        //     angular.forEach($scope.typeList, function (item) {
        //         if ($scope.current.href == item.href) {
        //             r = false;
        //         }

        //     });
        // }
        return r;
    };
    $scope.save_me = function () {
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
        $http.post(base_url + "cc/api/category", angular.toJson($scope.current, true)
        //$http.post(base_url + "cc/api/save", {"boby": angular.toJson($scope.current, true), "href":"type"}
                 // "content=" + encodeURIComponent(angular.toJson($scope.typeList, true)) + "&href=type"
            ).success(function (data) {
                $location.path("/");
            }).error(function (data, status, headers, config) {
                alert("add failed");
                console.log(arguments);
            });
    };
    $scope.edit_me = function () {
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
        $http.put(base_url + "cc/api/category", angular.toJson($scope.current, true)
            ).success(function (data) {
                $location.path("/");
            }).error(function (data, status, headers, config) {
                alert("edit failed");
                console.log(arguments);
            });
    };
    $scope.save = function () {
        console.log($scope.typeForm);
        if($scope.typeForm.$invalid) {
            return;
        }
        if (!href) {
            if(check_unique() == false) {
                alert("英文名和别的分类冲突了，换一个吧");
                return false;
            }
             $scope.save_me();
        } else {
             $scope.save_me();
             //$scope.edit_me();  //本来打算分开，现在发现没必要
        }
       
    };
}